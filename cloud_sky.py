"""Flaxeon's memory to Firestore, so the GitHub Pages viewer works while the PC is off.

Run by the scheduled GitHub Action after cloud_github.py. Reads Neon (read-only), builds
the sky with read_memory.py's own build_graph, and writes it to Firestore in the
`flaxeon` project as `spark_sky/meta` plus chunk documents (a document holds at most
1 MiB; the sky is about 10 MB). Only the operator's Google account can read them
(firebase/firestore.rules). The web viewer joins the chunks, searches them and asks.

Writes are generation-safe: the chunks of a new sky are written under a new id first,
then `meta` points at them, then the old chunks go. A run whose sky did not change
writes nothing.

    NEON_URL=...  FIREBASE_SERVICE_ACCOUNT='{...json...}'  python cloud_sky.py [--dry-run]
    (FIREBASE_SERVICE_ACCOUNT_FILE=path works too, for a run on the PC.)

Not included, by design: notes/captures (the PC's markdown files are their only copy and
stay off every remote) and the Tempest pack store (a file on the PC).
The log is counts only: the repo is public, and so are its Action logs.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import read_memory  # noqa: E402

COLLECTION = "spark_sky"
CHUNK = 900_000                 # characters; the JSON is ASCII, so bytes too. Firestore's cap is 1 MiB.


def _iso(ts):
    return ts.isoformat() if hasattr(ts, "isoformat") else (str(ts) if ts else None)


def _payload(raw):
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return None


def read_neon(url: str):
    """(facts, sessions, documents) with the queries NeonStore runs."""
    import psycopg
    # autocommit: read-only, so there is no COMMIT at the end for a dropped connection to fail
    with psycopg.connect(url, connect_timeout=15, autocommit=True) as con, con.cursor() as cur:
        cur.execute("SELECT category, key, value, updated_at FROM memory_facts")
        facts = {}
        for cat, key, value, ts in cur.fetchall():
            facts.setdefault(cat, {})[key] = {"value": value, "updated_at": _iso(ts)}
        cur.execute("SELECT id, recorded_on, summary, language FROM memory_sessions "
                    "ORDER BY id DESC LIMIT 500")
        sessions = [{"date": str(r[1]), "summary": r[2], "language": r[3] or ""}
                    for r in reversed(cur.fetchall())]
        cur.execute("SELECT name, payload FROM memory_documents")
        documents = {name: _payload(p) for name, p in cur.fetchall()}
    return facts, sessions, documents


def sky(facts, sessions, documents) -> tuple[str, str, dict]:
    """(body, generation, meta). The generation hashes the sky without its read time,
    so an unchanged memory gives the same generation."""
    nodes, links, present = read_memory.build_graph(facts, sessions, documents)
    graph = read_memory.make_graph(nodes, links, present, "neon")
    graph["mirror_day"] = None
    body = json.dumps(graph, ensure_ascii=True)
    stable = json.dumps({k: v for k, v in graph.items() if k != "read_at"}, ensure_ascii=True)
    gen = hashlib.sha256(stable.encode("ascii")).hexdigest()[:16]
    meta = {"gen": gen, "read_at": graph["read_at"], "notes": len(nodes), "links": len(links),
            "chunks": -(-len(body) // CHUNK)}
    return body, gen, meta


def firestore_client():
    import firebase_admin
    from firebase_admin import credentials, firestore
    raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
    path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_FILE", "")
    info = json.loads(raw) if raw else json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        app = firebase_admin.get_app()
    except ValueError:
        app = firebase_admin.initialize_app(credentials.Certificate(info))
    return firestore.client(app)


def push(db, body: str, gen: str, meta: dict) -> str:
    col = db.collection(COLLECTION)
    old = (col.document("meta").get().to_dict() or {})
    if old.get("gen") == gen and old.get("chunks") == meta["chunks"]:
        return "unchanged"
    for i in range(meta["chunks"]):
        col.document(f"{gen}_{i:03d}").set({"data": body[i * CHUNK:(i + 1) * CHUNK]})
    col.document("meta").set(meta)
    stale = 0
    for snap in col.list_documents():
        if snap.id != "meta" and not snap.id.startswith(gen + "_"):
            snap.delete()
            stale += 1
    return f"written ({meta['chunks']} chunks, {stale} old removed)"


def main(argv=None) -> int:
    dry = "--dry-run" in (argv if argv is not None else sys.argv[1:])
    url = os.environ.get("NEON_URL", "")
    has_fb = bool(os.environ.get("FIREBASE_SERVICE_ACCOUNT") or os.environ.get("FIREBASE_SERVICE_ACCOUNT_FILE"))
    if not url or (not dry and not has_fb):
        print("cloud sky: NEON_URL or FIREBASE_SERVICE_ACCOUNT is not set; nothing to do.")
        return 0
    try:
        body, gen, meta = sky(*read_neon(url))
    except Exception as e:
        print("cloud sky: Neon read failed:", type(e).__name__)      # never the message: it may hold the host
        return 1
    print(f"cloud sky: notes={meta['notes']} links={meta['links']} bytes={len(body)} chunks={meta['chunks']}")
    if dry:
        return 0
    try:
        print("cloud sky: firestore", push(firestore_client(), body, gen, meta))
    except Exception as e:
        print("cloud sky: Firestore write failed:", type(e).__name__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
