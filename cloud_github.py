"""GitHub to Flaxeon's memory, run by a scheduled GitHub Action while the PC is off.

Writes only what the PC's indexer would write for repos that are NOT cloned on
the PC: one `repo_index` document per repo (key `gh_<owner_repo>`), built with
build.py's own summary code so the two never rewrite each other. Repos cloned
on the PC have richer summaries from their files; those stay the PC's job.

    NEON_URL=...  GH_READ_TOKENS="tok1 tok2"  GH_OWNERS="K-nity"  python cloud_github.py [--dry-run]

It never deletes. A token that cannot see private repos would make every
private repo look deleted, so removing a gone repo's summary stays with the PC's
indexer, which lists through the operator's own GitHub sign-in.

Without GH_READ_TOKENS it uses the gh CLI's own sign-in (for a local test).
The log is counts only: the repo is public, and so are its Action logs.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402

DOCUMENT_TEXT_MAX = 48 * 1024          # Flaxeon's cap; over it, a pointer instead of text
GITHUB_LINE = re.compile(r"^GitHub: (\S+) \(", re.M)
OWNERS = tuple(os.environ.get("GH_OWNERS", "").split())   # organisations to list by name (e.g. K-nity)


def payload_for(p: dict) -> dict:
    """The same fields Flaxeon's build_payload gives the PC's run, in the same order."""
    text = build.summary_text(p)
    out = {"kind": "repo_index", "source": p["path"], "summary": build.summary_line(p),
           "updated": datetime.now(timezone.utc).isoformat()}
    if len(text.encode("utf-8")) > DOCUMENT_TEXT_MAX:
        out.update(pointer=p["path"], bytes=len(text.encode("utf-8")))
    else:
        out["text"] = text
    out.update(region=p["region"], title=p["title"], indexer="spark_sol_build")
    return out


def same(a: dict, b) -> bool:
    return isinstance(b, dict) and {k: v for k, v in a.items() if k != "updated"} == \
        {k: v for k, v in b.items() if k != "updated"}


def list_repos(tokens: list[str]) -> tuple[list[dict], set[str], int]:
    """Every repo each token can list, the owners listed in full, and failures."""
    repos, owners, failed = {}, set(), 0
    for tok in tokens or [None]:
        saved = os.environ.get("GH_TOKEN")
        if tok:
            os.environ["GH_TOKEN"] = tok
        try:
            for r in build.github_repos(lambda s: None, OWNERS):
                repos[r["nameWithOwner"]] = r
                owners.add(r["nameWithOwner"].split("/")[0].lower())
        except Exception as e:                    # the type only: the message can name a private repo
            failed += 1
            print(f"token {failed}: listing failed ({type(e).__name__})", file=sys.stderr)
        finally:
            if tok:
                if saved is None:
                    os.environ.pop("GH_TOKEN", None)
                else:
                    os.environ["GH_TOKEN"] = saved
    return list(repos.values()), owners, failed


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    dry = "--dry-run" in argv
    dsn = os.environ.get("NEON_URL", "")
    tokens = os.environ.get("GH_READ_TOKENS", "").split()
    if not dsn:
        print("NEON_URL is not set; nothing to do.")
        return 0
    repos, owners, failed = list_repos(tokens)
    if not repos:
        print(f"no repos listed ({failed} token failures); nothing changed.")
        return 1 if failed else 0

    import psycopg
    with psycopg.connect(dsn, connect_timeout=15) as con:
        with con.cursor() as cur:
            cur.execute("SELECT name, payload FROM memory_documents")
            docs = {n: (p if isinstance(p, dict) else json.loads(p)) for n, p in cur.fetchall()}
        mine = {n: d for n, d in docs.items() if isinstance(d, dict) and d.get("indexer") == "spark_sol_build"}
        cloned = {m.group(1) for n, d in mine.items() if not n.startswith("gh_")
                  for m in [GITHUB_LINE.search(str(d.get("text") or ""))] if m}

        prj = build.Projects()
        build.attach_github(prj, [r for r in repos if r["nameWithOwner"] not in cloned], False, lambda s: None)
        want = {p["key"]: payload_for(p) for p in prj.by_key.values()}

        written = unchanged = 0
        with con.cursor() as cur:
            for key, payload in sorted(want.items()):
                if same(payload, mine.get(key)):
                    unchanged += 1
                    continue
                written += 1
                if not dry:
                    cur.execute("INSERT INTO memory_documents (name, payload, updated_at) VALUES (%s, %s, %s) "
                                "ON CONFLICT (name) DO UPDATE SET payload = EXCLUDED.payload, "
                                "updated_at = EXCLUDED.updated_at",
                                (key, json.dumps(payload, ensure_ascii=False), datetime.now(timezone.utc)))
        if not dry:
            con.commit()
    print(("DRY RUN: " if dry else "") + json.dumps({
        "repos_listed": len(repos), "owners": len(owners), "token_failures": failed,
        "cloned_on_pc": len(cloned & {r["nameWithOwner"] for r in repos}), "github_only": len(want),
        "written": written, "unchanged": unchanged}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
