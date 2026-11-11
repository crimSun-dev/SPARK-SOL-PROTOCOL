## 1. Job

- [x] 1.1 Write `cloud_github.py` with the PC's document code, cloned-repo detection, and compare-before-write, with no deletes. Verified with a dry run against Neon: 60 repos, 36 cloned, 23 of 24 unchanged; the 1 write is a real pull-request count change; Deletes were removed after a public-only token showed that 10 private repos would look deleted.
- [x] 1.2 Add the scheduled workflow, and set the `NEON_URL` secret. Verify that a run without `GH_READ_TOKENS` exits cleanly having done nothing.

## 2. Tokens and a real run

- [x] 2.1 The operator creates read-only fine-grained tokens (crimSun-dev, and K-nity if its repos should be followed) and sets `GH_READ_TOKENS`. Verify with a manual run that `token_failures` is 0 and the listed repo count matches the PC's.
- [x] 2.2 Verify that a GitHub-only repo summary removed from Neon is written back by the next run, and that the run's log shows counts only.
- [x] 2.3 Delete summaries of repos GitHub confirms are gone or renamed, and keep everything a token cannot confirm. Verify with planted summaries for repos that never existed, in a real-token run and a public-only simulation, and verify that a real run removes them.
