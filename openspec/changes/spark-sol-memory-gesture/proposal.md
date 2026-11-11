## Why

SPARK SOL already turns a cited note into a fly and a new capture into a short filament pulse. Those two events are the only times the sky should perform, and today they share one pulse. A memory that lands in the database while the galaxy is the open page deserves a birth the operator can tell from a recall, and two different memories should not perform the same gesture. The chart, the plate, and the floor sentence stay readable. The database does not gain a second writer, and a closed page does not save up a show.

## What Changes

- Two gesture families on the open SPARK SOL page only. A recall plays when a turn cites one or more real records. A birth plays when one new memory row is now on the sky. The birth family and the recall family are different for the same key.
- Each record has one motif, chosen by its category and its key from a table of eight shapes times tiers of tempo and size. The table doubles whenever the largest category outgrows half of it. Within one category, keys take slots in hash order and a key whose slot is taken moves to the next free one, so two keys of one category, which share a dye, never share a slot. Each note also carries its own small tempo and size variation. The same key chooses the same motif, including after a reload, until the table doubles or a new key of its category takes its slot. Birth and recall of that key use different shapes.
- A motif is a change of the star that is already there: its dye, the filament, or the hairline that already leads to a name. It lasts under a second. It does not add a canvas, a sprite, a particle, a shake, or a full-screen wash. One camera remains the only camera. The existing fly still runs once for a one-to-three-note recall. The existing birth still ends by opening that star.
- The motif starts only after the page has the resulting state: the citation list for a recall, the new node for a birth. A failed write, an empty retrieval, and small talk play nothing. The floor sentence is unchanged.
- A reload that is not exactly one new star plays nothing. A reload that adds exactly one star plays that star’s birth motif once. Writes that happen while the page is closed are not stored as pending gestures.
- Reduced motion, when the OS asks for it, is a filament hold on that star instead of the motif. The status line still changes. `?mute=1` keeps the motif and still plays no sound.

This change does not add a push channel, a second graph, a gesture on the Desk HUD, a new memory table, or a replay queue.

## Capabilities

### New Capabilities

- `spark-memory-gesture`: on the open galaxy, a confirmed recall and a confirmed one-row birth each play a stable, distinct sky motif without covering the chart.

### Modified Capabilities

- None.

## Impact

- **Affected code**: `viewer/index.html` only, unless a test harness already drives the page. No change to Flaxeon’s `memory/neon_store.py`, `memory/memory_manager.py`, or the remember route’s write rules.
- **APIs**: none added. The page reads the `birth` object and the cited node list it already receives, and the one-new-star case of a reload it already applies.
- **Dependencies**: no new packages. No new font. No remote asset.
- **Success**: Saving one new memory while the galaxy is open plays that key’s birth motif once, then the star opens. Asking about that same memory later plays a different shape in the same tier, and plays it again on the next ask. Two keys in one category never share a motif slot. A failed save plays nothing and draws no star. Small talk does not move the camera. A reload of the whole sky plays nothing. With reduced motion on, the star holds filament instead of performing. A muted tab still shows the motif and stays quiet.
