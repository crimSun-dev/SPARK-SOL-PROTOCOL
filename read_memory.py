"""SPARK SOL memory reader. Read-only.

Turns the parent F.L.A.X.E.O.N memory store, plus the rows only the Tempest
pack file holds, into viewer/graph-data.js, the sky the protocol page draws. Neon is canonical. When Neon cannot be reached
(no driver, no URL, no network), the reader uses the local mirror
memory/long_term.json in the parent folder and says so in the file it writes.

It never writes to Neon, never runs the parent's schema DDL, and never copies
the connection string, the passkey row, or machine-state documents into
viewer/. Standard library only; Neon additionally needs the parent's psycopg.

    python read_memory.py                 # Neon first, mirror on failure
    python read_memory.py --mirror-only   # skip Neon (the offline drill)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent                      # the F.L.A.X.E.O.N root
MIRROR = PARENT / "memory" / "long_term.json"
# Tempest's pack store: a hand-started Tempest keeps writing here. The sky reads
# it and never writes it, nor copies it into the Flaxeon store.
PACK = PARENT / "TEMPEST SOL PROTOCOL" / "memory" / "long_term.json"
PACK_LABEL = "Tempest pack store (TEMPEST SOL PROTOCOL/memory/long_term.json)"
OUT = HERE / "viewer" / "graph-data.js"
CAPTURES = HERE / "notes" / "captures"    # this folder's own notes; the file is the source

# The host the last Neon read opened, for the server's connection log. Host only.
LAST_REMOTE_HOST = None

# Mirrors memory_manager.CATEGORIES; imported from the parent when it loads.
CATEGORIES = ("identity", "preferences", "projects",
              "relationships", "wishes", "notes")
# Project summaries written by build.py (kind repo_index) get their own regions.
INDEX_REGIONS = ("workspace", "pools", "experience", "skills")
REGIONS = CATEGORIES + ("documents", "sessions", "captures") + INDEX_REGIONS
# A category the operator gave a fed or moved project (feeds.py) is a region of its own.
REGION_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,23}$")

# Never a star: the operator passkey row and the parent's machine state.
NEVER = {"operator_passkey", "cloud_lock_token"}
MACHINE_STATE = {"monitors", "pushup_sessions", "reminders", "forgotten_facts"}
SECRETISH = re.compile(r"(passkey|api[_-]?key|secret|credential|token|password)", re.I)
SCRUB = [
    re.compile(r"postgres(?:ql)?://\S+", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}"),
]
EXCERPT = 700


def _scrub(text: str) -> str:
    for pat in SCRUB:
        text = pat.sub("[removed]", text)
    return text


_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*(.+?)\s*#*\s*$", re.M)
_MD = [
    (re.compile(r"(\*\*|__)(.+?)\1"), r"\2"),           # bold
    (re.compile(r"(?<!\w)[*_](\S.*?\S|\S)[*_](?!\w)"), r"\1"),  # italic
    (re.compile(r"`([^`]*)`"), r"\1"),                    # code ticks
    (re.compile(r"^\s*[-*+]\s+", re.M), ""),              # list bullets
    (re.compile(r"^\s*-{3,}\s*$", re.M), ""),              # rules
    (re.compile(r"\[([^\]]+)\]\([^)]*\)"), r"\1"),        # links
]


def _end_heading(m) -> str:
    """A heading becomes a sentence so it does not run into the next line."""
    t = m.group(1)
    return "\n\n" + (t if t[-1:] in ".!?:" else t + ".") + "\n\n"


def _plain(text: str) -> str:
    """Markdown marks off, so the plate reads as prose. Words are untouched;
    only heading lines gain a full stop."""
    text = _HEADING.sub(_end_heading, text)
    for pat, sub in _MD:
        text = pat.sub(sub, text)
    return text


def _excerpt(text: str) -> str:
    """About 700 characters, cut at a sentence. Paragraphs stay paragraphs."""
    blocks = [" ".join(b.split()) for b in re.split(r"\n\s*\n", _plain(text or ""))]
    blocks = [_scrub(b) for b in blocks if b]
    out, used = [], 0
    for blk in blocks:
        room = EXCERPT - used
        if room <= 40:
            break
        if len(blk) <= room:
            out.append(blk); used += len(blk) + 2
            continue
        cut = blk[:room]
        stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
        out.append(cut[: stop + 1] if stop > room * 0.5 else cut.rstrip() + "…")
        break
    return "\n\n".join(out)


def _human(key: str) -> str:
    words = re.sub(r"[_\-]+", " ", key).strip()
    return words[:1].upper() + words[1:] if words else key


def _day(ts) -> str | None:
    if not ts:
        return None
    return str(ts)[:10]


# ── sources ────────────────────────────────────────────────────────────────

def read_neon():
    """Returns (facts, sessions, documents) from Neon, or raises."""
    sys.path.insert(0, str(PARENT))
    from memory.config_manager import get_neon_url      # noqa: E402
    from memory.neon_store import NeonStore              # noqa: E402
    try:
        from memory import memory_manager as mm          # noqa: E402
        global CATEGORIES, MACHINE_STATE
        CATEGORIES = tuple(mm.CATEGORIES)
        MACHINE_STATE = set(mm.MACHINE_STATE_DOCUMENTS)
    except Exception:
        pass
    url = get_neon_url()
    if not url:
        raise RuntimeError("no Neon URL configured")
    global LAST_REMOTE_HOST
    try:
        from urllib.parse import urlsplit
        LAST_REMOTE_HOST = urlsplit(url).hostname or "neon"
    except Exception:
        LAST_REMOTE_HOST = "neon"
    store = NeonStore(url)
    store._schema_ready = True       # read-only: never run the CREATE TABLEs
    facts = {}
    for (cat, key), row in store.load_facts().items():
        facts.setdefault(cat, {})[key] = {"value": row.get("value", ""),
                                          "updated_at": row.get("updated_at")}
    sessions = store.load_sessions(limit=500)
    documents = store.load_documents()
    return facts, sessions, documents


def read_mirror():
    data = json.loads(MIRROR.read_text(encoding="utf-8"))
    facts = {c: data.get(c) or {} for c in CATEGORIES}
    sessions = data.get("sessions") or []
    documents = {k: v for k, v in data.items()
                 if k not in CATEGORIES and k != "sessions"}
    return facts, sessions, documents


def read_pack(path: Path | None = None):
    """The Tempest pack long-term file as (facts, documents). Missing = empty.
    Read only: the file is opened for reading and nothing is written back."""
    path = PACK if path is None else Path(path)
    if not path.is_file():
        return {}, {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}, {}
    facts = {c: data.get(c) for c in CATEGORIES if isinstance(data.get(c), dict)}
    documents = {k: v for k, v in data.items()
                 if k not in CATEGORIES and k != "sessions"}
    return facts, documents


def merge_pack(facts, documents, pack_facts, pack_documents):
    """Pack rows whose key the Flaxeon store lacks. The Flaxeon value wins a
    collision, so a key is never two stars. Returns (facts, documents) of the
    pack-only rows; build_graph marks them as pack stars."""
    only_facts = {}
    for cat, rows in (pack_facts or {}).items():
        mine = facts.get(cat) or {}
        extra = {k: v for k, v in rows.items() if k not in mine}
        if extra:
            only_facts[cat] = extra
    only_docs = {k: v for k, v in (pack_documents or {}).items() if k not in documents}
    return only_facts, only_docs


_CAP_DATE = re.compile(r"^\s*Date:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M | re.I)


def read_captures():
    """notes/captures/*.md, written by the server's commit_note(). Each file is
    the only durable copy of its star, so every read puts it back on the sky."""
    out = []
    if not CAPTURES.is_dir():
        return out
    for p in sorted(CAPTURES.glob("*.md")):
        try:
            raw = p.read_text(encoding="utf-8")
        except OSError:
            continue
        m = _HEADING.search(raw)
        title = m.group(1).strip() if m else _human(p.stem)
        d = _CAP_DATE.search(raw)
        date = d.group(1) if d else datetime.fromtimestamp(
            p.stat().st_mtime, timezone.utc).date().isoformat()
        body = raw
        if m:
            body = body.replace(m.group(0), "", 1)
        if d:
            body = body.replace(d.group(0), "", 1)
        out.append({"file": p.name, "stem": p.stem, "title": title,
                    "date": date, "text": body.strip()})
    return out


def capture_node(cap: dict) -> dict:
    """One capture as a star. Bone: no category dye, no pool dye."""
    text = _scrub(cap["text"])
    return dict(label=cap["title"], key=cap["stem"], group="captures",
                kind="capture", excerpt=_excerpt(text), updated=cap["date"],
                source="notes/captures/" + cap["file"], size=len(text),
                text=text)


# ── graph ──────────────────────────────────────────────────────────────────

def fact_node(cat: str, key: str, row, cap: dict | None = None) -> dict:
    """One fact as a star. A notes fact saved from a galaxy capture keeps the
    capture's title and file as its plate, so the note is one star, not two."""
    row = row if isinstance(row, dict) else {"value": row}
    value = str(row.get("value", ""))
    n = dict(label=_human(key), key=key, group=cat, kind="fact",
             excerpt=_excerpt(value), updated=_day(row.get("updated_at")
                                                    or row.get("updated")),
             size=len(value), text=_scrub(value))
    if cap is not None:
        n.update(label=cap["title"], source="notes/captures/" + cap["file"],
                 updated=n["updated"] or cap["date"])
    return n


def build_graph(facts, sessions, documents, captures=(), pack=None):
    """Nodes carry `text`, the whole scrubbed record, for the server's search.
    write() drops it: the browser only ever receives the excerpt.

    `pack` is (facts, documents) of pack-only rows (see merge_pack); each such
    star's plate names the Tempest pack store."""
    nodes = []
    pack_facts, pack_docs = pack or ({}, {})
    caps = {c["stem"]: c for c in captures}
    shared_stems = set()

    def add(**n):
        n["id"] = len(nodes)
        nodes.append(n)

    for cat in CATEGORIES:
        rows = [(k, r, False) for k, r in (facts.get(cat) or {}).items()]
        rows += [(k, r, True) for k, r in (pack_facts.get(cat) or {}).items()]
        for key, row, from_pack in sorted(rows, key=lambda x: x[0]):
            if from_pack and (key in NEVER or SECRETISH.search(key)):
                continue                     # the pack gets the reader's skip list
            cap = caps.get(key) if cat == "notes" and not from_pack else None
            if cap is not None:
                shared_stems.add(key)
            n = fact_node(cat, key, row, cap)
            if from_pack:
                n.update(store="tempest_pack", source=PACK_LABEL)
            add(**n)

    docs = [(k, d, False) for k, d in documents.items()]
    docs += [(k, d, True) for k, d in pack_docs.items()]
    for name, doc, from_pack in sorted(docs, key=lambda x: x[0]):
        if name in NEVER or name in MACHINE_STATE:
            continue
        if not isinstance(doc, dict):
            continue
        if {"hash", "salt"} <= set(doc):
            continue
        # A build.py summary was scrubbed when it was written, and its name is a
        # folder name ("Secret Game Dev Flowchart"), so the name filter skips it.
        # Project summaries, skills and experience modules: every document build.py owns.
        indexed = (doc.get("indexer") == "spark_sol_build" and not from_pack
                   and bool(REGION_NAME.match(str(doc.get("region") or ""))))
        if not indexed and SECRETISH.search(name):
            continue
        text = doc.get("text") or ""
        if not text and doc.get("pointer"):
            text = "Stored as a pointer to " + str(doc["pointer"])
        add(label=str(doc.get("title") or _human(name)) if indexed else _human(name),
            key=name, group=doc["region"] if indexed else "documents",
            kind=str(doc.get("kind") or "document"),
            excerpt=_excerpt(text or doc.get("summary") or ""),
            summary=_scrub(str(doc.get("summary") or ""))[:240],
            source=PACK_LABEL if from_pack else str(doc.get("source") or ""),
            updated=_day(doc.get("updated_at") or doc.get("updated")),
            size=int(doc.get("bytes") or len(text)),
            text=_scrub(_plain(text or str(doc.get("summary") or ""))),
            **({"store": "tempest_pack"} if from_pack else {}))

    for s in sessions:
        if not isinstance(s, dict):
            continue
        summary = str(s.get("summary") or "")
        date = str(s.get("date") or "")
        add(label="Session " + date if date else "Session", key=date,
            group="sessions", kind="session", excerpt=_excerpt(summary),
            language=s.get("language") or "", updated=date[:10] or None,
            size=len(summary), text=_scrub(summary))

    for cap in captures:
        if cap["stem"] in shared_stems:      # already a notes star
            continue
        add(**capture_node(cap))

    links = _links(nodes)
    present = [r for r in REGIONS if any(n["group"] == r for n in nodes)]
    present += sorted({n["group"] for n in nodes} - set(REGIONS))     # the operator's own categories
    return nodes, links, present


def _links(nodes):
    """A link exists when one star's text names another star.

    The name is a document's title words or a fact's value (five characters or
    more, whole words). Nothing is inferred from shared ordinary words.
    """
    full = {n["id"]: (n["label"] + " " + n["excerpt"]).lower() for n in nodes}
    names = {}
    for n in nodes:
        cands = set()
        if n["kind"] == "fact" and 5 <= len(n["excerpt"]) <= 60:
            cands.add(n["excerpt"].lower())
        if n["group"] == "documents" and len(n["label"]) >= 6:
            cands.add(n["label"].lower())
        names[n["id"]] = [c for c in cands if c.strip()]
    seen, out = set(), []
    for a in nodes:
        for b in nodes:
            if a["id"] == b["id"]:
                continue
            for name in names[b["id"]]:
                if re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", full[a["id"]]):
                    pair = tuple(sorted((a["id"], b["id"])))
                    if pair not in seen:
                        seen.add(pair)
                        out.append({"source": pair[0], "target": pair[1]})
                    break
    return out


def make_graph(nodes, links, present, source, reason=None) -> dict:
    mirror_day = None
    if MIRROR.exists():
        mirror_day = datetime.fromtimestamp(MIRROR.stat().st_mtime,
                                            timezone.utc).date().isoformat()
    return {
        "source": source,
        "reason": reason,
        "read_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mirror_day": mirror_day,
        "regions": present,
        "nodes": nodes,
        "links": links,
    }


def public_graph(graph: dict) -> dict:
    """What the browser may see: every node without its full `text`."""
    public = dict(graph)
    public["nodes"] = [{k: v for k, v in n.items() if k != "text"}
                       for n in graph["nodes"]]
    return public


def write_graph(graph: dict) -> None:
    """Atomic. Full record text never reaches the browser file."""
    body = json.dumps(public_graph(graph), ensure_ascii=True, indent=1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".js.tmp")
    tmp.write_text("// Written by read_memory.py. Do not edit.\n"
                   "const GRAPH = " + body + ";\n", encoding="utf-8")
    os.replace(tmp, OUT)


def write(nodes, links, present, source, reason=None):
    write_graph(make_graph(nodes, links, present, source, reason))


def load(mirror_only: bool = False) -> dict:
    """Read the memory store and the captures, write graph-data.js, and return
    the graph with full `text` on every node (server memory only)."""
    source, reason = "neon", None
    try:
        if mirror_only:
            raise RuntimeError("mirror requested")
        facts, sessions, documents = read_neon()
    except Exception as e:  # driver missing, no URL, network down
        source = "mirror"
        reason = type(e).__name__ + (": " + _scrub(str(e))[:120] if str(e) else "")
        if MIRROR.exists():
            facts, sessions, documents = read_mirror()
        else:
            source, reason = "none", reason + "; mirror missing"
            facts, sessions, documents = {}, [], {}
    try:
        pack = merge_pack(facts, documents, *read_pack())
    except Exception as e:  # a bad pack file never wipes the Flaxeon stars
        pack = ({}, {})
        reason = (reason + "; " if reason else "") + "pack unreadable: " + type(e).__name__
    nodes, links, present = build_graph(facts, sessions, documents,
                                        read_captures(), pack)
    graph = make_graph(nodes, links, present, source, reason)
    write_graph(graph)
    return graph


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mirror-only", action="store_true")
    args = ap.parse_args(argv)

    graph = load(args.mirror_only)
    nodes, links, present = graph["nodes"], graph["links"], graph["regions"]
    source, reason = graph["source"], graph["reason"]
    if source == "none" and not nodes:
        print("SPARK reader: no Neon and no mirror. Sky is empty.")
        return 1
    by = {r: sum(1 for n in nodes if n["group"] == r) for r in present}
    print(f"SPARK reader: source={source} notes={len(nodes)} links={len(links)}")
    print("  " + "  ".join(f"{k}={v}" for k, v in by.items()))
    if reason:
        print("  neon skipped: " + reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
