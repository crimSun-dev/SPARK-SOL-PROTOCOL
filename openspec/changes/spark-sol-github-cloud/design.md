## Context

See proposal.md. The PC's indexer owns every `spark_sol_build` document. Summaries of repos cloned on the PC have a `GitHub: owner/repo (` line in their text, which tells the cloud job which repos to leave alone.

## Goals / Non-Goals

**Goals:** new and pushed GitHub-only repos reach Flaxeon's memory within about 30 minutes while the PC is off. Deleted repos are removed by the PC's next run.

**Non-Goals:**
- Cloned repos.
- Skills and local files.
- The local search index.
- Flaxeon's Firebase replica: Neon is canonical, and Flaxeon reads it.

## Decisions

### 1. Same code, same bytes

`cloud_github.py` imports `build.py` and builds documents with `attach_github`, `summary_text` and `summary_line`. The payload fields and their order mirror Flaxeon's `build_payload`. Comparing documents while ignoring `updated` means an unchanged repo is never rewritten, by either side.

Verified 2026-11-11 with a dry run against Neon after a PC publish:
- 60 repos listed, 36 of them cloned on the PC.
- Of the 24 GitHub-only repos, 23 were unchanged.
- The one to write had a real change: its open pull requests went from 3 to 8.

### 2. Direct Neon write, no passkey

The Action holds its own credential, `NEON_URL`. Flaxeon's passkey gates processes on the PC, and storing it in the cloud would add a secret without adding protection. Writes use the same upsert as `NeonStore.save_document`.

### 3. Tokens

Fine-grained personal access tokens are scoped to one owner. `GH_READ_TOKENS` therefore holds one or more tokens separated by whitespace, for example one for crimSun-dev and one for the K-nity organisation. Each needs only "Metadata: read" and "Contents: read". Listings are merged. The job never deletes: a dry run with a public-only token showed that 10 private repos would have looked deleted.

### 4. A token that sees less never writes less

A fine-grained token without Issues and Pull requests read gets no counts. One without Contents read gets 403 on private READMEs. Writing those thinner documents would make the PC and the cloud overwrite each other on every run, as the first real run showed: 21 written, with "None issues".

So when a count cannot be read, the job keeps the count already in Neon. When a README cannot be read (anything but 404), it leaves the PC's document as it is. Verified with a public-plus-private token lacking Contents read: 0 written, 10 unchanged, 11 kept.

### 4. A token that sees less never writes less

A fine-grained token without Issues and Pull requests read gets no counts. One without Contents read gets 403 on private READMEs. Writing those thinner documents would make the PC and the cloud overwrite each other on every run, as the first real run showed: 21 written, with "None issues".

So when a count cannot be read, the job keeps the count already in Neon. When a README cannot be read (anything but 404), it leaves the PC's document as it is.

## Risks / Trade-offs

- [The Neon credential is in GitHub] → It is an encrypted Actions secret. Pull requests from forks do not receive it. Rotating the Neon password revokes it.
- [GitHub disables scheduled workflows after 60 days without repository activity] → Any push re-enables them, and the PC's commits normally provide that.
