"""SPARK SOL server. 127.0.0.1:4700 only. Standard library only.

Serves viewer/ and nothing else (config.json is a 404), and answers the page:
/chat, /tts, /hear, /remember, /health, /graph, /reload, /shutdown, /drill/*.
The memory sky comes from
read_memory.py; the full text of every record stays in this process, and the
browser only ever gets the plate's excerpt. voice.py and hear.py are
soft-imported: the server boots without either bay.

    python server.py               # re-read memory, then serve
    python server.py --no-read     # serve the last graph-data.js (no search index)
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import secrets
import http.server
import json
import math
import re
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter, deque
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = (HERE / "viewer").resolve()
CONFIG = HERE / "config.json"
CAPTURES = HERE / "notes" / "captures"
HOST, PORT = "127.0.0.1", 4700
sys.path.insert(0, str(HERE))

import netlog                                   # noqa: E402
import read_memory                              # noqa: E402

try:
    import voice                                # noqa: E402
except Exception as _e:                         # bay missing: the page uses the browser voice
    voice, VOICE_IMPORT_ERROR = None, f"{type(_e).__name__}: {_e}"
else:
    VOICE_IMPORT_ERROR = None
try:
    import hear                                 # noqa: E402
except Exception as _e:                         # bay missing: typing still works
    hear, HEAR_IMPORT_ERROR = None, f"{type(_e).__name__}: {_e}"
else:
    HEAR_IMPORT_ERROR = None

# ── persona: identical on every turn, always the first message ────────────
# Kept under 300 words (checked at boot). Control tags live inside it.
PERSONA = """You are Flaxeon, the notes instrument of F.L.A.X.E.O.N. You run on Draven's own machine and you speak to Draven alone.

How you answer:
- One true sentence first. Then only the facts that matter, in a sentence or two. Do not recite the note; it is already on the screen.
- Answer only from the notes sent with the question. If a note answers it, give the answer. Only if none does, say the notes do not cover it. Never invent a source. Never mention note numbers.
- Never claim an action happened. Only the server acts, and it reports what it did.
- If asked what a local turn costs: electricity. You live on this machine.
- Call the operator Draven, or nothing. No pet names. Never "sir".
- Wit is dry and rare. Never perform a joke.
- British spelling.
- Talk about scales, fire or saga plot only when the question is about that record.
- Plain spoken sentences: no lists, no markdown, no emoji.
- If a pronoun is needed for yourself, use she.

Asked to save, note or keep anything: reply only [REMEMBER] and the words."""

KEY_PLACEHOLDER = "PUT-YOUR-KEY-HERE"

DEFAULT_CONFIG = {
    "boot_brain": "local",
    "brain": {"base_url": "http://127.0.0.1:11434/v1", "model": "qwen3.5:9b",
              "api_key": "ollama", "extra_body": {"reasoning_effort": "none"}},
    "brains": {
        "local": {"base_url": "http://127.0.0.1:11434/v1", "model": "qwen3.5:9b",
                  "api_key": "ollama", "extra_body": {"reasoning_effort": "none"}},
        "big": {"base_url": "http://127.0.0.1:11434/v1", "model": "",
                "api_key": "ollama", "extra_body": {"reasoning_effort": "none"}},
        "claude": {"base_url": "https://api.anthropic.com", "model": "claude-opus-5-5",
                   "api_key": KEY_PLACEHOLDER},
    },
    "voice": {"url": "http://127.0.0.1:3900", "engine": "voxcpm2", "model_id": "voxcpm2",
              "profile": "Spark", "language": "en"},
    "_voice_mac_unselected": {
        "_comment": "Mac only. Not selected on this Windows machine. Copy into 'voice' on a Mac.",
        "engine": "mlx-audio", "model_id": "mlx-community/csm-1b-8bit"},
    "hearing": {"model": "large-v3-turbo", "wake_model": "small"},
}


def load_config() -> dict:
    if not CONFIG.exists():
        CONFIG.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


CFG: dict = {}
STATE = {"brain": "local", "voice_mode": "local", "boot_claimed": False,
         "sky_rev": 0, "mem_rev": 0, "shutting_down": False}
ARGS = {"mirror_only": False}
SERVER: dict = {"srv": None}
LOCK = threading.RLock()
HISTORY: deque = deque(maxlen=6)          # three exchanges; never written to the notes
GRAPH: dict = {"nodes": [], "links": [], "regions": [], "source": "none"}
INDEX: list[dict] = []                    # per node: title tokens, body Counter, text
DF: Counter = Counter()
BROWSER_HOSTS: dict = {"hosts": None, "t": None}


# ── search over the full text ─────────────────────────────────────────────
STOP = set("""a an and are as at be been but by can could did do does doing for from
had has have he her hers him his how i if in into is it its just me my of on or our
she so than that the their them then there these they this those to too up us was
we were what when where which who whom why will with would you your yours about
any all also am tell know say said want okay ok please hey spark flaxeon draven
today now doing going good fine well thanks thank hello hi morning evening night yes no""".split())


def tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if w in STOP or len(w) < 2:
            continue
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def index_node(n: dict) -> dict:
    text = n.get("text") or n.get("excerpt") or ""
    return {"title": set(tokens(n.get("label", "") + " " + str(n.get("key", "")))),
            "body": Counter(tokens(text)), "text": text}


def rebuild_index() -> None:
    INDEX.clear()
    DF.clear()
    for n in GRAPH["nodes"]:
        e = index_node(n)
        INDEX.append(e)
        DF.update(set(e["title"]) | set(e["body"]))


def score_notes(question: str, k: int = 6) -> list[tuple[int, float]]:
    """Keyword overlap on the whole record. A title match weighs three body matches."""
    q = set(tokens(question))
    if not q or not INDEX:
        return []
    N = len(INDEX)
    scored = []
    for i, e in enumerate(INDEX):
        s = 0.0
        for t in q:
            idf = math.log(1 + N / (1 + DF.get(t, 0)))
            if t in e["title"]:
                s += 3 * idf
            c = e["body"].get(t, 0)
            if c:
                s += idf * (1 + math.log(c))
        if s > 0:
            scored.append((i, round(s, 3)))
    scored.sort(key=lambda x: -x[1])
    return scored[:k]


def best_span(text: str, question: str, limit: int = 520) -> str:
    """The run of sentences in the full text that holds the most question words."""
    q = set(tokens(question))
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n{2,}", text or "") if s.strip()]
    if not sents:
        return ""
    best, best_hits = sents[0][:limit], -1
    for i in range(len(sents)):
        span, j = "", i
        while j < len(sents) and len(span) + len(sents[j]) + 1 <= limit:
            span = (span + " " + sents[j]).strip()
            j += 1
        if not span:
            span = sents[i][:limit]
        hits = sum(1 for t in tokens(span) if t in q)
        if hits > best_hits:
            best, best_hits = span, hits
    return best


# ── the Workspace index (build.py): full text on this machine ─────────────
INDEX_DB = HERE / "index" / "workspace.sqlite"


def coverage(question: str, text: str) -> float:
    """Share of the question's words that the text contains."""
    q = set(tokens(question))
    return len(q & set(tokens(text))) / len(q) if q else 0.0


