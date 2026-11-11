## Context

See proposal.md for why. The indexer is `build.py`. It writes `index/workspace.sqlite`, which has five tables:
- `files`: path, project, size, mtime and a note
- `projects`: the per-project summary
- `chunks`: an FTS5 table of 1,500-character chunks
- `chunk_rows`: links each file to its chunks
- `meta`: holds the list of published names

It publishes through Flaxeon's `memory_manager.save_document` with a payload from `tools/memory_ingest.build_payload`, tagged `kind: repo_index`, `indexer: spark_sol_build` and a region. `read_memory.py` draws those as stars. `server.py`'s `search_index` reads the FTS table read-only during `/chat`.

On 2026-11-11 the index held 405,084 files and 210 projects (128 workspace, 66 pools, 14 experience, 2 skills), and `meta.published` listed 210 names. Neon held 14 documents, none of kind `repo_index`. Flaxeon's local cache held one (`ws_writing_prose`).

## Goals / Non-Goals

**Goals:**

- Record the indexer's current behaviour as a spec, and check each part against the running code.
- Make the publish report true: saved, forgotten and read back, all counted against Neon.
- Get the 210 summaries into Neon and onto the sky.

**Non-Goals:**

- New roots, such as the PC's Documents or Desktop.
- A schedule, a file watcher, embeddings, or full text in Neon.
- Any change to Flaxeon's `ingest_memory` limits.

## Decisions

### 1. SPARK SOL owns the indexer; Flaxeon's ingest limits stay as they are

Flaxeon's corpus-ingest rules govern what the operator hands Flaxeon in a conversation, and they refuse whole-repo drops because the full text would land in Neon. This indexer keeps the full text local and writes only one scrubbed summary per project. So it lives in SPARK SOL's own specs, not as a change to Flaxeon's `corpus-ingest`.

Alternative considered: amending `corpus-ingest` in the Flaxeon repo. Rejected, because that would loosen the operator-facing tool's limits to cover a batch job that never sends full text.

### 2. One project, one summary, one star

A git repo is one project. A plain folder under the Workspace is one project, and a course folder splits by module. A pool course is one project, as is each experience module. Each skills root is one project. A GitHub repo joins its local clone by remote URL, or stands alone.

Alternative considered: one star per file. Rejected, because 405,084 stars is not a chart.

### 3. The publish report counts what Neon holds

The current read-back samples five names through `load_document`, which can be satisfied by the local cache. The fix counts `repo_index` documents tagged `spark_sol_build` in Neon after writing, and fails the run loudly when that count differs from the number saved. When Neon is unavailable, writes queue as pending in Flaxeon's existing way, and the report says "queued", not "saved".

## Risks / Trade-offs

- [The publish gap's cause is unknown] → Task 4.1 diagnoses it before anything is changed. Candidates: the writes went to Flaxeon's pending queue and were never flushed; a later Flaxeon sync rewrote the cache; or a forget pass removed them.
- [Summaries quote READMEs] → They are scrubbed, capped at 1,600 characters of README, and stay inside the operator's own Neon. A public repo's README is public anyway. A private repo's README stays in the operator's store.
- [The index is about 5 GB] → It stays local and ignored by git. Pruned folders and size caps keep it from growing with dependencies.
- [Projects on the sky change the chart] → About 210 new stars in four regions. The galaxy already lays out regions, and the gesture rules treat a reload with more than one new star as playing nothing.

## Open Questions

None that change what gets built. Extra roots, such as Documents and Desktop, are a separate change if the operator wants them.
