## Why

Flaxeon knows each skills folder only as one summary. The full text of every skill lives in SPARK SOL's local index, which Flaxeon itself cannot recall from. The operator wants every skill and every experience module on this PC in Flaxeon's database, each one recallable by name and each one a star.

## What Changes

- Skill folders read: `~/.cursor/skills`, `~/.claude/skills`, `~/.claude/plugins`, `~/.gemini/skills`, `~/.codex/skills` and `~/.agents/skills`. The new folders also join the local full-text index.
- `~/.claude/skills/POOL` joins the index as a second pools folder. Files identical in path and size to `~/.cursor/skills/POOL` are skipped, so only its own files (for example two experience modules and its pool index) are added.
- One document per skill in Flaxeon's shared memory (`kind: skill`):
  - Contents: `SKILL.md` first, then that skill's reference `.md` files. Text is filled to just under Flaxeon's 48 KB document cap, and omitted references are named at the end.
  - Identical copies of a skill in several folders become one document that lists every location.
  - A same-named skill with different content gets its own document.
- One document per experience module (`kind: experience`), holding the module's full text within the same cap, in place of the short summary.
- Every skill and experience document is a star: one per skill in the Skills region, and one per module in the Experience region.
- All of these are written by the indexer only through Flaxeon's own memory path, with the passkey gate open. They are scrubbed, counted in Neon after writing, and forgotten when their source is gone.

## Capabilities

### New Capabilities

- `skill-corpus`: every skill and experience module on this PC is a scrubbed, size-capped document in Flaxeon's shared memory and a star on the galaxy.

### Modified Capabilities

- None. `workspace-index` (in change `spark-sol-workspace-index`) is not yet archived; this change extends its roots and its publish set without changing its existing requirements.

## Impact

- `build.py` (roots, skill discovery, payloads), `read_memory.py` (draws `skill` and `experience` documents as stars).
- Neon gains about 600 documents, most under 20 KB, none over 48 KB. Flaxeon's prompt briefing is unaffected: it lists document titles within a fixed 320-character budget.
