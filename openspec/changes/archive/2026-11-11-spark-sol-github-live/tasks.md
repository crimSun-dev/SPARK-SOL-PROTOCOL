## 1. Passkey and lock

- [x] 1.1 Store the passkey with DPAPI in `cache/passkey.dpapi` and read it with `passkey_store.load()`. Verified with `python passkey_store.py --check`: the store decrypts and unlocks Flaxeon, the value is never printed, and git ignores the file.
- [x] 1.2 Make `build.py` take a lock on the index. Verify that a second run started during a first one exits with code 3 and says another run is writing.

## 2. Watch

- [x] 2.1 Add the server's GitHub watch: a baseline first, an index run on a change, saving the seen state only after success, and logging failures. Verified with stubbed checks (5/5): a baseline only on the first check, a new repo triggers a run, a failed run is retried, and an offline check is logged.
- [x] 2.2 Real run. Remove one repo from `cache/github_seen.json` and restart the server. Verify that the watch notices the "new" repo, runs the indexer with the stored passkey, reaches exit 0 with every document counted in Neon, and writes the new seen state, and that `/health` reports the result.
