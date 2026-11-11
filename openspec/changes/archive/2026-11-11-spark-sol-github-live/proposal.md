## Why

The indexer brings every repo into Flaxeon's memory, but only when someone runs it with the passkey. A repo created or pushed afterwards stays unknown until the next hand-started run. The operator wants Flaxeon to follow GitHub live.

## What Changes

- The SPARK SOL server checks GitHub every 10 minutes (`--github-watch`, 0 turns it off). Each check is one small `gh` listing of the repos, with their last-push times, for the signed-in account and its organisations.
- When a repo is added, removed or pushed since the last indexed state, the server runs `build.py`. The run publishes through the passkey gate and reloads the sky, and the open page and the web viewer follow within a minute.
- The first check on a machine records a baseline and runs nothing. A failed run leaves the old state in place, so the next check tries again. A check that cannot reach GitHub is logged and changes nothing.
- The passkey for these runs is stored once, encrypted with Windows DPAPI for the operator's user account, in `cache/passkey.dpapi`, which git ignores. It is decrypted only into one indexer run's environment, and never printed or logged. Without the store, the watch reports "publish pending" and publishes nothing.
- `build.py` takes a lock, so a watch run and a hand-started run never write the index at the same time.
- `/health` reports the watch: repo count, time of the last check, whether a run is in progress, and the last result. The log is in `cache/github_watch.log`.

## Capabilities

### New Capabilities

- `github-live`: Flaxeon's memory and the galaxy follow the operator's GitHub without a hand-started run.

### Modified Capabilities

- None.

## Impact

- `server.py` (watch thread, health), `passkey_store.py` (DPAPI read), `build.py` (lock).
- One `gh` listing every 10 minutes. A full incremental index (about 5 minutes) runs only after a change.