def search_index(question: str, k: int = 3) -> list[dict]:
    """Best chunk per project from the local full-text index, at most k projects.
    Read-only; an index that is missing or mid-build returns nothing."""
    words = list(dict.fromkeys(re.findall(r"[a-z0-9]+", question.lower())))
    words = [w for w in words if w not in STOP and len(w) > 1]
    if not words or not INDEX_DB.exists():
        return []
    match = " OR ".join(f'"{w}"' for w in words[:12])
    try:
        con = sqlite3.connect(f"file:{INDEX_DB.as_posix()}?mode=ro", uri=True, timeout=2)
        try:
            rows = con.execute(
                "SELECT project, path, title, body FROM chunks WHERE chunks MATCH ? "
                "ORDER BY bm25(chunks, 4.0, 1.0) LIMIT 60", (match,)).fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return []
    out, seen = [], set()
    for project, path, title, body in rows:
        if project in seen:
            continue
        seen.add(project)
        out.append({"project": project, "path": path, "title": title, "body": body or "",
                    "coverage": coverage(question, title + " " + (body or ""))})
        if len(out) == k:
            break
    out.sort(key=lambda h: -h["coverage"])
    return out


def search_files(query: str, k: int = 10) -> list[dict]:
    """The page's file search: best chunk per file from the local index, at most k
    files, every word required first and any word as a fallback. Read-only. The
    snippet is already scrubbed; the index never held a key."""
    words = list(dict.fromkeys(re.findall(r"[a-z0-9]+", query.lower()[:200])))
    words = [w for w in words if w not in STOP and len(w) > 1][:8]
    if not words or not INDEX_DB.exists():
        return []
    out, seen = [], set()
    try:
        con = sqlite3.connect(f"file:{INDEX_DB.as_posix()}?mode=ro", uri=True, timeout=2)
        try:
            for joiner in (" AND ", " OR "):
                rows = con.execute(
                    "SELECT project, path, title, body FROM chunks WHERE chunks MATCH ? "
                    "ORDER BY bm25(chunks, 4.0, 1.0) LIMIT 80",
                    (joiner.join(f'"{w}"' for w in words),)).fetchall()
                for project, path, title, body in rows:
                    if path in seen:
                        continue
                    seen.add(path)
                    out.append({"project": project, "path": path, "title": title,
                                "snippet": best_span(body or "", query, 220)})
                    if len(out) == k:
                        return out
        finally:
            con.close()
    except sqlite3.Error:
        return out
    return out


# ── brains ────────────────────────────────────────────────────────────────
class BrainError(Exception):
    pass


def brain_cfg(name: str | None = None) -> dict:
    name = name or STATE["brain"]
    return dict(CFG["brains"].get(name) or CFG["brain"])


def where(name: str) -> str:
    return "the cloud" if "api.anthropic.com" in brain_cfg(name).get("base_url", "") else "this machine"


def _body_openai(b: dict, system: str, messages: list, max_tokens: int) -> tuple[str, dict, dict]:
    body = {"model": b["model"], "messages": [{"role": "system", "content": system}] + messages,
            "max_tokens": max_tokens, "stream": False}
    body.update(b.get("extra_body") or {})
    url = b["base_url"].rstrip("/") + "/chat/completions"
    return url, body, {"Authorization": "Bearer " + b.get("api_key", "")}


def _body_anthropic(b: dict, system: str, messages: list, max_tokens: int) -> tuple[str, dict, dict]:
    body = {"model": b["model"], "system": system, "messages": messages,
            "max_tokens": max_tokens}
    url = b["base_url"].rstrip("/") + "/v1/messages"
    return url, body, {"x-api-key": b.get("api_key", ""), "anthropic-version": "2023-06-01"}


def complete(b: dict, system: str, messages: list, max_tokens: int = 600) -> str:
    """One completion. Retries once with a larger budget if the reply is empty
    because it ran out of tokens. Never logs the key."""
    cloud = "api.anthropic.com" in b.get("base_url", "")
    for budget in (max_tokens, max_tokens * 3):
        url, body, auth = (_body_anthropic if cloud else _body_openai)(b, system, messages, budget)
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json", **auth})
        try:
            with netlog.open_url(req, "brain " + ("cloud" if cloud else "local") + " completion",
                                 300) as r:
                d = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise BrainError(f"the brain answered HTTP {e.code}") from e
        except Exception as e:
            raise BrainError(f"the brain did not answer ({type(e).__name__})") from e
        if cloud:
            text = "".join(c.get("text", "") for c in d.get("content", []) if c.get("type") == "text")
            finish = "length" if d.get("stop_reason") == "max_tokens" else d.get("stop_reason")
        else:
            c = (d.get("choices") or [{}])[0]
            text, finish = (c.get("message") or {}).get("content") or "", c.get("finish_reason")
        text = text.strip()
        if text or finish != "length":
            return text
    return text


