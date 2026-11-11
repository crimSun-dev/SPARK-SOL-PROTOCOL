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

Outbound hosts: api.github.com (through the gh CLI) and Flaxeon's Neon (and
Firebase if configured) for the summaries. Nothing else.
"""
from __future__ import annotations

import argparse
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
PARENT = HERE.parent                                   # F.L.A.X.E.O.N
WORKSPACE = PARENT.parent                              # G:\...\Workspace
HOME = Path.home()
INDEX_DIR = HERE / "index"
DB_PATH = INDEX_DIR / "workspace.sqlite"

ROOTS = [
    ("workspace", WORKSPACE),
    ("pools", HOME / ".cursor" / "skills" / "POOL"),
    ("skills", HOME / ".cursor" / "skills"),           # POOL pruned here; it is its own root
    ("skills", HOME / ".claude" / "skills"),
]

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

    def __init__(self):
        self.git_roots: dict[str, set[Path]] = {}
        self.by_key: dict[str, dict] = {}

    def project_for(self, kind: str, root: Path, path: Path) -> dict:
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
        label = f"{root.parent.name} skills"          # ".claude skills" / ".cursor skills"
        return self._get("skills", label, root, "skills", "skills root")

    def _get(self, prefix: str, title: str, path: Path, region: str, kind: str) -> dict:
        key = f"{prefix}_{slug(title)}"
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


def github_repos(say) -> list[dict]:
    me = gh_json("api", "user", "--jq", "{login: .login}")["login"]
    owners = [me] + [o["login"] for o in (gh_json("api", "user/orgs") or [])]
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
        except Exception:
            r["readme"] = ""
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


def index(args, say) -> tuple[Projects, dict]:
    prj = Projects()
    db = None if args.dry_run else open_db()
    stats = Counter()
    seen: set[str] = set()
    roots = [(k, r) for k, r in ROOTS if r.is_dir() and (not args.only or args.only == k)]
    t0 = time.time()
    for kind, root in roots:
        say(f"{kind}: {root}")
        for path in walk(kind, root, prj):
            name = path.name
            try:
                st = path.stat()
            except OSError:
                continue
            p = prj.project_for(kind, root, path)
            ext = path.suffix.lower()
            rel = path.relative_to(Path(p["path"])) if Path(p["path"]) in path.parents else Path(name)
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
            "skills root": "Skills", "folder": "Folder"}.get(p["kind"], p["kind"])
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


def publish(prj: Projects, say) -> dict:
    """One repo_index document per project into Flaxeon's shared memory, through
    the parent's own save_document. Documents this indexer published before and
    no longer has are forgotten. Nothing else in the store is touched."""
    sys.path.insert(1, str(PARENT))
    from memory import memory_manager as mm
    from tools.memory_ingest import build_payload
    db = open_db()
    row = db.execute("SELECT v FROM meta WHERE k='published'").fetchone()
    before = set(json.loads(row[0])) if row else set()
    names = []
    cache = mm._load_local()
    items = sorted(prj.by_key.values(), key=lambda p: p["key"])
    for i, p in enumerate(items):
        payload = build_payload(p["key"], "repo_index", summary_text(p), source=p["path"],
                                summary=summary_line(p))
        payload.update(region=p["region"], title=p["title"], indexer="spark_sol_build")
        mm.save_document(p["key"], payload, _memory=cache, _write_cache=(i == len(items) - 1))
        names.append(p["key"])
        if (i + 1) % 50 == 0:
            say(f"  … {i + 1}/{len(items)} summaries saved")
    stale = sorted(before - set(names))
    for n in stale:
        mm.forget_document(n)
    back = sum(1 for n in names[:5] if isinstance(mm.load_document(n), dict))
    db.execute("INSERT OR REPLACE INTO meta VALUES ('published', ?)", (json.dumps(names),))
    db.commit()
    db.close()
    return {"saved": len(names), "forgotten": len(stale), "read_back": f"{back}/{min(5, len(names))}"}


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
    prj, stats = index(args, say)
    say("index: " + ", ".join(f"{k}={v:,}" for k, v in stats.items()))
    if not args.no_github and args.only in (None, "__none__"):
        try:
            repos = github_repos(say)
            attach_github(prj, repos, not args.dry_run, say)
        except Exception as e:
            say(f"  github skipped: {type(e).__name__}: {e}")
    by_region = Counter(p["region"] for p in prj.by_key.values())
    say(f"projects: {len(prj.by_key)}  " + "  ".join(f"{k}={v}" for k, v in by_region.items()))
    if args.dry_run:
        for p in sorted(prj.by_key.values(), key=lambda p: (p["region"], p["title"].lower())):
            say(f"  [{p['region']}] {summary_line(p)[:150]}")
        return 0
    save_projects(prj)
    if not args.no_publish and args.only in (None, "__none__"):
        say("publishing one summary per project to Flaxeon's shared memory…")
        say("  " + json.dumps(publish(prj, say)))
        reload_server(say)
    size = DB_PATH.stat().st_size / 1e9 if DB_PATH.exists() else 0
    say(f"done. index {DB_PATH} ({size:.2f} GB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
