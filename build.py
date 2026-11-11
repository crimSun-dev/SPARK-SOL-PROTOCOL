"""SPARK SOL indexer: the whole Workspace, the CrimSun pools, the skills, GitHub.

Full text goes into a LOCAL SQLite full-text index (index/workspace.sqlite, on
this machine, never uploaded). SPARK's /chat searches it. Flaxeon's shared
memory (Neon) gets ONE short `repo_index` summary per project, written through
the parent's own save_document, so Flame, Tempest and the galaxy all know each
project exists without the store becoming a file server.

Never indexed: key and secret files (by name), and key-shaped strings inside
any file (scrubbed before they are stored). Pruned: dependency, VCS and build
folders, and the pool's duplicate `chunks` copies. Binaries and media: name and
path only. Re-runs are incremental by size and modification time.

    python build.py                 # index everything, then publish summaries
    python build.py --no-publish    # local index only, Neon untouched
    python build.py --dry-run       # list projects and counts, write nothing
    python build.py --no-github     # skip the gh calls
    python build.py --only workspace|pools|skills|github

What the operator fed Flaxeon (feeds.json, see feeds.py) is indexed too: each feed
is its own star in the category it was given, and a category entry moves an
existing project to another region of the sky.

Outbound hosts: api.github.com (through the gh CLI) and Flaxeon's Neon (and
Firebase if configured) for the summaries. Nothing else.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import feeds  # noqa: E402  (feeds.json: what the operator fed Flaxeon)
PARENT = HERE.parent                                   # F.L.A.X.E.O.N
WORKSPACE = PARENT.parent                              # G:\...\Workspace
HOME = Path.home()
INDEX_DIR = HERE / "index"
DB_PATH = INDEX_DIR / "workspace.sqlite"

CURSOR_POOL = HOME / ".cursor" / "skills" / "POOL"
CLAUDE_POOL = HOME / ".claude" / "skills" / "POOL"   # mostly a copy: identical files are skipped
ROOTS = [
    ("workspace", WORKSPACE),
    ("pools", CURSOR_POOL),
    ("pools", CLAUDE_POOL),
    ("skills", HOME / ".cursor" / "skills"),           # POOL pruned here; it is its own root
    ("skills", HOME / ".claude" / "skills"),
    ("skills", HOME / ".claude" / "plugins"),
    ("skills", HOME / ".gemini" / "skills"),
    ("skills", HOME / ".codex" / "skills"),
    ("skills", HOME / ".agents" / "skills"),
]
SKILL_TEXT_MAX = 47 * 1024     # under Flaxeon's 48 KB DOCUMENT_TEXT_MAX, so the text is never dropped
FED_TEXT_MAX = 46 * 1024       # a fed file's own text on its star; the header fits in the rest

# ── what is never read ────────────────────────────────────────────────────
PRUNE_DIRS = {"node_modules", "venv", ".venv", "env", ".git", "dist", "build", "__pycache__",
              ".next", ".nuxt", ".cache", "target", ".gradle", ".idea", ".vs", "Library", "Temp",
              "obj", "Logs", ".pytest_cache", ".mypy_cache", "site-packages", ".svelte-kit",
              ".turbo", "coverage", ".expo", "Pods", ".dart_tool", ".parcel-cache", "bower_components",
              "chunks", "_build_snhu", "$RECYCLE.BIN", "System Volume Information"}
PRUNE_PATHS = {str(INDEX_DIR).lower(), str(HERE / "cache").lower()}
# Files whose whole job is to hold a secret. Ordinary code that merely mentions
# one (secrets.py, token.py, env_handler.gd) is indexed and scrubbed instead:
# the first, broader rule skipped 1,074 files, mostly library code.
SECRET_FILE = re.compile(
    r"(^\.env($|\.)|\.env$|^api[_-]?keys?\b"
    r"|credentials?\.(json|ya?ml|toml|ini|txt|csv|xml)$|secrets?\.(json|ya?ml|toml|ini|env|txt)$"
    r"|\.(pem|key|p12|pfx|jks|keystore|secret|kdbx|ppk)$|^keystore|^id_(rsa|ed25519|ecdsa|dsa)"
    r"|service[-_]?account.*\.json$|^\.(npmrc|pypirc|netrc|git-credentials)$"
    r"|passwords?\.(txt|json|csv)$)", re.I)
SKIP_FILE = re.compile(r"(\.min\.(js|css)$|\.map$|\.bundle\.js$|^package-lock\.json$|^yarn\.lock$"
                       r"|^pnpm-lock\.yaml$|^cargo\.lock$|^poetry\.lock$|^composer\.lock$|^gemfile\.lock$"
                       r"|^graph-data\.js$)", re.I)
TEXT_EXT = {".md", ".markdown", ".txt", ".rst", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
            ".json", ".html", ".htm", ".css", ".scss", ".cs", ".gd", ".java", ".kt", ".c", ".cc",
            ".cpp", ".h", ".hpp", ".lua", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sql", ".sh",
            ".ps1", ".bat", ".go", ".rs", ".swift", ".dart", ".vue", ".svelte", ".php", ".rb", ".csv",
            ".tex", ".ipynb", ".shader", ".glsl", ".hlsl", ".xml", ".gradle", ".cmake", ".r", ".m"}
DOC_EXT = {".pdf", ".docx", ".pptx", ".xlsx"}
TEXT_MAX = 512 * 1024          # bigger text files are generated or data: name only
DATA_MAX = 256 * 1024          # .json / .csv / .xml
DOC_TEXT_MAX = 1024 * 1024     # extracted text kept per document
CHUNK = 1500

# ── secrets inside files ──────────────────────────────────────────────────
SCRUB = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[private key removed]"),
    (re.compile(r"\b(sk|rk|pk)-[A-Za-z0-9_\-]{16,}"), "[key removed]"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{16,}"), "[key removed]"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}"), "[key removed]"),
    (re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}"), "[key removed]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"), "[key removed]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[key removed]"),
    (re.compile(r"\b(postgres(ql)?|mysql|mongodb(\+srv)?|redis|amqp)://\S+", re.I), "[connection string removed]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{20,}"), "Bearer [removed]"),
    (re.compile(r"""(?i)(["']?(?:api[_-]?key|secret|token|password|passwd|private[_-]?key|client[_-]?secret)["']?\s*[:=]\s*)(["'])[^"'\n]{6,}\2"""),
     r"\1\2[removed]\2"),
]
_PARENT_SCRUB = None