def ollama_loaded(b: dict) -> bool:
    base = b["base_url"].rstrip("/").removesuffix("/v1")
    try:
        with netlog.open_url(base + "/api/ps", "brain load check", 3) as r:
            ps = json.loads(r.read())
        return any(m.get("name") == b["model"] or m.get("model") == b["model"]
                   for m in ps.get("models", []))
    except Exception:
        return False


# Idle after a turn, so the next sentence is not a cold load. Chosen at apply
# time (openspec flaxeon-spark-sol-link): 2 minutes. Nothing holds the model
# for the life of the process and nothing refreshes it on a timer.
TURN_KEEP_ALIVE = "2m"


def ollama_hold(b: dict, keep: str = TURN_KEEP_ALIVE) -> bool:
    """Load the model and keep it resident for `keep`. Blocks while it loads.
    keep="0" unloads it."""
    base = b["base_url"].rstrip("/").removesuffix("/v1")
    req = urllib.request.Request(base + "/api/generate",
                                 data=json.dumps({"model": b["model"], "keep_alive": keep}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with netlog.open_url(req, "brain load/keep-warm", 600) as r:
            r.read()
        return True
    except Exception:
        return False


# ── the busy flag: stop never drops the model mid-reply ──────────────────
GEN = {"n": 0}
GEN_DONE = threading.Condition()


@contextlib.contextmanager
def generating():
    with GEN_DONE:
        GEN["n"] += 1
    try:
        yield
    finally:
        with GEN_DONE:
            GEN["n"] -= 1
            GEN_DONE.notify_all()


def busy() -> bool:
    with GEN_DONE:
        return GEN["n"] > 0


def wait_idle(timeout: float | None = None) -> bool:
    with GEN_DONE:
        return GEN_DONE.wait_for(lambda: GEN["n"] == 0, timeout)


def think(b: dict, system: str, messages: list, max_tokens: int = 600) -> str:
    """One completion inside the busy flag. A local brain then gets the short
    post-turn idle (TURN_KEEP_ALIVE) before the flag drops."""
    with generating():
        text = complete(b, system, messages, max_tokens)
        if "api.anthropic.com" not in b.get("base_url", "") and b.get("model"):
            ollama_hold(b, TURN_KEEP_ALIVE)
        return text


def shutdown_worker(unload=None, exit_server=None) -> None:
    """Finish the reply in flight, unload the local model, then stop serving."""
    wait_idle()
    b = brain_cfg() if CFG else {}
    if b.get("model") and "api.anthropic.com" not in b.get("base_url", ""):
        (unload or ollama_hold)(b, "0")
    if exit_server is not None:
        exit_server()
    elif SERVER["srv"] is not None:
        SERVER["srv"].shutdown()


# ── the note door ─────────────────────────────────────────────────────────
class NoteWriteError(Exception):
    pass


def shared_memory():
    """Flaxeon's memory_manager: the notes Flame and Tempest already read.
    No Neon connection of SPARK's own; the parent module owns that."""
    parent = str(read_memory.PARENT)
    if parent not in sys.path:
        sys.path.insert(1, parent)
    from memory import memory_manager           # noqa: E402
    return memory_manager


def share_note(stem: str, text: str) -> tuple[bool, str | None]:
    """remember(stem, text, "notes"), then check it is really there.
    Never the persona document, the passkey, or machine-state rows."""
    if stem in read_memory.NEVER or stem in read_memory.MACHINE_STATE:
        return False, "that name is never written to shared memory"
    try:
        mm = shared_memory()
        mm.remember(stem, text, category="notes")
        entry = ((mm.load_memory() or {}).get("notes") or {}).get(stem)
        value = entry.get("value") if isinstance(entry, dict) else entry
        if not value:
            return False, "the shared memory did not keep it"
        return True, None
    except Exception as e:
        return False, f"the shared memory did not answer ({type(e).__name__})"


def _slug(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())[:6]
    return "-".join(words) or "note"


def commit_note(text: str) -> dict:
    """File first (the durable copy), then the live graph-data.js, then the index.
    Returns the receipt. Raises NoteWriteError; never a quiet success."""
    text = re.sub(r"\s+", " ", text or "").strip(" .,:;-")
    if not text:
        raise NoteWriteError("there was nothing after the phrase to remember")
    words = text.split()
    title = " ".join(words[:7]) + ("…" if len(words) > 7 else "")
    title = title[:1].upper() + title[1:]
    today = date.today().isoformat()
    with LOCK:
        try:
            CAPTURES.mkdir(parents=True, exist_ok=True)
            base = f"{today}-{_slug(text)}"
            path, k = CAPTURES / (base + ".md"), 2
            while path.exists():
                path, k = CAPTURES / f"{base}-{k}.md", k + 1
            path.write_text(f"# {title}\n\nDate: {today}\n\n{text}\n", encoding="utf-8")
        except OSError as e:
            raise NoteWriteError(f"the note file could not be written ({e.strerror or type(e).__name__})")
        cap = {"file": path.name, "stem": path.stem, "title": title, "date": today, "text": text}
        shared, shared_error = share_note(path.stem, text)
        if shared:      # one star: the notes fact, plated with the capture
            node = read_memory.fact_node("notes", path.stem,
                                         {"value": text, "updated": today}, cap)
        else:           # the file is the only copy
            node = read_memory.capture_node(cap)
        node["id"] = len(GRAPH["nodes"])
        related = next((i for i, _ in score_notes(text, 3)), -1)
        GRAPH["nodes"].append(node)
        if node["group"] not in GRAPH["regions"]:
            GRAPH["regions"].append(node["group"])
        try:
            read_memory.write_graph(GRAPH)
        except OSError as e:
            GRAPH["nodes"].pop()
            raise NoteWriteError(f"the note file is saved but the sky file could not be updated ({type(e).__name__})")
        e = index_node(node)
        INDEX.append(e)
        DF.update(set(e["title"]) | set(e["body"]))
        STATE["mem_rev"] += 1                  # the read-only web viewer follows this, not sky_rev
    public = {k: v for k, v in node.items() if k != "text"}
    return {"index": node["id"], "path": "notes/captures/" + path.name, "title": title,
            "text": text, "node": public, "related": related,
            "shared": shared, "shared_error": shared_error}


def forget_last(path: str) -> dict:
    """Preflight's clean-up: removes a capture only if it is the newest star.
    Ids are positions, so nothing older can be removed without a restart."""
    with LOCK:
        last = GRAPH["nodes"][-1] if GRAPH["nodes"] else None
        if (not last or last.get("group") not in ("captures", "notes")
                or last.get("source") != path):
            raise NoteWriteError("only the newest capture can be removed while running")
        f = (HERE / path).resolve()
        if CAPTURES.resolve() not in f.parents:
            raise NoteWriteError("not a capture path")
        f.unlink(missing_ok=True)
        forgotten = None
        if last["group"] == "notes":          # the shared copy goes too
            try:
                shared_memory().forget(last["key"], category="notes")
                forgotten = True
            except Exception:
                forgotten = False
        GRAPH["nodes"].pop()
        INDEX.pop()
        group = last["group"]
        if not any(n["group"] == group for n in GRAPH["nodes"]):
            GRAPH["regions"] = [r for r in GRAPH["regions"] if r != group]
        read_memory.write_graph(GRAPH)
        STATE["mem_rev"] += 1
        DF.clear()
        for e in INDEX:
            DF.update(set(e["title"]) | set(e["body"]))
    return {"removed": path, "shared_forgotten": forgotten}


# ── reload: the sky re-reads memory in this process ───────────────────────
def reload_sky(loader=None) -> dict:
    """Re-read the Flaxeon store and the Tempest pack file, rebuild the index,
    rewrite graph-data.js. No restart, no model call, nothing written back."""
    global GRAPH
    loader = loader or (lambda: read_memory.load(ARGS["mirror_only"]))
    with LOCK:
        graph = loader()
        GRAPH = graph
        rebuild_index()
        STATE["sky_rev"] += 1
        STATE["mem_rev"] += 1
        HISTORY.clear()                        # old answers cite old positions
    return {"source": GRAPH.get("source"), "note_count": len(GRAPH["nodes"]),
            "sky_rev": STATE["sky_rev"]}


# ── GitHub watch: new, deleted or pushed repos reach Flaxeon without a hand ──
GITHUB_SEEN = HERE / "cache" / "github_seen.json"
GITHUB_LOG = HERE / "cache" / "github_watch.log"
GITHUB = {"checked_at": None, "repos": None, "last_run": None, "last_result": None, "running": False}


def _gh_json(*args):
    import subprocess
    p = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip()[:200])
    return json.loads(p.stdout or "null")


def github_print() -> dict:
    """{nameWithOwner: pushedAt} for the signed-in account and its organisations."""
    me = _gh_json("api", "user", "--jq", "{login: .login}")["login"]
    owners = [me] + [o["login"] for o in (_gh_json("api", "user/orgs") or [])]
    out = {}
    for owner in owners:
        for r in _gh_json("repo", "list", owner, "--limit", "1000", "--json", "nameWithOwner,pushedAt") or []:
            out[r["nameWithOwner"]] = r.get("pushedAt")
    return out


def _log_github(line: str) -> None:
    with contextlib.suppress(OSError):
        GITHUB_LOG.parent.mkdir(parents=True, exist_ok=True)
        with GITHUB_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")


def run_indexer() -> tuple[int, str]:
    """One build.py run with the stored passkey in its environment only."""
    import os, subprocess
    import passkey_store
    key = passkey_store.load()
    if not key:
        return 2, "no passkey store (cache/passkey.dpapi): GitHub changed, publish pending"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("FLAXEON_", "TEMPEST_SOL_"))}
    env.update(FLAXEON_PASSKEY=key, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, str(HERE / "build.py")], cwd=HERE, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=3600)
    tail = [l for l in p.stdout.splitlines() if l.lstrip().startswith(("{", "publish FAILED", "not publishing",
                                                                         "another build", "projects:", "skills:"))]
    return p.returncode, " | ".join(tail)[-600:]


