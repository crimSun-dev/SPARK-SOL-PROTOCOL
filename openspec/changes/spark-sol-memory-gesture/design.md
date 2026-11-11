## Context

See proposal.md for why this change exists. The galaxy page is `viewer/index.html`. One `3d-force-graph` camera is already the only camera. `CRIMSUN_POOL/SPARK_SOL_IMPECCABLE_DESIGN_SPEC.md` §5 is the motion law: idle yaw, one eased fly, a filament pulse, no shake, no confetti. Reduced motion already cuts flies and turns pulses into a filament hold through `REDUCED`. `play()` is the only function that makes sound, and `?mute=1` returns before any audio exists.

A recall already lands in `showCited` after `/chat` returns a node list. An empty list returns before any camera call. A one-to-three-note list calls `openStar` once. A birth already lands in `addNote` after the reply carries `birth`. `commit_note` does not bump `sky_rev`, so a successful remember does not pass through `swapSky` first. `addNote` inserts the node, paints it into `pulsing` for 700 ms, then calls `openStar`. If that id is already on the sky, `addNote` returns and draws nothing.

A reload is `swapSky`. It keeps each known `group:key` at its old position, clears `pulsing`, and does not fly. The first `noteRev` only records `sky_rev` and does not swap. There is no client store of pending gestures.

## Goals / Non-Goals

**Goals:**

- A motif is a short paint on the star that is already in the graph, chosen from a table by category and key, with a separate slot for birth and for recall.
- The paint starts only inside `addNote`, `showCited`, or the one-new-star branch of `swapSky`, after that function has the resulting node.
- `speak()` ending, and a later reload, cannot erase a motif that belongs to a different set.

**Non-Goals:**

- A second canvas, a particle system, a camera path, a push channel, or a queue in `sessionStorage` or on the server.
- Any change to `commit_note`, `neon_store.py`, or the remember route’s success and failure JSON, except reading fields the page already receives.

## Decisions

### 1. A growing table, seeded by category and key, with a variation per note

Dye is `DYES[group]`, one colour per category, so it does not separate keys inside one category. With a fixed eight-slot table, the 47-note sky of 2026-11-11 had 16 same-category pairs on one shape and one dye.

The page holds one constant list of eight shapes. The table is those shapes times `tiers` tiers, where `tiers` is the smallest power of two with `8 × tiers ≥ 2 × the largest category` (32 slots for that sky, whose largest category is 12). A key’s home slot comes from `h = hashStr(group + ":" + key)`: shape `h % 8`, tier `floor(h / 8) % tiers`. Within one category, keys claim slots in order of `h`, then key, and a key whose home is taken moves to the next free slot. The table is at least twice the largest category, so a free slot always exists and two keys of one category never share a slot. Two stars with the same category and key are one record name and share a motif. Birth uses the same tier with shape `(shape + 4) % 8`, so the birth and recall of one key never share a shape.

Tier 0 is the shape as written. Each later tier scales tempo by 0.86–1.04 and size and brightness by 0.75–1.25, spread by golden-ratio steps. Each note adds its own variation from a second hash, `hashStr("motif:" + group + ":" + key)`: about ±6% tempo and ±8% size and brightness. A birth is locked to 700 ms, so on a birth only the size and brightness variation shows. A recall lasts at most 980 ms.

Each shape is a change of the existing halo, the existing core dot, or the existing leader line: scale, opacity, or a brief filament tint, scaled by the tier and the note’s variation. None of them adds a mesh. A birth shape lasts 700 ms, so it ends as the star opens. `paintStar` then returns the star to focus, hover, cited, or rest. The mesh paints its current gesture when it is created, so a hold set before the first draw is visible.

Alternative considered: a random variant per event. Rejected, because asking again would not repeat the motif. Alternative considered: one variant per key with no family offset. Rejected, because birth and recall would look the same. Alternative considered: a fixed eight-shape table with an amplitude step from the next hash bits. Replaced on 2026-11-11 by the operator’s choice of a growing table plus a per-note variation, because a pair whose shape and step both matched still shared a show and nothing guaranteed separation inside a category. Alternative considered: growing the table with a plain modulo. Rejected, because a modulo of any size still collides; collisions are resolved by probing instead.

### 2. Three call sites, and a set that `speak` does not own

`showCited` plays the recall motif only after it has built a non-empty list. An empty list still returns immediately. The existing fly for one to three notes stays. Each cited star plays its own recall slot. `addNote` plays the birth motif only after the new node is in `nodes`. The early return for an id that is already present stays, so a duplicate reply does not perform twice. The 700 ms filament and the following `openStar` stay.

The motif lives in its own set, not in `pulsing`. `speak` adds the focused star to `pulsing` and later clears that set. That clear must not end a motif. While a star is in `pulsing`, filament wins the colour only: no dye tint and no dyed leader. Size and brightness still play. A birth stays in `pulsing` for the whole 700 ms, so a colour-only block would hide the birth motif. When speech ends, the motif continues only if its own timer has not finished.

`swapSky` compares `group:key` against the map it already builds. It plays a birth motif only when the new sky has exactly one key that was absent and no key that was removed. Any other difference, including a full reload, plays nothing. The motif is applied to the new node object after the swap’s `pulsing.clear()`, not to the object that was discarded.

Reduced motion does not run the variant. The same call sites add that star to `pulsing` and leave it there until the next paint that is not a gesture. That is the filament hold §5 already specifies. `?mute=1` is not consulted, because the motif does not call `play()`.

Alternative considered: playing the motif from `turn()` before `addNote` or `showCited`. Rejected, because a failed reply and an empty citation list are not yet distinguishable from a result at that point, and a swap may replace the node object first.

### 3. A closed page stores nothing

No write path records a gesture. The server’s receipt is not given a `gesture` field. Opening the page is the initial graph load. The first `noteRev` still only stores `sky_rev`. A star that appeared while the tab was closed is an ordinary node on that load, so it does not pass through `addNote` and does not pass the one-new-star test of a later swap unless a later reload’s diff is exactly that one key.

## Risks / Trade-offs

- [A growing table moves motifs] → A key keeps its motif until the table doubles, or until a new key of its category sorts ahead of it on its slot. On a doubling, about half the keys move to a new tier and probing changes the shape of about 12%. One new key in a 12-key category changes about 0.2 other keys on average. The table grows by doubling so that this is rare.
- [`speak` clears `pulsing` today] → The motif set is separate, so a reply that both cites and speaks cannot cancel the motif by clearing the filament set.
- [A reload that adds one star and removes another] → That is two changes, so it plays nothing. Only a pure single addition plays a birth.
- [The motif timer and the 700 ms birth pulse overlap] → The birth motif is 700 ms and ends as the star opens. Filament owns the colour for that whole pulse. The motif’s size and brightness remain visible. There is no second camera move.

## Migration Plan

Ship as a change to `viewer/index.html` only. No data migration. Rollback is restoring that file. An open tab picks the new page up on reload. Nothing is queued across that reload.

## Open Questions

None. The eight shapes, the doubling tier rule, the probing order, the per-note variation, the family offset, and the three call sites are decided above.
