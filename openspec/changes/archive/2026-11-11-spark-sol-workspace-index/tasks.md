## 1. Roots and secrets

- [x] 1.1 Confirm `build.py` reads only the four roots. Verify with `python build.py --dry-run` that every listed project path lies under the Workspace, `~/.cursor/skills` or `~/.claude/skills`, and that no path is under the PC's Documents, Desktop or Downloads.
- [x] 1.2 Confirm that secret files never enter the index. Verify that a query of `files` for `.env`, `api_keys.json`, `*.pem`, `credentials.json` and `service-account*.json` returns no rows.
- [x] 1.3 Confirm that secret-shaped strings are scrubbed. Verify that an FTS search of `chunks` for `sk-`, `ghp_`, `AIza`, `postgres://` and `BEGIN PRIVATE KEY` returns only removal markers.

## 2. Pruning and re-runs

- [x] 2.1 Confirm pruning. Verify that `files` holds no path containing `node_modules`, `.git`, `venv`, `__pycache__` or a pool `chunks` folder.
- [x] 2.2 Confirm incremental re-runs. Run `python build.py --no-publish --no-github` twice, and verify that the second run reports every file unchanged and writes none.
- [x] 2.3 Confirm removal. Delete a scratch file under the Workspace, re-run, and verify that it is gone from `files` and `chunks`.

## 3. GitHub

- [x] 3.1 Confirm that cloned repos join their local project and uncloned repos stand alone. Verify that `crimSun-dev/SPARK-SOL-PROTOCOL` maps to its local project, and that a repo with no clone appears as a `gh_` project with its README searchable.
- [x] 3.2 Confirm that a run without GitHub access continues. Verify that `--no-github` (and a run with `gh` signed out) finishes and names the skip.

## 4. Publish to shared memory

- [x] 4.1 Find why the 210 names in `meta.published` are not in Neon: check Flaxeon's pending queue, the Neon `documents` table, and any later forget or sync. Record the cause in this change's design.md before changing code.
- [x] 4.2 Fix the cause. Make `publish` count the `repo_index` documents tagged `spark_sol_build` in Neon after writing, report saved, queued, forgotten and read-back from Neon, and exit non-zero when they disagree. Verify with a full run that Neon holds one `repo_index` document per project.
- [x] 4.3 Confirm that the indexer forgets only its own summaries. Verify that facts and non-indexer documents in Neon are identical before and after a run, and that a removed project's summary is forgotten.

## 5. The galaxy

- [x] 5.1 Confirm that the summaries become stars. With the galaxy running, verify after a full run that `/graph` lists nodes in the workspace, pools, experience and skills regions, and that their count matches Neon.
- [x] 5.2 Confirm that `/chat` answers from the index. Ask about a file that exists only in the Workspace, and verify that the answer cites that project.
- [x] 5.3 Confirm the read-only web viewer. Verify that https://crimsun-dev.github.io/SPARK-SOL-PROTOCOL/ shows the new regions within one watch interval, and that no summary text is in the published site.
