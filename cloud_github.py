"""GitHub to Flaxeon's memory, run by a scheduled GitHub Action while the PC is off.

Writes only what the PC's indexer would write for repos that are NOT cloned on
the PC: one `repo_index` document per repo (key `gh_<owner_repo>`), built with
build.py's own summary code so the two never rewrite each other. Repos cloned
on the PC have richer summaries from their files; those stay the PC's job.

    NEON_URL=...  GH_READ_TOKENS="tok1 tok2"  GH_OWNERS="K-nity"  python cloud_github.py [--dry-run]

Deletes only what GitHub confirms: a repo missing from a listing with no token
failure, whose exact name now answers 404 (or redirects after a rename), and,
for a private repo, only when the listing proved the token sees private repos.
A token that cannot see private repos therefore never makes them look deleted.

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
COUNTS = re.compile(r", (\w+) issues, (\w+) pull requests$", re.M)
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
            m = re.search(r"HTTP \d{3}[^(\n]*", str(e))    # the status, never the URL (it can name a repo)
            print(f"token {failed}: listing failed ({type(e).__name__}"
                  + (f", {m.group(0).strip()}" if m else "") + ")", file=sys.stderr)
        finally:
            if tok:
                if saved is None:
                    os.environ.pop("GH_TOKEN", None)
                else:
                    os.environ["GH_TOKEN"] = saved
    return list(repos.values()), owners, failed


def repo_status(nwo: str, tokens: list[str]) -> str:
    """'gone' when every token gets 404 for that exact repo; the new full name when
    GitHub redirects a rename; 'exists' or 'unknown' otherwise."""
    import subprocess
    answers = []
    for tok in tokens or [None]:
        env = {**os.environ, **({"GH_TOKEN": tok} if tok else {})}
        p = subprocess.run(["gh", "api", f"repos/{nwo}", "--jq", ".full_name"], env=env,
                           capture_output=True, text=True, timeout=60)
        if p.returncode == 0 and p.stdout.strip():
            name = p.stdout.strip()
            return name if name.lower() != nwo.lower() else "exists"
        answers.append("404" if "HTTP 404" in (p.stderr or "") else "other")
    return "gone" if answers and all(a == "404" for a in answers) else "unknown"


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

        # A repo whose README this token cannot read keeps the PC's document (when there is one):
        # a thinner summary would be rewritten back by the PC on its next run.
        unknown = {r["nameWithOwner"] for r in repos if r.get("readme_unknown")}
        prj = build.Projects()
        build.attach_github(prj, [r for r in repos if r["nameWithOwner"] not in cloned], False, lambda s: None)
        kept = 0
        for key in [k for k, p in prj.by_key.items() if p["title"] in unknown and k in mine]:
            del prj.by_key[key]
            kept += 1
        for p in prj.by_key.values():                # a token without Issues/Pull requests read sees no counts:
            gh = p["github"]                         # keep the counts Neon already has, never write "None"
            old = COUNTS.search(str((mine.get(p["key"]) or {}).get("text") or ""))
            if old and gh.get("issues") is None and gh.get("pull_requests") is None:
                gh["issues"], gh["pull_requests"] = (int(x) if x.isdigit() else None for x in old.groups())
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
            # Deleted and renamed repos. A summary goes only when GitHub confirms it: the
            # listing had no token failure, the owner was listed, a private repo's owner was
            # listed with private repos visible, and that exact repo now answers 404 (or
            # redirects to a new name, which the listing above has already written).
            listed = {r["nameWithOwner"].lower() for r in repos}
            private_owners = {r["nameWithOwner"].split("/")[0].lower() for r in repos if r.get("isPrivate")}
            deleted = renamed = unconfirmed = 0
            for key, d in sorted(mine.items()):
                nwo = str(d.get("title") or "")
                if failed or not key.startswith("gh_") or key in want or "/" not in nwo or nwo.lower() in listed:
                    continue
                owner = nwo.split("/")[0].lower()
                was_private = "(private" in str(d.get("text") or "")
                if owner not in owners or (was_private and owner not in private_owners):
                    unconfirmed += 1
                    continue
                status = repo_status(nwo, tokens)
                if status in ("exists", "unknown"):
                    unconfirmed += 1
                    continue
                deleted += status == "gone"
                renamed += status != "gone"
                if not dry:
                    cur.execute("DELETE FROM memory_documents WHERE name = %s", (key,))
        if not dry:
            con.commit()
    print(("DRY RUN: " if dry else "") + json.dumps({
        "repos_listed": len(repos), "owners": len(owners), "token_failures": failed,
        "cloned_on_pc": len(cloned & {r["nameWithOwner"] for r in repos}), "github_only": len(want),
        "written": written, "unchanged": unchanged, "kept_readme_unreadable": kept,
        "deleted": deleted, "renamed": renamed, "not_confirmed": unconfirmed}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
