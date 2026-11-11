"""What the operator has fed Flaxeon to index, and the category each thing goes in.

`feeds.json` (beside this file, git-ignored: it holds local paths) is the registry
build.py reads on every run:

    {"feeds": [{"path": "G:/Games/Ember", "category": "games", "title": "Ember",
                "added": "2026-11-11"}],
     "categories": {"G:/.../Workspace/Secret Game": "games"}}

- A feed is a file or folder that becomes its own star, wherever it lives. Outside
  build.py's roots it is a root of its own; inside one (the Workspace, the pools,
  the skills) it is split out of the project that would have held it.
- A category entry moves an existing project, by its path, to another region of the
  sky without making it a feed.
- A category is any short name: the built-in regions (workspace, pools, experience,
  skills) or a new one ("games", "music"); a new one becomes a new region of the sky.

Standard library only. Flaxeon's spark_protocol tool writes this file; so can:

    python feeds.py list
    python feeds.py add "G:/Games/Ember" --category games [--title Ember]
    python feeds.py categorize "G:/.../Workspace/Secret Game" games
    python feeds.py remove "G:/Games/Ember"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILE = HERE / "feeds.json"
BUILT_IN = ("workspace", "pools", "experience", "skills")
_CAT = re.compile(r"[^a-z0-9]+")


class FeedError(ValueError):
    pass


def category(name: str) -> str:
    """'Board Games' -> 'board-games'. Refuses an empty or over-long name."""
    c = _CAT.sub("-", str(name or "").strip().lower()).strip("-")
    if not c or len(c) > 24:
        raise FeedError("a category is 1 to 24 letters, digits or dashes")
    return c


def norm(path) -> str:
    """One spelling per place: absolute, forward slashes, no trailing slash."""
    p = Path(os.path.expandvars(os.path.expanduser(str(path)))).resolve()
    return p.as_posix().rstrip("/")


def _key(path: str) -> str:
    return path.lower() if os.name == "nt" else path


def load(file: Path | None = None) -> dict:
    file = file or FILE
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    feeds = [f for f in data.get("feeds") or [] if isinstance(f, dict) and f.get("path")]
    cats = {k: v for k, v in (data.get("categories") or {}).items() if isinstance(v, str)}
    return {"feeds": feeds, "categories": cats}


def save(data: dict, file: Path | None = None) -> None:
    file = file or FILE
    tmp = file.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, file)


def add_feed(path, cat: str, title: str | None = None, file: Path | None = None) -> dict:
    p = norm(path)
    if not Path(p).exists():
        raise FeedError(f"nothing at {p}")
    entry = {"path": p, "category": category(cat), "title": (title or "").strip() or Path(p).stem,
             "added": date.today().isoformat()}
    data = load(file)
    data["feeds"] = [f for f in data["feeds"] if _key(norm(f["path"])) != _key(p)] + [entry]
    data["categories"].pop(next((k for k in data["categories"] if _key(norm(k)) == _key(p)), ""), None)
    save(data, file)
    return entry


def set_category(path, cat: str, file: Path | None = None) -> dict:
    """A feed keeps its entry and changes category; anything else gets a category entry."""
    p, c = norm(path), category(cat)
    data = load(file)
    for f in data["feeds"]:
        if _key(norm(f["path"])) == _key(p):
            f["category"] = c
            save(data, file)
            return {"path": p, "category": c, "feed": True}
    data["categories"] = {k: v for k, v in data["categories"].items() if _key(norm(k)) != _key(p)}
    data["categories"][p] = c
    save(data, file)
    return {"path": p, "category": c, "feed": False}


def remove(path, file: Path | None = None) -> bool:
    p = _key(norm(path))
    data = load(file)
    n = len(data["feeds"]) + len(data["categories"])
    data["feeds"] = [f for f in data["feeds"] if _key(norm(f["path"])) != p]
    data["categories"] = {k: v for k, v in data["categories"].items() if _key(norm(k)) != p}
    save(data, file)
    return len(data["feeds"]) + len(data["categories"]) < n


def categories(file: Path | None = None) -> list[str]:
    """The built-in regions, then every category the registry uses."""
    data = load(file)
    used = [f["category"] for f in data["feeds"]] + list(data["categories"].values())
    return list(BUILT_IN) + sorted(set(used) - set(BUILT_IN))


def override_for(project_path, data: dict) -> str | None:
    """The category entry for exactly this project path, if there is one."""
    p = _key(norm(project_path))
    for k, v in data["categories"].items():
        if _key(norm(k)) == p:
            return v
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    a = sub.add_parser("add"); a.add_argument("path"); a.add_argument("--category", required=True)
    a.add_argument("--title")
    c = sub.add_parser("categorize"); c.add_argument("path"); c.add_argument("category")
    r = sub.add_parser("remove"); r.add_argument("path")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "list":
            data = load()
            for f in data["feeds"]:
                print(f"feed  [{f['category']}] {f['title']}  {f['path']}")
            for k, v in data["categories"].items():
                print(f"move  [{v}] {k}")
            print("categories:", ", ".join(categories()))
        elif args.cmd == "add":
            print(json.dumps(add_feed(args.path, args.category, args.title)))
        elif args.cmd == "categorize":
            print(json.dumps(set_category(args.path, args.category)))
        else:
            print("removed" if remove(args.path) else "not in the registry")
    except FeedError as e:
        print("feeds:", e)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
