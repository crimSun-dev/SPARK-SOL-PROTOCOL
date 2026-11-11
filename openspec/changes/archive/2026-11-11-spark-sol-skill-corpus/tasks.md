## 1. Discovery

- [x] 1.1 Add the four new skill folders to the indexer's roots, and `~/.claude/skills/POOL` as a pools root skipping files identical to `~/.cursor/skills/POOL`. Verify with a dry run that the new roots are listed, and that only the `.claude` POOL's own files are added.
- [x] 1.2 Discover skills as folders with `SKILL.md` outside pruned folders, with names from frontmatter, deduplicated by content. Verify that the count of distinct skills is reported, that no skill lies under `node_modules`, and that identical copies list every location.

## 2. Documents

- [x] 2.1 Build one `skill` document per skill: `SKILL.md` first, then references, under the cap, with omitted references named. Verify with a unit check that a skill over the cap keeps its full `SKILL.md`, and that every payload carries `text` rather than a `pointer`.
- [x] 2.2 Build one `experience` document per experience module with its full text within the cap. Verify that the experience documents in Neon carry the module text.
- [x] 2.3 Count and forget every indexer document, whatever its kind. Verify with the fake-store checks, and with a real run whose report matches Neon's count of indexer documents.

## 3. Stars and a real run

- [x] 3.1 Draw `skill` and `experience` indexer documents as stars in their regions. Verify after a real publish that `/graph` shows one Skills star per skill document and one Experience star per module.
- [x] 3.2 Confirm that other memory is untouched. Verify that Neon's facts and non-indexer documents are identical before and after the run. Result on 2026-11-11:
  - The indexer forgot 0 documents and wrote only its own 831.
  - The fact differences in that window were 6 wishes merged by Dreamsite on the operator's instruction, recorded in `forgotten_facts` at 08:51 UTC.
