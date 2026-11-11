# SPARK SOL corpus

Recorded 2026-11-10. Updated the same day: the first page loads the parent F.L.A.X.E.O.N memory database. The markdown allowlist below is a later index. There is no synthetic sample corpus.

## First page source

The parent folder holds the store the Desk already uses.

- Canonical: Neon tables `memory_facts`, `memory_sessions`, `memory_documents`, via `F.L.A.X.E.O.N/memory/neon_store.py`. The reader asks `memory/config_manager.py` for the URL. The URL is not written into this protocol.
- Offline mirror: `F.L.A.X.E.O.N/memory/long_term.json`, used when Neon is unreachable.
- A fact's color is its category. Documents and sessions are their own colors. The eight dyes are the memory-region table in the design spec. The plate shows the key or the document name. A region with no records draws no name.
- `/chat`, `/tts`, and `/hear` are not faked in the page. The first build shows the real sky from this database. A spoken turn waits until `server.py` exists.

The sky indexes **knowledge documents**: understanding-pool modules, master ledgers, and experience modules. It does not index raw source trees, virtualenvs, `node_modules`, or key files. A repository becomes a star when a pool or experience markdown exists for it.

## In the sky now

These folders are the `notes_dir` allowlist. Counts are markdown files kept after the skip rules, seen on this PC on 2026-11-10.

| Root | What it is | Markdown files kept |
|---|---|---|
| `C:\Users\Draven Chen\.cursor\skills\POOL\BOOKS COMPLETE POOL` | Book ledgers | 879 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\SAMPOERNA COMPLETE POOL MODULES` | Sampoerna course pool | 1,266 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\SNHU COMPLETE POOL MODULES` | SNHU course pool | 163 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\SOPHIA COMPLETE POOL` | Sophia course pool | 3,201 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\STUDYCOM COMPLETE POOL` | Study.com course pool | 66 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\WRITING PROSE POOL` | Prose pool | 23 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\MANGA WRITING POOL` | Manga pool | 4 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\Full Stack Dev` | Full-stack modules | 12 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\Game Dev Books` | Game-dev modules | 24 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\Game Engine Guides and Tutorials` | Engine guides | 10 |
| `C:\Users\Draven Chen\.cursor\skills\POOL\EXPERIENCE POOL` | Lived experience | 14 |
| `g:\Draven's Very Important Files\Workspace\F.L.A.X.E.O.N\CRIMSUN_POOL` | FLAXEON decision records and breadcrumbs | 73 |

About **5,700** markdown files stay. The raw scan was about 8,900. Sophia stores the same notes twice, once under `chunks\` and once under `chunk_modules\`. The indexer skips `chunks\`, `_build_snhu\`, and any file whose name contains `api_keys`, `.env`, or `credentials`.

A star's color is the allowlist root, one dye per pool, listed in the design spec. No two pools share a dye. The course is the first directory under that root that is not named `chunk_modules`, and the layout keeps that course as a tight neighborhood inside the pool's region. The plate names the course. Sophia is one sage region. Pre-Calculus is the dense neighborhood inside it, about 1,700 stars, not a separate color. The immediate parent of those files is the folder `chunk_modules`, and using that name as the color would paint unrelated notes the same.

Skill files under `.cursor\skills` and `.claude\skills` are **not** notes. The pool already lives inside `.cursor\skills\POOL`. Scanning the whole skills tree would count the pool twice and would turn procedure files into stars.

## Experience coverage

Compiled experience modules exist for four codebases:

- Excel Workflow
- Merge Cats Defender
- Sunnyside World
- Tiny Swords Last Stand

`JARVIS_FOUNDATIONAL_EXPERIENCE.md` inside the FLAXEON CrimSun folder is archaeology for F.L.A.X.E.O.N. The experience indexer cannot see it until it is recompiled into the standard entry shape.

## Not in the sky yet

GitHub account **crimSun-dev** has **54** repositories. **K-nity** has **3**. The Workspace directory on this PC has many more local trees (games, engines, course checkouts, tools) that are not all on that account.

A repo joins the sky when one of these exists:

1. An understanding module compiled from its real docs, or
2. An experience module from archaeology or from a breadcrumb log

Until then the repo is a backlog row, not a star. Cloning all 54 into `notes/` would put source, locks, and secrets in the graph. That is refused.

Course checkouts that already have a complete pool (SNHU, Sophia, Sampoerna, Study.com) are in the table above. A separate "file subscriptions" library was not found on this machine. Those course pools are the subscribed material the sky can already read. Uncompiled downloads, including a local Coursera folder, stay out until a pool module exists.

## First index, when the server exists

`config.json` `notes_dir` is this allowlist, not a single `./notes` folder and not the whole PC. Captures from "remember that" still land in this protocol's own `notes/captures/` and become stars through `commit_note()`. They do not write into the pool sources.

The first `/chat` proof uses a question against a real ledger title, and the note count on screen is the allowlist count.