def scrub(text: str) -> str:
    global _PARENT_SCRUB
    for pat, sub in SCRUB:
        text = pat.sub(sub, text)
    if _PARENT_SCRUB is None:
        try:
            sys.path.insert(1, str(PARENT))
            from memory.memory_manager import scrub_secret_shapes, scrub_secrets
            _PARENT_SCRUB = (scrub_secrets, scrub_secret_shapes)
        except Exception:
            _PARENT_SCRUB = ()
    for fn in _PARENT_SCRUB:
        try:
            text = fn(text)
        except Exception:
            pass
    return text


# ── extraction ────────────────────────────────────────────────────────────
def read_text(p: Path) -> str:
    raw = p.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    if b"\x00" in raw[:4096]:
        return ""                                   # binary with a text extension
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def read_doc(p: Path) -> str:
    ext = p.suffix.lower()
    if ext == ".pdf":
        import fitz                                 # PyMuPDF, already installed
        out, n = [], 0
        with fitz.open(p) as d:
            for page in d:
                t = page.get_text()
                out.append(t)
                n += len(t)
                if n > DOC_TEXT_MAX:
                    break
        return "\n".join(out)
    if ext == ".docx":
        import docx
        d = docx.Document(str(p))
        parts = [para.text for para in d.paragraphs]
        for table in d.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts)
    if ext == ".pptx":                              # no python-pptx here: the XML is enough
        out = []
        with zipfile.ZipFile(p) as z:
            slides = sorted((n for n in z.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                            key=lambda n: int(re.findall(r"\d+", n)[-1]))
            for n in slides:
                xml = z.read(n).decode("utf-8", errors="ignore")
                out.append(" ".join(re.findall(r"<a:t>([^<]*)</a:t>", xml)))
        return "\n\n".join(out)
    if ext == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        out, n = [], 0
        try:
            for ws in wb.worksheets:
                out.append(f"## {ws.title}")
                for row in ws.iter_rows(values_only=True):
                    line = " | ".join("" if v is None else str(v) for v in row).strip(" |")
                    if line:
                        out.append(line)
                        n += len(line)
                    if n > DOC_TEXT_MAX:
                        break
        finally:
            wb.close()
        return "\n".join(out)
    return ""


def chunks(text: str, size: int = CHUNK) -> list[str]:
    text = re.sub(r"[ \t]+\n", "\n", text)
    blocks = re.split(r"\n\s*\n", text)
    out, cur = [], ""
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        while len(b) > size:                        # one huge block: cut at a line
            cut = b.rfind("\n", 0, size)
            cut = cut if cut > size // 3 else size
            piece, b = b[:cut], b[cut:].lstrip()
            if cur:
                out.append(cur)
                cur = ""
            out.append(piece)
        if cur and len(cur) + len(b) + 2 > size:
            out.append(cur)
            cur = b
        else:
            cur = (cur + "\n\n" + b) if cur else b
    if cur:
        out.append(cur)
    return out


# ── projects ──────────────────────────────────────────────────────────────
def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60] or "x"


COURSE_DIR = re.compile(r"(course|class modules|modules)", re.I)


