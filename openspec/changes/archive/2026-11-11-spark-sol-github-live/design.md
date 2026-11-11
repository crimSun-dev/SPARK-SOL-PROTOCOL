## Context

See proposal.md. GitHub webhooks would need a public address for this PC. The server binds to 127.0.0.1 only, so the watch polls instead.

## Goals / Non-Goals

**Goals:** new and pushed repos reach Flaxeon's memory unattended, within about 15 minutes.

**Non-Goals:** webhooks or tunnels; a partial GitHub-only publish. Each run is the normal incremental index, so the stale-forget rules stay in one place.

## Decisions

### 1. Polling `gh repo list` with push times

A fingerprint of `{nameWithOwner: pushedAt}` catches creation, deletion, renames and pushes in one cheap listing per owner. It is compared with `cache/github_seen.json`, which is written only after a successful run.

### 2. DPAPI for the passkey

PowerShell `ConvertFrom-SecureString` with no key uses DPAPI for the current user. `passkey_store.load()` calls `CryptUnprotectData` through ctypes, with no new dependency. Another Windows account, or a copy of the file on another machine, cannot decrypt it.

Alternatives considered:
- Plain text in an environment variable. Rejected, because it would be readable by every process and would sit in the registry.
- Only publishing while Flaxeon is unlocked. Rejected by the operator, because a new repo would wait for a hand-started run.

### 3. The run is `build.py`, in its own process

The child's environment drops every `FLAXEON_*` and `TEMPEST_SOL_*` variable, then sets `FLAXEON_PASSKEY` alone. Output is kept only as the publish-report lines. `build.py` holds an `msvcrt` lock on `index/build.lock`, so concurrent runs refuse rather than corrupt the index.

## Risks / Trade-offs

- [Every push re-indexes] → It is incremental: about 2 to 5 minutes, at most one run per interval.
- [The passkey can be decrypted by any program running as the operator] → That is the same trust as the running Flaxeon process. Deleting `cache/passkey.dpapi` stops unattended publishing.