def watch_github(stop: threading.Event, every: float) -> None:
    """Every `every` seconds, compare the repos and their push times with what was
    last indexed. On a difference, run the indexer, which publishes and reloads
    the sky. The first check after a fresh install only records the baseline."""
    while True:
        try:
            now = github_print()
            GITHUB.update(checked_at=time.time(), repos=len(now))
            try:
                seen = json.loads(GITHUB_SEEN.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                seen = None
            if seen is None:
                GITHUB_SEEN.parent.mkdir(parents=True, exist_ok=True)
                GITHUB_SEEN.write_text(json.dumps(now, indent=1), encoding="utf-8")
                _log_github(f"baseline: {len(now)} repos")
            elif now != seen and not STATE["shutting_down"]:
                added = sorted(set(now) - set(seen)); gone = sorted(set(seen) - set(now))
                pushed = sorted(k for k in now if k in seen and now[k] != seen[k])
                _log_github(f"changed: +{added} -{gone} pushed {pushed[:10]}; indexing")
                GITHUB.update(running=True)
                code, tail = run_indexer()
                GITHUB.update(running=False, last_run=time.time(), last_result=f"exit {code}: {tail}")
                _log_github(f"indexer exit {code}: {tail}")
                if code == 0:
                    GITHUB_SEEN.write_text(json.dumps(now, indent=1), encoding="utf-8")
        except Exception as e:                     # gh offline, signed out, timed out: try again next time
            GITHUB.update(running=False, last_result=f"check failed: {type(e).__name__}: {str(e)[:160]}")
            _log_github(GITHUB["last_result"])
        if stop.wait(every):
            return


def _sky_print(graph: dict) -> str:
    """What a viewer would draw: nodes, links, regions. Not the read time."""
    pub = read_memory.public_graph(graph)
    return json.dumps([pub.get("nodes"), pub.get("links"), pub.get("regions")],
                      sort_keys=True, ensure_ascii=True, default=str)


def watch_memory(stop: threading.Event, every: float) -> None:
    """Re-read Neon every `every` seconds, outside the lock, so Flaxeon's own writes
    reach the sky. Swap only when what a viewer would draw changed, and only from a
    Neon read: a dropped connection never replaces the live sky with the mirror."""
    while not stop.wait(every):
        if STATE["shutting_down"]:
            return
        try:
            graph = read_memory.load(False)
        except Exception as e:
            print(f"SPARK SOL: memory watch read failed ({type(e).__name__})", flush=True)
            continue
        if graph.get("source") != "neon":
            continue
        with LOCK:
            same = _sky_print(graph) == _sky_print(GRAPH)
        if same:
            continue
        reload_sky(lambda: graph)
        netlog.note(read_memory.LAST_REMOTE_HOST or "neon", "memory read (Neon) by the watch")
        print(f"SPARK SOL: memory changed, sky swapped (notes={len(graph['nodes'])}, "
              f"mem_rev={STATE['mem_rev']})", flush=True)


# ── routes: checked before anything reaches the brain ─────────────────────
def _norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", s).strip()


def badge() -> dict:
    b = brain_cfg()
    return {"brain": STATE["brain"], "model": b.get("model", ""), "where": where(STATE["brain"]),
            "voice": STATE["voice_mode"], "sky_rev": STATE["sky_rev"]}


def r_voice_local(m, text):
    if voice is None:
        return {"answer": "The local voice bay is not installed. The browser voice stays."}
    try:
        voice.select_engine()
    except Exception:
        STATE["voice_mode"] = "browser"
        return {"answer": "The local voice is not answering. The browser voice stays."}
    STATE["voice_mode"] = "local"
    return {"answer": "Local voice."}


def r_voice_browser(m, text):
    STATE["voice_mode"] = "browser"
    return {"answer": "Browser voice."}


def switch_brain(name: str) -> dict:
    """Runtime only; boot_brain in config.json is not touched."""
    b = CFG["brains"].get(name)
    if not b:
        return {"answer": f"There is no brain called {name} on the shelf."}
    if not b.get("model"):
        return {"answer": f"The {name} brain has no model set in config.json. Staying put."}
    cloud = "api.anthropic.com" in b.get("base_url", "")
    if cloud and (not b.get("api_key") or b["api_key"] == KEY_PLACEHOLDER):
        return {"answer": "The cloud key is not set, so I am staying on this machine."}
    if not cloud and not ollama_loaded(b):
        return {"answer": "One moment.", "next": {"switch": name}}
    return confirm_switch(name)


def confirm_switch(name: str) -> dict:
    b = CFG["brains"][name]
    cloud = "api.anthropic.com" in b.get("base_url", "")
    place = "the cloud" if cloud else "this machine"
    try:
        line = think(b, PERSONA, [{"role": "user", "content":
                        f"You are now the {name} brain, model {b['model']}, running on {place}. "
                        f"Confirm that in one short sentence that names {place}."}], 80)
    except BrainError as e:
        return {"answer": ("The cloud did not answer" if cloud else f"The {name} brain did not answer")
                + f", so I am staying on the {STATE['brain']} brain."}
    with LOCK:
        STATE["brain"] = name
        HISTORY.clear()
    return {"answer": line or f"{name.capitalize()} brain, on {place}."}


def r_which(m, text):
    b = brain_cfg()
    return {"answer": f"The {STATE['brain']} brain, {b.get('model')}, on {where(STATE['brain'])}."}


def r_remember(m, text):
    try:
        receipt = commit_note(m.group("rest") or "")
    except NoteWriteError as e:
        return {"answer": f"That did not save: {e}.", "error": str(e)}
    said = receipt["text"] if len(receipt["text"]) <= 160 else receipt["title"]
    if receipt.get("shared"):
        tail = " Flame and Tempest can see it too."
    else:
        tail = (" The shared memory did not take it, so only this galaxy has it"
                f" ({receipt.get('shared_error') or 'unknown error'}).")
    return {"answer": f"Saved: {said.rstrip('.')}.{tail}", "birth": receipt}


ROUTES = [
    (re.compile(r"^(?:please )?use (?:your|the) local voice\b", re.I), r_voice_local),
    (re.compile(r"^(?:please )?use (?:your|the) browser voice\b", re.I), r_voice_browser),
    (re.compile(r"^(?:switch to (?:your )?local brain|go local)\b", re.I), lambda m, t: switch_brain("local")),
    (re.compile(r"^switch to (?:your )?big brain\b", re.I), lambda m, t: switch_brain("big")),
    (re.compile(r"^(?:switch to claude|go cloud)\b", re.I), lambda m, t: switch_brain("claude")),
    (re.compile(r"^which brain are you on\b", re.I), r_which),
    (re.compile(r"^(?:remember that|note to self|don'?t let me forget|do not let me forget|log this)"
                r"[\s,:;.\-]*(?P<rest>.*)$", re.I | re.S), r_remember),
]

# The only control tag. [SWITCH ...] was tried against qwen3.5:9b on 2026-11-10 and
# dropped: it missed 2 of 5 and sent "the cloud" to the wrong shelf entry. The
# spoken routes above are the brain switch.
TAG_REMEMBER = re.compile(r"\[REMEMBER\]\s*(?P<rest>.+)", re.I | re.S)


def chat(question: str) -> dict:
    t0 = time.perf_counter()
    q = _norm(question)
    if not q:
        return {"answer": "", "nodes": [], "seconds": 0.0, **badge()}
    for pat, fn in ROUTES:
        m = pat.match(q)
        if m:
            out = fn(m, q)
            out.setdefault("nodes", [])
            if out.get("birth"):
                out["nodes"] = [out["birth"]["index"]]
            out.update(route=pat.pattern[:40], seconds=round(time.perf_counter() - t0, 2), **badge())
            return out
    files = search_index(q)                     # the Workspace index, outside the lock
    with LOCK:                                  # a reload cannot swap the sky mid-score
        hits = score_notes(q)
        top = hits[0][1] if hits else 0
        mem = [i for i, s in hits if s >= top * 0.5]
        # Memory and the file index score on different scales, so they meet on
        # coverage: the share of the question's words each source holds.
        key_to_id = {n.get("key"): n["id"] for n in GRAPH["nodes"]}
        cands = [(coverage(q, INDEX[i]["text"] + " " + GRAPH["nodes"][i]["label"]), i) for i in mem]
        cands += [(h["coverage"], key_to_id[h["project"]]) for h in files if h["project"] in key_to_id]
        best = max((c for c, _ in cands), default=0)
        if files:
            cited = list(dict.fromkeys(i for c, i in sorted(cands, key=lambda x: -x[0])
                                       if best >= .5 and c >= best * .8))
        else:                                   # memory only: the rule the sky already had
            cited = mem
        notes = []
        for n, (i, _) in enumerate(hits[: 6 - min(3, len(files))], 1):
            node = GRAPH["nodes"][i]
            region = read_memory._human(node["group"])
            notes.append(f"[{n}] {node['label']} ({region}): {best_span(INDEX[i]['text'], q)}")
        for h in files:
            notes.append(f"[{len(notes) + 1}] {h['title']} (file {h['path']}): {best_span(h['body'], q)}")
    today = datetime.now().strftime("%A %d %B %Y")
    user = (f"Today is {today}.\n\nNotes:\n" + ("\n\n".join(notes) if notes else "(no note matched)")
            + f"\n\nQuestion: {q}")
    b = brain_cfg()
    try:
        answer = think(b, PERSONA, list(HISTORY) + [{"role": "user", "content": user}])
    except BrainError as e:
        return {"answer": f"No answer: {e}.", "nodes": [], "error": str(e),
                "seconds": round(time.perf_counter() - t0, 2), **badge()}
    out = {"nodes": cited}
    tr = TAG_REMEMBER.search(answer)
    if tr:
        out.update(r_remember(tr, q))
        out["tag"] = "REMEMBER"
        out["nodes"] = [out["birth"]["index"]] if out.get("birth") else []
    else:
        out["answer"] = re.sub(r"\s*\[\d\]", "", answer).strip()
        with LOCK:
            HISTORY.append({"role": "user", "content": q})
            HISTORY.append({"role": "assistant", "content": out["answer"]})
    out.update(seconds=round(time.perf_counter() - t0, 2), **badge())
    return out


# ── HTTP ──────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = {f"http://{HOST}:{PORT}", f"http://localhost:{PORT}"}
# The GitHub Pages viewer. It may READ the sky and the health line from this
# machine's server and nothing else: no /chat, no /remember, no POST of any kind.
WEB_VIEWER_ORIGINS = {"https://crimsun-dev.github.io"}
WEB_VIEWER_PATHS = {"/graph", "/health", "/search"}
# A paired web viewer may also ask. Pairing takes the code the local page shows;
# asking takes the token pairing returned. No other POST is open to the web.
WEB_POST_PATHS = {"/pair", "/chat"}
WEB_TOKENS = HERE / "cache" / "web_tokens.json"       # SHA-256 of each token; delete to unpair all
PAIR = {"code": "", "misses": 0}
PAIR_LOCK = threading.Lock()


def new_pair_code() -> None:
    PAIR["code"], PAIR["misses"] = f"{secrets.randbelow(10 ** 6):06d}", 0


def _token_hashes() -> set[str]:
    try:
        return set(json.loads(WEB_TOKENS.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def token_ok(token: str | None) -> bool:
    return bool(token) and hashlib.sha256(token.encode()).hexdigest() in _token_hashes()


def pair(code: str) -> str | None:
    """A token for the right code. Five misses, or one success, replace the code."""
    with PAIR_LOCK:
        if not PAIR["code"]:
            new_pair_code()
        if not secrets.compare_digest(str(code or "").strip(), PAIR["code"]):
            PAIR["misses"] += 1
            if PAIR["misses"] >= 5:
                new_pair_code()
            return None
        token = secrets.token_urlsafe(32)
        hashes = _token_hashes() | {hashlib.sha256(token.encode()).hexdigest()}
        WEB_TOKENS.parent.mkdir(parents=True, exist_ok=True)
        WEB_TOKENS.write_text(json.dumps(sorted(hashes)), encoding="utf-8")
        new_pair_code()
        return token


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".mjs": "text/javascript",
                      ".woff2": "font/woff2"}
    protocol_version = "HTTP/1.1"

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    # static: viewer/ and nothing else
    def send_head(self):
        target = Path(self.translate_path(self.path)).resolve()
        if target != ROOT and ROOT not in target.parents:
            self.send_error(404)
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass

    def _send(self, code: int, obj=None, body: bytes | None = None,
              ctype="application/json", headers=None):
        if body is None:
            body = json.dumps(obj, ensure_ascii=False).encode()
        # A refused POST whose body was never read would leave those bytes on a
        # kept-alive connection, to be parsed as the next request (a 501).
        if self.command == "POST" and not getattr(self, "_body_read", False):
            self.close_connection = True
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in {**getattr(self, "_cors", {}), **(headers or {})}.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> bytes:
        self._body_read = True
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(min(n, 20 * 1024 * 1024)) if n else b""

    def _json_body(self) -> dict:
        try:
            d = json.loads(self._body() or b"{}")
            return d if isinstance(d, dict) else {}
        except ValueError:
            return {}

    def _web_viewer(self, path: str, post: bool = False) -> dict:
        """CORS headers for the web viewer on the routes it may use, or none."""
        o = self.headers.get("Origin")
        if o not in WEB_VIEWER_ORIGINS or path not in (WEB_POST_PATHS if post else WEB_VIEWER_PATHS):
            return {}
        return {"Access-Control-Allow-Origin": o, "Vary": "Origin"}

    def do_OPTIONS(self):                       # preflight: the web viewer's GETs, /pair and /chat
        self._cors = {}
        path = urlsplit(self.path).path
        post = path in WEB_POST_PATHS
        h = self._web_viewer(path, post)
        if not h:
            return self._send(403, {"error": "origin not allowed"})
        h.update({"Access-Control-Allow-Methods": "POST" if post else "GET",
                  "Access-Control-Allow-Private-Network": "true",
                  "Access-Control-Max-Age": "600"})
        if post:
            h["Access-Control-Allow-Headers"] = "Content-Type, X-Spark-Token"
        return self._send(204, body=b"", headers=h)

    def _origin_ok(self) -> bool:
        o = self.headers.get("Origin")
        return o is None or o in ALLOWED_ORIGINS

    def do_GET(self):
        self._cors = {}
        u = urlsplit(self.path)
        web = self._web_viewer(u.path)
        if u.path == "/health":                 # the web viewer never claims the boot line
            return self._send(200, health(None if web else parse_qs(u.query)), headers=web)
        if u.path == "/graph":                  # the public excerpt graph, never `text`
            with LOCK:
                public = read_memory.public_graph(GRAPH)
            return self._send(200, {**public, "sky_rev": STATE["sky_rev"],
                                    "mem_rev": STATE["mem_rev"]}, headers=web)
        if u.path == "/pair/code":              # the local page only: no CORS, loopback, own origin
            o = self.headers.get("Origin")
            if not self._loopback() or (o is not None and o not in ALLOWED_ORIGINS) or web:
                return self._send(403, {"error": "local page only"})
            with PAIR_LOCK:
                if not PAIR["code"]:
                    new_pair_code()
                return self._send(200, {"code": PAIR["code"], "paired": len(_token_hashes())})
        if u.path == "/search":                 # read-only file search for the find box
            q = (parse_qs(u.query).get("q") or [""])[0]
            with LOCK:
                key_to_id = {n.get("key"): n["id"] for n in GRAPH["nodes"]}
            hits = search_files(q)
            for h in hits:
                h["star"] = key_to_id.get(h["project"])
            return self._send(200, {"query": q[:200], "files": hits}, headers=web)
        if u.path == "/drill/connections":
            since = float((parse_qs(u.query).get("since") or ["0"])[0])
            # The page's list is everything it has ever loaded, so the latest post
            # is complete whenever it was sent. None means no page ever posted.
            return self._send(200, {"server": netlog.since(since),
                                    "browser": BROWSER_HOSTS["hosts"],
                                    "browser_posted_at": BROWSER_HOSTS["t"]})
        return super().do_GET()

    def _loopback(self) -> bool:
        return self.client_address[0] in ("127.0.0.1", "::1")

    def do_POST(self):
        self._body_read = False                 # per request: the handler serves a whole connection
        self._cors = {}
        u = urlsplit(self.path)
        if self.headers.get("Origin") in WEB_VIEWER_ORIGINS:
            self._cors = self._web_viewer(u.path, post=True)
            if not self._cors:                  # every other POST stays closed to the web
                return self._send(403, {"error": "origin not allowed"})
            if u.path == "/pair":
                token = pair(str(self._json_body().get("code") or ""))
                return self._send(200, {"token": token}) if token else self._send(403, {"error": "wrong code"})
            if not token_ok(self.headers.get("X-Spark-Token")):
                return self._send(401, {"error": "not paired"})
        elif not self._origin_ok():
            return self._send(403, {"error": "origin not allowed"})
        try:
            if u.path in ("/reload", "/shutdown") and not self._loopback():
                return self._send(403, {"error": "loopback only"})
            if u.path == "/reload":
                try:
                    return self._send(200, reload_sky())
                except Exception as e:           # the previous sky stays
                    return self._send(500, {"error": f"reload failed ({type(e).__name__})"})
            if u.path == "/shutdown":
                waiting = busy()
                if not STATE["shutting_down"]:
                    STATE["shutting_down"] = True
                    threading.Thread(target=shutdown_worker, daemon=True,
                                     name="spark-shutdown").start()
                return self._send(202, {"stopping": True, "waiting_for_reply": waiting})
            if STATE["shutting_down"] and u.path in ("/chat", "/remember"):
                return self._send(503, {"answer": "SPARK SOL is stopping.", "nodes": [],
                                        "error": "stopping"})
            if u.path == "/chat":
                d = self._json_body()
                if isinstance(d.get("next"), dict) and d["next"].get("switch"):
                    out = confirm_switch(str(d["next"]["switch"]))
                    out.setdefault("nodes", [])
                    return self._send(200, {**out, **badge()})
                return self._send(200, chat(str(d.get("text") or "")))
            if u.path == "/remember":
                try:
                    r = commit_note(str(self._json_body().get("text") or ""))
                except NoteWriteError as e:
                    return self._send(500, {"error": str(e)})
                return self._send(201, r)
            if u.path == "/remember/undo":
                try:
                    return self._send(200, forget_last(str(self._json_body().get("path") or "")))
                except NoteWriteError as e:
                    return self._send(409, {"error": str(e)})
            if u.path == "/tts":
                return self._tts(str(self._json_body().get("text") or ""))
            if u.path == "/hear":
                return self._hear(parse_qs(u.query))
            if u.path == "/drill/browser":
                hosts = self._json_body().get("hosts")
                BROWSER_HOSTS.update(hosts=sorted({str(h) for h in hosts or []}), t=time.time())
                return self._send(204, body=b"")
        except Exception as e:                       # never a crash, never a key in the reply
            return self._send(500, {"error": type(e).__name__})
        return self._send(404, {"error": "not found"})

    def _tts(self, text: str):
        fallback = {"X-Spark-Voice": "browser"}
        if voice is None or STATE["voice_mode"] != "local":
            return self._send(503, {"fallback": "browser"}, headers=fallback)
        if not voice.is_up():
            return self._send(503, {"fallback": "browser"}, headers=fallback)
        try:
            wav = voice.synthesize(text[:voice.MAX_CHARS])
        except Exception:
            return self._send(503, {"fallback": "browser"}, headers=fallback)
        return self._send(200, body=wav, ctype="audio/wav",
                          headers={"X-Spark-Voice": voice.header()})

    def _hear(self, q):
        if hear is None or hear.status()["status"] != "ready":
            return self._send(503, {"error": "ears down",
                                    "status": hear.status()["status"] if hear else "missing"})
        which = (q.get("model") or ["command"])[0]
        try:
            text, secs = hear.transcribe(self._body(), "wake" if which == "wake" else "command")
        except Exception as e:
            return self._send(400, {"error": f"could not hear that clip ({type(e).__name__})"})
        return self._send(200, {"text": text, "seconds": secs})


def health(q: dict | None = None) -> dict:
    v = voice.status() if voice else {"status": "missing", "error": VOICE_IMPORT_ERROR}
    h = hear.status() if hear else {"status": "missing", "error": HEAR_IMPORT_ERROR}
    boot_line = False
    if q and q.get("claim_boot") and v["status"] == "ready" and STATE["voice_mode"] == "local":
        with LOCK:
            if not STATE["boot_claimed"]:
                STATE["boot_claimed"] = boot_line = True
    v = {k: v.get(k) for k in ("status", "engine", "model_id", "profile", "error")}
    return {**badge(), "voice_bay": v, "hearing": h, "note_count": len(GRAPH["nodes"]),
            "mem_rev": STATE["mem_rev"],
            "github": {"repos": GITHUB["repos"], "checked_at": GITHUB["checked_at"],
                       "running": GITHUB["running"], "last_run": GITHUB["last_run"],
                       "last_result": (GITHUB["last_result"] or "")[:160]},
            "source": GRAPH.get("source"), "boot_line": boot_line,
            "constants": {"SILENCE_MS": getattr(hear, "SILENCE_MS", 700),
                          "FINISH_MS": getattr(hear, "FINISH_MS", 900),
                          "MIN_UTTERANCE_MS": getattr(hear, "MIN_UTTERANCE_MS", 300)}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-read", action="store_true")
    ap.add_argument("--mirror-only", action="store_true", help="skip Neon (the offline drill)")
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--watch", type=float, default=60.0,
                    help="seconds between Neon re-reads for the live sky (0 turns the watch off)")
    ap.add_argument("--github-watch", type=float, default=600.0,
                    help="seconds between GitHub checks that re-run the indexer on a change (0 turns it off)")
    args = ap.parse_args()
    ARGS["mirror_only"] = bool(args.mirror_only)
    assert len(PERSONA.split()) < 300, "PERSONA must stay under 300 words"

    CFG.update(load_config())
    STATE["brain"] = CFG.get("boot_brain") or "local"
    if STATE["brain"] not in CFG["brains"]:
        STATE["brain"] = "local"

    global GRAPH
    if args.no_read:
        print("SPARK SOL: --no-read, search index is the last plate excerpts only")
        try:
            s = (ROOT / "graph-data.js").read_text(encoding="utf-8")
            GRAPH = json.loads(s[s.index("{"):s.rindex("}") + 1])
        except Exception:
            pass
    else:
        t = time.time()
        GRAPH = read_memory.load(args.mirror_only)
        if GRAPH["source"] == "neon":
            netlog.note(read_memory.LAST_REMOTE_HOST or "neon", "memory read (Neon) at boot")
        print(f"SPARK SOL: memory source={GRAPH['source']} notes={len(GRAPH['nodes'])} "
              f"({time.time() - t:.1f}s)")
    rebuild_index()

    stop = threading.Event()
    b = brain_cfg()
    # The local model loads on the first turn and idles out TURN_KEEP_ALIVE after
    # the last one; it is not pinned for the life of the process.
    if voice:
        voice.configure(CFG.get("voice", {}))
        threading.Thread(target=voice.watch, args=(stop,), daemon=True).start()
        threading.Thread(target=voice.keep_warm, args=(stop,), daemon=True).start()
    else:
        print("SPARK SOL: voice bay missing:", VOICE_IMPORT_ERROR)
    if args.watch > 0 and not args.no_read and not args.mirror_only:
        threading.Thread(target=watch_memory, args=(stop, max(10.0, args.watch)), daemon=True,
                         name="spark-memory-watch").start()
    if args.github_watch > 0 and not args.no_read and not args.mirror_only:
        threading.Thread(target=watch_github, args=(stop, max(60.0, args.github_watch)), daemon=True,
                         name="spark-github-watch").start()
    if hear:
        threading.Thread(target=hear.load_models, args=(CFG.get("hearing", {}),), daemon=True).start()
    else:
        print("SPARK SOL: hearing bay missing:", HEAR_IMPORT_ERROR)

    class Server(http.server.ThreadingHTTPServer):
        daemon_threads = True

        def handle_error(self, request, client_address):
            if isinstance(sys.exc_info()[1], (ConnectionAbortedError, ConnectionResetError,
                                              BrokenPipeError)):
                return                        # the tab went away mid-reply
            super().handle_error(request, client_address)

    srv = Server((HOST, args.port), Handler)
    SERVER["srv"] = srv
    print(f"SPARK SOL page: http://{HOST}:{args.port}/   brain={STATE['brain']} ({b.get('model')})",
          flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    stop.set()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