class Projects:
    """Which project a file belongs to. One project = one Neon summary = one star."""

    def __init__(self, fed: list[dict] | None = None):
        self.git_roots: dict[str, set[Path]] = {}
        self.by_key: dict[str, dict] = {}
        # fed paths claim their files first, wherever they live; the deepest claim wins
        self.claims = sorted(((Path(f["path"]), f) for f in fed or []), key=lambda c: -len(c[0].parts))

    def claim_for(self, path: Path) -> dict | None:
        for at, f in self.claims:
            if path == at or at in path.parents:
                key = "feed_" + slug(f["title"]) + "_" + hashlib.sha1(at.as_posix().lower().encode()).hexdigest()[:6]
                return self._get("feed", f["title"], at, f["category"],
                                 "fed file" if at.is_file() else "fed folder", key=key)
        return None

    def project_for(self, kind: str, root: Path, path: Path) -> dict:
        fed = self.claim_for(path)
        if fed is not None:
            return fed
        rel = path.relative_to(root)
        parts = rel.parts
        if kind == "workspace":
            for anc in [path.parent, *path.parent.parents]:
                if anc in self.git_roots.get(str(root), set()):
                    return self._get("ws", anc.relative_to(root).as_posix(), anc, "workspace", "git repo")
                if anc == root:
                    break
            if len(parts) == 1:
                return self._get("ws", "Workspace root files", root, "workspace", "folder")
            top = parts[0]
            if COURSE_DIR.search(top) and len(parts) > 2:
                return self._get("ws", f"{top}/{parts[1]}", root / top / parts[1], "workspace", "course folder")
            return self._get("ws", top, root / top, "workspace", "folder")
        if kind == "pools":
            top = parts[0]
            if len(parts) == 1:
                return self._get("pool", Path(top).stem, path, "pools", "pool module")
            if top.upper().startswith("EXPERIENCE"):
                name = Path(parts[-1]).stem if len(parts) == 2 else parts[1]
                return self._get("exp", name, root / top / parts[1], "experience", "experience module")
            inner = [p for p in parts[1:-1] if p.lower() != "chunk_modules"]
            course = inner[0] if inner else None
            if course:
                return self._get("pool", f"{top}/{course}", root / top / course, "pools", "pool course")
            return self._get("pool", top, root / top, "pools", "pool")
        # skills: one star per skills root
        label = f"{root.parent.name} {root.name}"     # ".claude skills" / ".claude plugins" / ".gemini skills"
        return self._get("skills", label, root, "skills", "skills root")

    def _get(self, prefix: str, title: str, path: Path, region: str, kind: str, key: str = "") -> dict:
        key = key or f"{prefix}_{slug(title)}"
        p = self.by_key.get(key)
        if p is None:
            p = self.by_key[key] = {"key": key, "title": title, "path": str(path), "region": region,
                                    "kind": kind, "files": Counter(), "bytes": 0, "langs": Counter(),
                                    "latest": 0.0, "top": Counter(), "readme": "", "git": {}, "github": None}
        return p


def git_info(repo: Path) -> dict:
    def g(*args):
        try:
            r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                               timeout=15, encoding="utf-8", errors="replace")
            return r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            return ""
    remote = g("remote", "get-url", "origin")
    remote = re.sub(r"//[^@/]+@", "//", remote)           # never keep credentials in a URL
    last = g("log", "-1", "--format=%cs|%s")
    d, _, msg = last.partition("|")
    return {"remote": remote, "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
            "last_commit": d, "last_message": msg[:160], "commits": g("rev-list", "--count", "HEAD")}


def norm_remote(url: str) -> str:
    url = (url or "").lower().strip().removesuffix(".git").rstrip("/")
    m = re.search(r"github\.com[:/]+([^/]+/[^/]+)$", url)
    return m.group(1) if m else ""


# ── GitHub ────────────────────────────────────────────────────────────────
def gh_json(*args, timeout=120):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=timeout,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:200])
    return json.loads(r.stdout) if r.stdout.strip() else None


def github_repos(say, extra_owners=()) -> list[dict]:
    me = gh_json("api", "user", "--jq", "{login: .login}")["login"]
    try:                                           # a fine-grained token may not list organisations
        orgs = [o["login"] for o in (gh_json("api", "user/orgs") or [])]
    except RuntimeError:
        orgs = []
    owners = list(dict.fromkeys([me, *orgs, *extra_owners]))
    repos = []
    fields = ("nameWithOwner,description,primaryLanguage,pushedAt,url,isPrivate,isFork,isArchived,"
              "stargazerCount,defaultBranchRef,repositoryTopics,issues,pullRequests")
    for owner in owners:
        try:
            listed = gh_json("repo", "list", owner, "--limit", "1000", "--json", fields)
        except RuntimeError:
            listed = gh_json("repo", "list", owner, "--limit", "1000", "--json",
                             "nameWithOwner,description,primaryLanguage,pushedAt,url,isPrivate,isFork,isArchived")
        say(f"  github {owner}: {len(listed)} repos")
        repos += listed
    for r in repos:
        try:
            p = subprocess.run(["gh", "api", f"repos/{r['nameWithOwner']}/readme", "-H",
                                "Accept: application/vnd.github.raw"], capture_output=True,
                               timeout=60, encoding="utf-8", errors="replace")
            r["readme"] = p.stdout if p.returncode == 0 else ""
            # 404 is "no README"; anything else (403: the token cannot read contents) is "unknown"
            r["readme_unknown"] = p.returncode != 0 and "HTTP 404" not in (p.stderr or "")
        except Exception:
            r["readme"], r["readme_unknown"] = "", True
    return repos


# ── the index ─────────────────────────────────────────────────────────────
SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, project TEXT, root TEXT, kind TEXT,
  size INTEGER, mtime REAL, indexed INTEGER, note TEXT);
