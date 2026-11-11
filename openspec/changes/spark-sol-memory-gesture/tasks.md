## 1. Motif table

- [x] 1.1 Add a constant of eight motif shapes in `viewer/index.html`, times tiers of tempo and size. The tier count is the smallest power of two that makes the table at least twice the largest category. Take the home slot from `hashStr(group + ":" + key)`. Within a category, keys claim slots in hash order and probe to the next free slot. Birth is the same tier with shape `(shape + 4) % 8`. Each note adds its own small tempo and size variation from a second hash. Each shape changes only the existing halo, core dot, or leader line, using that record’s dye or filament. A recall lasts under a second. A birth lasts 700 ms. Verify that two calls with the same group and key return the same recall slot and a birth slot of a different shape. Verify that the table is at least twice the largest category, and that across the whole sky no two keys of one category share a slot.

- [x] 1.2 Paint a motif from its own set, separate from `pulsing`, and have `paintStar` return the star to focus, hover, cited, or rest when the timer ends. While a star is in `pulsing`, filament wins the colour only. Size and brightness still play. Verify that `speak` clearing `pulsing` does not remove a star from the motif set.

## 2. The two moments

- [x] 2.1 In `showCited`, after the non-empty citation list exists, play each cited star’s recall motif. Keep the immediate return for an empty list and the single `openStar` for one to three notes. Verify that a one-note answer flies once and plays that key’s recall motif, and that asking again plays the same motif.

- [x] 2.2 In `addNote`, after the new node is in `nodes`, play its birth motif, keep the 700 ms filament pulse, and still call `openStar` when that pulse ends. Keep the early return when the id is already present. Verify that one successful remember plays the birth slot once and then opens the star, and that the birth slot is not the recall slot from 2.1.

## 3. Edges

- [x] 3.1 In `swapSky`, after the new nodes exist and after `pulsing.clear()`, play a birth motif only when exactly one `group:key` was added and none were removed. Verify that a reload of the whole sky plays nothing, and that a reload whose only difference is one new key plays that key’s birth motif once.

- [x] 3.2 Leave failed writes, empty retrievals, and small talk on the paths that already draw no star and call no camera method. Do not add a pending-gesture store. Verify that a rejected remember plays nothing and draws no star, that small talk does not move the camera, and that a star written while the page was closed appears on the next open without a birth motif.

- [x] 3.3 When `REDUCED.matches` is set, the three call sites hold filament on that star instead of running a variant. Do not call `play()` from a motif. Verify that reduced motion shows a filament hold and still changes the status line, and that `?mute=1` still shows the motif and produces no sound.
