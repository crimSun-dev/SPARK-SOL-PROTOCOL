## Why

`build.py` already indexes the whole Workspace, the CrimSun pools, the skills folders and the operator's GitHub repos, and publishes one summary per project to Flaxeon's shared memory. It was written without a change record. The Flaxeon changes it touches say the opposite: `flaxeon-corpus-ingest` and `flaxeon-memory-manage` refuse whole-repo and POOL ingest into Neon, and `flaxeon-spark-sol-link` says the galaxy does not crawl GitHub, repos, courses, games or pool modules. This change puts the indexer on the record as SPARK SOL's own capability, and says where it stops, so the two rule sets agree.

It also records a gap found on 2026-11-11. The local index lists 210 published summaries, but Neon holds no `repo_index` documents and Flaxeon's local cache holds one. So the Workspace, Pools, Experience and Skills regions never reach the sky.

## What Changes

- A local full-text index at `index/workspace.sqlite` covers four roots: the Workspace folder that contains F.L.A.X.E.O.N, `~/.cursor/skills/POOL` (pools and experience modules), `~/.cursor/skills`, and `~/.claude/skills`. It holds full text, split into chunks, on this machine only. It is never committed and never uploaded.
- GitHub repos owned by the operator and their organisations are read through the `gh` CLI: metadata and the README. A repo that is cloned locally joins its local project. A repo that is not cloned becomes a project of its own.
- Files: secret files are skipped by name, and not even the name is stored. Secret-shaped strings inside any other file are scrubbed before storage. Dependency, VCS and build folders and the pool's duplicate `chunks` folders are pruned. Oversized text, generated files and binaries are stored by name and path only. PDF, Word, PowerPoint and Excel files are stored as extracted text. Re-runs are incremental by size and modification time, and files that are gone leave the index.
- Flaxeon's shared memory gets exactly one short `repo_index` document per project, written through Flaxeon's own `save_document`. Never the full text. Summaries this indexer published earlier and no longer has are forgotten. No other document or fact is touched.
- The galaxy draws each summary as a star in the Workspace, Pools, Experience or Skills region. SPARK SOL's `/chat` searches the local index for detail.
- A run ends by asking the galaxy to reload, if it is running.
- The publish step reports what actually reached Neon. The 2026-11-11 gap is diagnosed and fixed.

This change does not add the PC's Documents, Desktop, Downloads or any other folder outside the four roots. It does not put full text in Neon, add embeddings, or run on a schedule. It does not change Flaxeon's `ingest_memory` limits: those govern what the operator hands Flaxeon. This indexer is SPARK SOL's own, and it writes summaries only.

## Capabilities

### New Capabilities

- `workspace-index`: SPARK SOL keeps a local full-text index of the Workspace, pools, skills and GitHub repos. It publishes one scrubbed summary per project to Flaxeon's shared memory, and the galaxy draws those summaries as stars.

### Modified Capabilities

- None.

## Impact

- **Code**: `build.py`, the summary branch in `read_memory.py`, and `search_index` in `server.py` already exist. The fix for the publish gap lands in `build.py`, or in the Flaxeon `memory_manager` path it calls, once diagnosed.
- **Data**: `index/` (about 5 GB on 2026-11-11, 405,084 files, 210 projects) stays local and is ignored by git. Neon gains about 210 small `repo_index` documents.
- **Network**: `api.github.com` through `gh`, and Flaxeon's Neon (and Firebase if configured) for summaries only.