CREATE TABLE IF NOT EXISTS projects (key TEXT PRIMARY KEY, title TEXT, region TEXT, kind TEXT,
  path TEXT, info TEXT, summary TEXT, updated TEXT);
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(title, body, path UNINDEXED,
  project UNINDEXED, tokenize='porter unicode61');
CREATE TABLE IF NOT EXISTS chunk_rows (path TEXT, rid INTEGER);
CREATE INDEX IF NOT EXISTS chunk_rows_path ON chunk_rows(path);
"""


def drop_chunks(db: sqlite3.Connection, path: str, existed: bool) -> None:
    """Remove a file's chunks by rowid. `DELETE ... WHERE path=?` on the FTS
    table scans the whole index, which made the first build slow down with
    every file it wrote, so it only runs for rows written before chunk_rows."""
    rids = [r[0] for r in db.execute("SELECT rid FROM chunk_rows WHERE path=?", (path,))]
    if rids:
        db.executemany("DELETE FROM chunks WHERE rowid=?", [(r,) for r in rids])
        db.execute("DELETE FROM chunk_rows WHERE path=?", (path,))
    elif existed:
        db.execute("DELETE FROM chunks WHERE path=?", (path,))


def add_chunk(db: sqlite3.Connection, title: str, body: str, path: str, project: str) -> None:
    cur = db.execute("INSERT INTO chunks(title, body, path, project) VALUES (?,?,?,?)",
                     (title, body, path, project))
    db.execute("INSERT INTO chunk_rows VALUES (?,?)", (path, cur.lastrowid))


def open_db() -> sqlite3.Connection:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    return db


def walk(kind: str, root: Path, prj: Projects):
    git = prj.git_roots.setdefault(str(root), set())
    if root.is_file():                             # a single fed file is its own root
        yield root
        return
    for dp, dns, fns in os.walk(root):
        d = Path(dp)
        if ".git" in dns and kind == "workspace":
            git.add(d)
        keep = []
        for n in dns:
            full = str(d / n).lower()
            if n in PRUNE_DIRS or (n.startswith(".") and n not in (".github",)) or full in PRUNE_PATHS:
                continue
            if kind == "skills" and d == root and n == "POOL":
                continue                           # the pool is its own root
            keep.append(n)
        dns[:] = keep
        for f in fns:
            yield d / f


def fed_roots(fed: list[dict]) -> list[tuple[str, Path]]:
    """Feeds that no built-in root already walks become roots of their own."""
    out = []
    for f in fed:
        at = Path(f["path"])
        if at.exists() and not any(r == at or r in at.parents for _, r in ROOTS if r.is_dir()):
            out.append(("feed", at))
    return out


def index(args, say) -> tuple[Projects, dict]:
    reg = feeds.load()
    prj = Projects(reg["feeds"])
    db = None if args.dry_run else open_db()
    stats = Counter()
    seen: set[str] = set()
    roots = [(k, r) for k, r in ROOTS + fed_roots(reg["feeds"])
             if (r.is_dir() or (k == "feed" and r.is_file())) and (not args.only or args.only == k)]
    t0 = time.time()
    for kind, root in roots:
        say(f"{kind}: {root}")
        for path in walk(kind, root, prj):
            name = path.name
            try:
                st = path.stat()
            except OSError:
                continue
            if kind == "pools" and root == CLAUDE_POOL:     # the .cursor POOL already holds this file
                try:
                    if (CURSOR_POOL / path.relative_to(root)).stat().st_size == st.st_size:
                        stats["pool_twin_skipped"] += 1
                        continue
                except OSError:
                    pass
            p = prj.project_for(kind, root, path)
            ext = path.suffix.lower()
            rel = path.relative_to(Path(p["path"])) if Path(p["path"]) in path.parents else Path(name)
            if p["kind"] == "fed file":                # its own star: the name is the whole listing
                rel = Path(name)
            p["top"][rel.parts[0] if len(rel.parts) > 1 else "(files)"] += 1
            p["latest"] = max(p["latest"], st.st_mtime)
            if SECRET_FILE.search(name):
                stats["secret_skipped"] += 1
                continue                           # not even the name goes in
            spath = str(path)
            seen.add(spath)
            cls = "text" if ext in TEXT_EXT else "doc" if ext in DOC_EXT else "other"
            p["files"][cls] += 1
            p["bytes"] += st.st_size
            if cls == "text":
                p["langs"][ext] += 1
            if not p["readme"] and re.match(r"(readme|skill)\.(md|markdown|txt)$", name, re.I) \
                    and path.parent == Path(p["path"]):
                try:
                    p["readme"] = scrub(read_text(path))[:4000]
                except OSError:
                    pass
            stats[cls] += 1
            if p["kind"] == "fed file" and cls in ("text", "doc") and not p.get("full"):
                try:                               # a fed file's star carries the file itself
                    if cls == "doc":
                        raw = read_doc(path)
                    else:
                        raw = read_text(path) if st.st_size <= TEXT_MAX else ""
                    p["full"] = scrub(raw)[:FED_TEXT_MAX]
                    p["full_cut"] = len(raw) > FED_TEXT_MAX
                except Exception:
                    pass
            if db is None:
                continue
            row = db.execute("SELECT size, mtime FROM files WHERE path=?", (spath,)).fetchone()
            if row and row[0] == st.st_size and abs(row[1] - st.st_mtime) < 1e-3:
                stats["unchanged"] += 1
                continue
            body, note = "", ""
            if SKIP_FILE.search(name):
                note = "generated file: name only"
            elif cls == "text":
                cap = DATA_MAX if ext in (".json", ".csv", ".xml") else TEXT_MAX
                if st.st_size > cap:
                    note = f"over {cap // 1024} KB: name only"
                else:
                    try:
                        body = read_text(path)
                    except OSError as e:
                        note = f"unreadable: {type(e).__name__}"
            elif cls == "doc":
                try:
                    body = read_doc(path)[:DOC_TEXT_MAX]
                    if not body.strip():
                        note = "no extractable text (scanned?): name only"
                except Exception as e:
                    note = f"extract failed: {type(e).__name__}"
            drop_chunks(db, spath, existed=row is not None)
            title = f"{p['title']} / {path.relative_to(root).as_posix()}"
            if body.strip():
                body = scrub(body)
                for c in chunks(body):
                    add_chunk(db, title, c, spath, p["key"])
                stats["chunked"] += 1
            else:
                add_chunk(db, title, "", spath, p["key"])   # the name is still findable
            db.execute("INSERT OR REPLACE INTO files VALUES (?,?,?,?,?,?,?,?)",
                       (spath, p["key"], str(root), cls, st.st_size, st.st_mtime,
                        1 if body.strip() else 0, note))
            stats["written"] += 1
            if stats["written"] % 2000 == 0:
                db.commit()
                say(f"  … {stats['written']} files written, {time.time() - t0:.0f}s")
        if db is not None:
            db.commit()
    if db is not None:                             # files that are gone leave the index
        gone = [r[0] for r in db.execute("SELECT path, root FROM files")
                if r[0] not in seen and any(r[1] == str(rt) for _, rt in roots)]
        for g in gone:
            drop_chunks(db, g, existed=True)
            db.execute("DELETE FROM files WHERE path=?", (g,))
        stats["removed"] = len(gone)
        db.commit()
        db.close()
    for root_key, roots_set in prj.git_roots.items():
        for repo in roots_set:
            key = f"ws_{slug(repo.relative_to(Path(root_key)).as_posix())}"
            if key in prj.by_key:
                prj.by_key[key]["git"] = git_info(repo)
    moved = 0
    for p in prj.by_key.values():                  # the operator's categories win over the default region
        cat = feeds.override_for(p["path"], reg)
        if cat and cat != p["region"]:
            p["region"], moved = cat, moved + 1
    stats["feeds"] = len(reg["feeds"])
    stats["moved"] = moved
    stats["seconds"] = round(time.time() - t0)
    return prj, stats


def attach_github(prj: Projects, repos: list[dict], db_ok: bool, say) -> None:
    local = {norm_remote(p["git"].get("remote", "")): p for p in prj.by_key.values() if p["git"]}
    db = open_db() if db_ok else None
    for r in repos:
        nwo = r["nameWithOwner"]
        info = {k: r.get(k) for k in ("nameWithOwner", "description", "url", "isPrivate", "isFork",
                                     "isArchived", "pushedAt", "stargazerCount")}
        info["language"] = (r.get("primaryLanguage") or {}).get("name")
        info["issues"] = (r.get("issues") or {}).get("totalCount")
        info["pull_requests"] = (r.get("pullRequests") or {}).get("totalCount")
        p = local.get(nwo.lower())
        if p is None:                              # on GitHub, not cloned here
            p = prj._get("gh", nwo, Path(r.get("url") or nwo), "workspace", "github repo")
            p["path"] = r.get("url") or nwo
            if not p["readme"]:
                p["readme"] = scrub(r.get("readme") or "")[:4000]
        p["github"] = info
        if db is not None and r.get("readme"):
            spath = f"github:{nwo}/README"
            drop_chunks(db, spath, existed=False)
            for c in chunks(scrub(r["readme"])):
                add_chunk(db, f"{p['title']} / README (GitHub)", c, spath, p["key"])
    if db is not None:
        db.commit()
        db.close()


# ── skills and experience modules: one full document each ─────────────────
FRONTMATTER = re.compile(r"\A﻿?---\s*\r?\n(.*?)\r?\n---", re.S)


def _front(text: str, field: str) -> str:
    m = FRONTMATTER.match(text or "")
    f = re.search(rf"^{field}:\s*(.+)$", m.group(1), re.M) if m else None
    return f.group(1).strip().strip("'\"") if f else ""


def _keep_dir(parent: Path, name: str, root: Path) -> bool:
    return not (name in PRUNE_DIRS or name.startswith(".") or (parent == root and name == "POOL"))


def find_skills() -> list[dict]:
    """Every folder with a SKILL.md under the skill roots, outside pruned folders.
    Identical copies (same SKILL.md and same reference names and sizes) are one
    skill that lists every location. Keys: skill_<name>, then a root suffix, then a
    short hash, so a different skill with the same name never overwrites another."""
    by_hash: dict[str, dict] = {}
    out: list[dict] = []
    for kind, root in ROOTS:
        if kind != "skills" or not root.is_dir():
            continue
        for dp, dns, fns in os.walk(root):
            d = Path(dp)
            dns[:] = sorted(n for n in dns if _keep_dir(d, n, root))
            if "SKILL.md" not in fns:
                continue
            try:
                main = read_text(d / "SKILL.md")
            except OSError:
                continue
            refs = []
            for rp, rdns, rfns in os.walk(d):
                r = Path(rp)
                rdns[:] = sorted(n for n in rdns if _keep_dir(r, n, root) and not (r / n / "SKILL.md").exists())
                refs += [r / f for f in sorted(rfns) if f.lower().endswith(".md")
                         and not (r == d and f == "SKILL.md") and not SECRET_FILE.search(f)]
            ident = hashlib.sha1(main.encode("utf-8", "replace"))
            for r in refs:
                try:
                    ident.update(f"{r.relative_to(d).as_posix()}:{r.stat().st_size}".encode())
                except OSError:
                    pass
            h = ident.hexdigest()
            if h in by_hash:
                by_hash[h]["also"].append(str(d))
                continue
            sk = {"name": _front(main, "name") or d.name, "desc": _front(main, "description"),
                  "path": str(d), "root": root, "main": main, "refs": refs, "also": []}
            by_hash[h] = sk
            out.append(sk)
    taken: set[str] = set()
    for sk in out:
        base = f"skill_{slug(sk['name'])}"
        key = base
        if key in taken:
            key = f"{base}_{slug(sk['root'].parent.name + '_' + sk['root'].name)}"
        if key in taken:
            key = f"{base}_{hashlib.sha1(sk['path'].encode()).hexdigest()[:6]}"
        taken.add(key)
        sk["key"] = key
    return out


def _fill(head: str, first: str, parts: list[tuple[str, Path]], cut_note: str) -> str:
    """head + first, then each part while it fits under SKILL_TEXT_MAX; the rest named."""
    body = head + scrub(first)
    omitted = []
    for label, path in parts:
        try:
            block = f"\n\n## {label}\n\n" + scrub(read_text(path))
        except OSError:
            continue
        if len((body + block).encode("utf-8")) + 1024 <= SKILL_TEXT_MAX:
            body += block
        else:
            omitted.append(label)
    if omitted:
        body += "\n\nNot included (over the size limit): " + ", ".join(omitted)
    if len(body.encode("utf-8")) > SKILL_TEXT_MAX:
        body = body.encode("utf-8")[:SKILL_TEXT_MAX - 200].decode("utf-8", "ignore") + "\n\n" + cut_note
    return body


def skill_text(sk: dict) -> str:
    head = "\n".join([f"# {sk['name']}", "", f"Skill at: {sk['path']}",
                      *[f"Also at: {a}" for a in sk["also"]], "", ""])
    d = Path(sk["path"])
    return _fill(head, sk["main"], [(r.relative_to(d).as_posix(), r) for r in sk["refs"]],
                 "[cut at the size limit]")


def skill_summary(sk: dict) -> str:
    desc = " ".join((sk["desc"] or "").split())
    if not desc:
        body = FRONTMATTER.sub("", sk["main"], count=1)
        desc = next((" ".join(b.split()).lstrip("# ") for b in body.split("\n\n")
                     if len(b.strip()) > 12 and not b.strip().startswith(("<", "!", "[", "```"))), "")
    return scrub(f"Skill: {sk['name']}. {desc}")[:400]


def experience_text(p: dict) -> str:
    root = Path(p["path"])
    files = [root] if root.is_file() else sorted(
        (Path(dp) / f for dp, dns, fns in os.walk(root) for f in fns
         if f.lower().endswith((".md", ".txt"))), key=lambda x: x.as_posix().lower())
    if not files:
        return summary_text(p)
    head = f"# {p['title']}\n\nExperience module at: {p['path']}\n\n"
    first, rest = files[0], files[1:]
    try:
        first_text = read_text(first)
    except OSError:
        return summary_text(p)
    return _fill(head, first_text, [(f.relative_to(root).as_posix() if root.is_dir() else f.name, f) for f in rest],
                 "[cut at the size limit]")


# ── summaries: what Flaxeon's shared memory gets ──────────────────────────
def summary_line(p: dict) -> str:
    gh = p.get("github") or {}
    desc = (gh.get("description") or "").strip()
    if not desc and p["readme"]:
        for block in p["readme"].split("\n\n"):
            line = " ".join(block.split()).lstrip("# ").strip()
            if line and not line.startswith(("<", "!", "[", "---")) and len(line) > 12:
                desc = line
                break
    files = sum(p["files"].values())
    what = {"git repo": "Git repo", "github repo": "GitHub repo (not cloned here)",
            "course folder": "Course folder", "pool course": "Pool course",
            "pool module": "Pool module", "pool": "Pool", "experience module": "Experience module",
            "skills root": "Skills", "folder": "Folder",
            "fed folder": "Folder fed to Flaxeon", "fed file": "File fed to Flaxeon"}.get(p["kind"], p["kind"])
    s = f"{what}: {p['title']}" + (f", {files:,} files" if files else "")
    return (s + (". " + desc if desc else "."))[:400]


def summary_text(p: dict) -> str:
    gh, git = p.get("github") or {}, p.get("git") or {}
    lines = [f"# {p['title']}", "", summary_line(p), ""]
    lines.append(f"Where: {p['path']}")
    if git.get("remote"):
        lines.append(f"Git: {git['remote']} on {git.get('branch')}, {git.get('commits')} commits, "
                     f"last {git.get('last_commit')}: {git.get('last_message')}")
    if gh:
        lines.append(f"GitHub: {gh.get('nameWithOwner')} ({'private' if gh.get('isPrivate') else 'public'}"
                     f"{', fork' if gh.get('isFork') else ''}{', archived' if gh.get('isArchived') else ''}), "
                     f"language {gh.get('language')}, pushed {str(gh.get('pushedAt'))[:10]}, "
                     f"{gh.get('issues')} issues, {gh.get('pull_requests')} pull requests")
    if p["files"]:
        lines.append("Files: " + ", ".join(f"{v:,} {k}" for k, v in p["files"].most_common()))
    if p["langs"]:
        lines.append("Mostly: " + ", ".join(f"{k} ({v})" for k, v in p["langs"].most_common(6)))
    if p["latest"]:
        lines.append("Last changed: " + datetime.fromtimestamp(p["latest"]).strftime("%Y-%m-%d"))
    top = [k for k, _ in p["top"].most_common(14) if k != "(files)"]
    if top:
        lines.append("Inside: " + ", ".join(top))
    if p.get("full"):                              # a fed file: its own text, not a listing
        lines += ["", p["full"]]
        if p.get("full_cut"):
            lines += ["", f"(Cut at {FED_TEXT_MAX // 1024} KB; the whole file is in SPARK SOL's local index.)"]
        return scrub("\n".join(lines))
    if p["readme"]:
        lines += ["", p["readme"][:1600]]
    lines.append("")
    lines.append("Full text is in SPARK SOL's local index; ask the galaxy for detail.")
    return scrub("\n".join(lines))


def save_projects(prj: Projects) -> None:
    db = open_db()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.execute("DELETE FROM projects")
    for p in prj.by_key.values():
        info = {k: v for k, v in p.items() if k in ("git", "github", "path", "kind")}
        info["files"] = dict(p["files"])
        db.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?,?)",
                   (p["key"], p["title"], p["region"], p["kind"], p["path"],
                    json.dumps(info), summary_line(p), now))
    db.commit()
    db.close()


class PublishError(RuntimeError):
    pass


def memory_gate():
    """Flaxeon's memory module, once its passkey gate is open in this process.
    A closed gate makes Flaxeon's writes skip Neon and Firebase without queueing
    anything, so publishing behind it would be a silent loss (2026-11-11: 210
    summaries). Never opens Neon around the gate."""
    sys.path.insert(1, str(PARENT))
    from core.passkey import cloud_allowed
    from memory import memory_manager as mm
    if not cloud_allowed():
        raise PublishError(
            "Flaxeon's memory is locked in this process, so nothing would reach Neon. "
            "Set FLAXEON_PASSKEY for this one run, or run with --no-publish.")
    neon, _ = mm._backends()
    if neon is None:
        raise PublishError("no Neon store is configured for Flaxeon, so nothing would reach it")
    return mm, neon


def _indexed_in_neon(neon) -> set[str]:
    """Every document this indexer owns: project summaries, skills, experience modules."""
    return {name for name, d in neon.load_documents().items()
            if isinstance(d, dict) and d.get("indexer") == "spark_sol_build"}


def documents_for(prj: Projects, skills: list[dict]):
    """(key, kind, text, source, summary, region, title) for everything published."""
    for p in sorted(prj.by_key.values(), key=lambda p: p["key"]):
        if p["kind"] == "experience module":     # its text stays an experience text in any category
            yield p["key"], "experience", experience_text(p), p["path"], summary_line(p), p["region"], p["title"]
        else:
            yield p["key"], "repo_index", summary_text(p), p["path"], summary_line(p), p["region"], p["title"]
    for sk in sorted(skills, key=lambda s: s["key"]):
        yield sk["key"], "skill", skill_text(sk), sk["path"], skill_summary(sk), "skills", sk["name"]


def publish(prj: Projects, say, github_read: bool = True, skills: list[dict] | None = None) -> dict:
    """One repo_index document per project into Flaxeon's shared memory, through
    the parent's own save_document. Documents this indexer published before and
    no longer has are forgotten. Nothing else in the store is touched. The result
    is counted in Neon, not taken on trust."""
    mm, neon = memory_gate()
    from tools.memory_ingest import build_payload
    db = open_db()
    row = db.execute("SELECT v FROM meta WHERE k='published'").fetchone()
    current = {n: d for n, d in neon.load_documents().items()
               if isinstance(d, dict) and d.get("indexer") == "spark_sol_build"}
    was_in_neon = set(current)                    # what earlier runs really wrote
    before = (set(json.loads(row[0])) if row else set()) | was_in_neon
    pending0 = len(mm._load_pending())
    names = []
    cache = mm._load_local()
    items = list(documents_for(prj, skills or []))
    pointers = unchanged = 0
    same = lambda a, b: isinstance(b, dict) and {k: v for k, v in a.items() if k != "updated"} ==         {k: v for k, v in b.items() if k != "updated"}
    for i, (key, kind, text, source, summary, region, title) in enumerate(items):
        payload = build_payload(key, kind, text, source=source, summary=summary)
        pointers += "pointer" in payload
        payload.update(region=region, title=title, indexer="spark_sol_build")
        names.append(key)
        if same(payload, current.get(key)):          # already in Neon as is: no write, no new timestamp
            cache[key] = current[key]
            unchanged += 1
            continue
        cache[key] = payload                       # Flaxeon fills the cache dict only on a write
        mm.save_document(key, payload, _memory=cache, _write_cache=False)
        if (i + 1) % 100 == 0:
            say(f"  … {i + 1}/{len(items)} documents checked")
    mm._write_local(cache)                         # Flaxeon's offline copy, once
    stale = before - set(names)
    if not github_read:                           # not seen this run is not gone: keep GitHub-only repos
        stale = {n for n in stale if not n.startswith("gh_")}
    stale = sorted(stale)
    for n in stale:
        mm.forget_document(n)
    queued = len(mm._load_pending()) - pending0
    in_neon = _indexed_in_neon(neon)
    missing = sorted(set(names) - in_neon)
    left = sorted(set(stale) & in_neon)
    db.execute("INSERT OR REPLACE INTO meta VALUES ('published', ?)",
               (json.dumps(sorted(set(names) & in_neon)),))
    db.commit()
    db.close()
    out = {"saved": len(names) - len(missing), "written": len(names) - unchanged, "unchanged": unchanged,
           "queued": queued,
           "forgotten": len(set(stale) & was_in_neon) - len(left),
           "in_neon": len(in_neon), "expected": len(names), "text_dropped_to_pointer": pointers}
    if missing and len(missing) > queued:
        raise PublishError(f"{len(missing)} of {len(names)} summaries are not in Neon and only "
                           f"{queued} were queued (first missing: {', '.join(missing[:3])}). {json.dumps(out)}")
    if left:
        raise PublishError(f"{len(left)} stale summaries are still in Neon: {', '.join(left[:3])}")
    return out


def reload_server(say) -> None:
    try:
        req = urllib.request.Request("http://127.0.0.1:4700/reload", data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            say("  galaxy reloaded: " + r.read().decode()[:160])
    except Exception:
        say("  galaxy not running; it reads the new memory at its next start")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-publish", action="store_true")
    ap.add_argument("--no-github", action="store_true")
    ap.add_argument("--only", choices=["workspace", "pools", "skills", "github"])
    args = ap.parse_args(argv)
    say = lambda s: print(s, flush=True)               # noqa: E731

    if args.only == "github":
        args.only = "__none__"
    if not args.dry_run:                           # one writer at a time: a manual run and the GitHub watch
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        lock = open(INDEX_DIR / "build.lock", "a+")
        try:
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            say("another build.py run is writing the index; try again when it ends")
            return 3
        except ImportError:
            pass
    publishing =not args.dry_run and not args.no_publish and args.only in (None, "__none__")
    if publishing:                                 # before an hour of indexing, not after
        try:
            memory_gate()
        except PublishError as e:
            say(f"not publishing: {e}")
            return 2
    prj, stats = index(args, say)
    say("index: " + ", ".join(f"{k}={v:,}" for k, v in stats.items()))
    github_read = False
    if not args.no_github and args.only in (None, "__none__"):
        try:
            repos = github_repos(say)
            attach_github(prj, repos, not args.dry_run, say)
            github_read = True
        except Exception as e:
            say(f"  github skipped: {type(e).__name__}: {e}")
    elif args.no_github:
        say("  github skipped: --no-github")
    by_region = Counter(p["region"] for p in prj.by_key.values())
    say(f"projects: {len(prj.by_key)}  " + "  ".join(f"{k}={v}" for k, v in by_region.items()))
    skills = find_skills() if args.only in (None, "skills", "__none__") else []
    copies = sum(len(s["also"]) for s in skills)
    say(f"skills: {len(skills)} distinct ({copies} identical copies merged) from "
        + ", ".join(str(r) for k, r in ROOTS if k == "skills" and r.is_dir()))
    if args.dry_run:
        for p in sorted(prj.by_key.values(), key=lambda p: (p["region"], p["title"].lower())):
            say(f"  [{p['region']}] {summary_line(p)[:150]}")
        return 0
    save_projects(prj)
    if publishing:
        say("publishing one summary per project to Flaxeon's shared memory…")
        try:
            say("  " + json.dumps(publish(prj, say, github_read, skills)))
        except PublishError as e:
            say(f"publish FAILED: {e}")
            return 1
        reload_server(say)
    size = DB_PATH.stat().st_size / 1e9 if DB_PATH.exists() else 0
    say(f"done. index {DB_PATH} ({size:.2f} GB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
