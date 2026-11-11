## Why

The GitHub watch runs on the operator's PC. While the PC is off, a new or changed repo waits. The operator wants Flaxeon's memory to follow GitHub even then.

## What Changes

- A scheduled GitHub Action, `github-to-memory`, runs every 30 minutes, and can also be started by hand.
- It runs `cloud_github.py`, which lists every repo the read-only tokens can see and writes one `repo_index` summary per repo that is not cloned on the PC (`gh_<owner_repo>`).
  - It uses `build.py`'s own summary code, so a document from the cloud and one from the PC are identical, and neither side rewrites the other's work.
  - It deletes a `gh_` summary only when its owner's repos were listed in full and the repo no longer exists.
- Repos cloned on the PC keep their file-based summaries. Updating those stays the PC's job.
- Secrets live in the repo's encrypted Actions secrets:
  - `NEON_URL`: Flaxeon's Neon connection string.
  - `GH_READ_TOKENS`: one or more read-only, fine-grained tokens that the operator creates.
- The passkey is not stored in the cloud. It is Flaxeon's gate on the PC, and the Action holds its own credential to Neon.
- The Action logs counts only, because the repo and its logs are public.

## Capabilities

### New Capabilities

- `github-cloud`: Flaxeon's memory follows GitHub-only repos while the PC is off.

### Modified Capabilities

- None.

## Impact

- `cloud_github.py`, `.github/workflows/github-to-memory.yml`.
- Neon credentials are stored in GitHub secrets, by the operator's choice. Revoking means rotating the Neon password and deleting the secret.
