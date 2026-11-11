## Context

See proposal.md. `build.py` already publishes one `repo_index` summary per project through `memory_gate()` and counts the result in Neon. `read_memory.py` draws indexer documents as stars only when their kind is `repo_index`.

## Goals / Non-Goals

**Goals:** a document and a star per skill and per experience module, within Flaxeon's cap, deduplicated across folders.

**Non-Goals:** documents per reference file; embeddings; any change to Flaxeon's cap or its prompt briefing.

## Decisions

### 1. A skill is a folder with `SKILL.md`; its body is `SKILL.md` plus its own references

A skill's references are the `.md` files below its folder, excluding any subfolder that has its own `SKILL.md`, which is a skill of its own. The text is filled in a fixed order, `SKILL.md` first and then references by path, up to 47 KB. That leaves room under Flaxeon's 48 KB `DOCUMENT_TEXT_MAX`, so `build_payload` never falls back to a pointer and drops the text.

### 2. Keys and duplicates

- The name comes from the `name:` field in the frontmatter, or else from the folder name.
- The key is `skill_<slug(name)>`. Copies with the same content hash merge into that one document, and every location is listed under "Also at".
- A different skill with the same name gets `skill_<slug(name)>_<root>`, plus a short hash suffix if that key is also taken.

Alternative considered: one document per folder. Rejected, because `~/.cursor` and `~/.claude` hold mostly the same skills, which would put two identical stars side by side.

### 3. Experience modules carry full text

An experience project's payload is its module text, within the same cap, with kind `experience`. Pool courses and the other projects keep their `repo_index` summaries.

### 4. The second POOL is deduplicated by path and size

`~/.claude/skills/POOL` is walked as a pools root. A file whose path relative to the POOL, and whose size, match the file in `~/.cursor/skills/POOL` is skipped.

### 5. Stars

`read_memory.py` draws every document tagged `indexer: spark_sol_build` whose region is an index region, whatever its kind. Neon counting and forgetting likewise cover every document with that tag.

## Risks / Trade-offs

- [About 600 more stars] → The sky lays out by region. Find searches every star by name.
- [Flaxeon's local cache grows by a few MB] → It is Flaxeon's offline copy. It is measured after the first run.
