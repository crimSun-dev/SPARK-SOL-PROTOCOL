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

### 4. Cause of the 2026-11-11 publish gap, and the fix

Cause, found in task 4.1:
- Flaxeon gates Neon and Firebase behind the operator passkey. In a fresh process, `core.passkey.cloud_allowed()` is false until the passkey is unlocked or `FLAXEON_PASSKEY` is set.
- While the gate is closed, `memory_manager._backends()` returns `(None, None)`. So `save_document` and `forget_document` skip both stores and queue nothing. `memory/.pending_sync.json` did not exist.
- `build.py` runs as its own process, so all 210 writes were dropped without an error.
- The local cache got only one document. `save_document` puts a payload into the cache dict only when `_write_cache` is true, and `build.py` set that flag on the last item only (`ws_writing_prose`, last by key).
- The five-name read-back went through `load_document` and was never checked against Neon.

Fix, all in `build.py`:
- `publish` refuses to start when `cloud_allowed()` is false. It names the two ways to open the gate (unlock in Flaxeon, or `FLAXEON_PASSKEY` in the environment of that one run) and exits non-zero.
- It never opens Neon around the gate.
- It puts every payload into the local cache itself.
- After writing, it counts the `repo_index` documents tagged `spark_sol_build` in Neon and compares that count with the number saved, counting any writes queued as pending separately.

A run that did not read GitHub, because of `--no-github` or because `gh` failed, keeps the summaries of GitHub-only repos (`gh_*`). A repo that was not seen in this run is not treated as gone. A `--no-github` run now says that it skipped GitHub.

Verified 2026-11-11 with the passkey:
- A full run published 212 summaries; all 212 were counted in Neon.
- All 32 facts and 14 other documents were unchanged.
- A throwaway project was published (213), then forgotten after its folder was deleted (212).

Alternative considered: writing through `NeonStore` directly, as `read_memory.py` does for reads. Rejected, because it would bypass the operator's passkey for writes.

## Risks / Trade-offs

- [Publishing needs the operator's passkey in that process] → The run is operator-started, and the passkey goes in that run's environment only. It is never written to a file or a log.
- [Summaries quote READMEs] → They are scrubbed, capped at 1,600 characters of README, and stay inside the operator's own Neon. A public repo's README is public anyway. A private repo's README stays in the operator's store.
- [The index is about 5 GB] → It stays local and ignored by git. Pruned folders and size caps keep it from growing with dependencies.
- [Projects on the sky change the chart] → About 210 new stars in four regions. The galaxy already lays out regions, and the gesture rules treat a reload with more than one new star as playing nothing.

## Open Questions

None that change what gets built. Extra roots, such as Documents and Desktop, are a separate change if the operator wants them.
