## 1. Job

- [x] 1.1 Write `cloud_github.py` with the PC's document code, cloned-repo detection, compare-before-write, and owner-scoped deletes. Verified with a dry run against Neon: 60 repos, 36 cloned, 23 of 24 unchanged; the 1 write is a real pull-request count change; 0 deletes.
- [x] 1.2 Add the scheduled workflow, and set the `NEON_URL` secret. Verify that a run without `GH_READ_TOKENS` exits cleanly having done nothing.

## 2. Tokens and a real run

- [ ] 2.1 The operator creates read-only fine-grained tokens (crimSun-dev, and K-nity if its repos should be followed) and sets `GH_READ_TOKENS`. Verify with a manual run that `token_failures` is 0 and the listed repo count matches the PC's.
- [ ] 2.2 Verify that a GitHub-only repo summary removed from Neon is written back by the next run, and that the run's log shows counts only.
