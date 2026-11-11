# Paste into `/opsx-propose` (or “propose this OpenSpec change”)

Planning only. Do not implement. Do not start `/opsx:apply`.
Change name (kebab-case, exact): `spark-sol-memory-gesture`
Schema: this repo’s default `spec-driven`.
Planning home: Flaxeon root `openspec/` — not a new tree under `SPARK SOL PROTOCOL/`.
If that change folder already exists, continue it — do not invent a second name.
Do not edit `openspec/changes/flaxeon-spark-sol-link/`. That change starts and reloads the galaxy. This change only draws on the galaxy that is already open.

Authority (read before writing artifacts; do not relitigate):
- `SPARK SOL PROTOCOL/CRIMSUN_POOL/GROWTH_SENIOR_DECISION_MANIFEST_SPARK_SOL_MEMORY_GESTURE.md`
- `SPARK SOL PROTOCOL/CRIMSUN_POOL/SPARK_SOL_IMPECCABLE_DESIGN_SPEC.md` §5 Motion, Birth, Camera, Mute, Reduced motion
- Code: `SPARK SOL PROTOCOL/viewer/index.html` (`addNote`, `showCited`, `play`), `SPARK SOL PROTOCOL/server.py` (`/remember`, `/reload`, the `birth` field on a turn)

This change adds a short, repeatable sky gesture when the open SPARK SOL page is showing a memory it just read, and a different gesture when it is showing a memory that was just written. It does not change how memory is stored.

Copy the artifacts below into the change folder. Do not widen scope.

---

## Why this change (for the propose agent — do not put this heading in proposal.md)

The sky already flies to a cited star and pulses filament for about 700 ms when a capture is born. Those two moments look like the same pulse. A memory Flaxeon writes into the database does not get its own picture unless that write arrives as one new star on the open page. The operator asked for a cool animation on both moments, and for each memory’s animation to be its own.

Observed on 2026-11-11:

1. `addNote` places the new star, adds it to `pulsing` for 700 ms, then opens it. `showCited` lights the cited set and the existing fly runs. Small talk calls no camera method.
2. §5 of the design spec is the whole motion grammar: idle yaw, one eased fly, one filament pulse, cited dyes to full. No shake. No confetti. Reduced motion cuts flies and turns pulses into a filament hold. `?mute=1` removes sound and keeps every visual.
3. A gesture that plays when the request is sent, rather than when the row is the resulting state, is false feedback. A failed remember already draws no star.
4. An effect that covers the thing it announces has already shipped once, as a black box where a death animation should have been. This sky does not get a second canvas.
5. Uniqueness is per record, not per visit. The same key plays the same motif the next time. A new random show on every visit would report the click, not the memory.
6. If the SPARK page is not open, the write still commits. Nothing is queued to perform when the page is opened later. The star is simply there.

---

# proposal.md

```markdown
## Why

SPARK SOL already turns a cited note into a fly and a new capture into a short filament pulse. Those two events are the only times the sky should perform, and today they share one pulse. A memory that lands in the database while the galaxy is the open page deserves a birth the operator can tell from a recall, and two different memories should not perform the same gesture. The chart, the plate, and the floor sentence stay readable. The database does not gain a second writer, and a closed page does not save up a show.

## What Changes

- Two gesture families on the open SPARK SOL page only. A recall plays when a turn cites one or more real records. A birth plays when one new memory row is now on the sky. The birth family and the recall family are different for the same key.
- Each record has one motif, chosen from a finite table by its category and its key. The same key always chooses the same motif, including after a reload. Two keys may share a shape only when the table is smaller than the sky, and then their dyes still differ.
- A motif is a change of the star that is already there: its dye, the filament, or the hairline that already leads to a name. It lasts under a second. It does not add a canvas, a sprite, a particle, a shake, or a full-screen wash. One camera remains the only camera. The existing fly still runs once for a one-to-three-note recall. The existing birth still ends by opening that star.
- The motif starts only after the page has the resulting state: the citation list for a recall, the new node for a birth. A failed write, an empty retrieval, and small talk play nothing. The floor sentence is unchanged.
- A reload that is not exactly one new star plays nothing. A reload that adds exactly one star plays that star’s birth motif once. Writes that happen while the page is closed are not stored as pending gestures.
- Reduced motion, when the OS asks for it, is a filament hold on that star instead of the motif. The status line still changes. `?mute=1` keeps the motif and still plays no sound.

This change does **not** add a push channel, a second graph, a gesture on the Desk HUD, a new memory table, or a replay queue.

## Capabilities

### New Capabilities

- `spark-memory-gesture`: on the open galaxy, a confirmed recall and a confirmed one-row birth each play a stable, distinct sky motif without covering the chart.

### Modified Capabilities

- None.

## Impact

- **Affected code**: `SPARK SOL PROTOCOL/viewer/index.html` only, unless a test harness already drives the page. No change to `memory/neon_store.py`, `memory/memory_manager.py`, or the remember route’s write rules.
- **APIs**: none added. The page reads the `birth` object and the cited node list it already receives, and the one-new-star case of a reload it already applies.
- **Dependencies**: no new packages. No new font. No remote asset.
- **Success (this change):** Saving one new memory while the galaxy is open plays that key’s birth motif once, then the star opens. Asking about that same memory later plays a different motif, and plays it again on the next ask. A second memory does not play the first memory’s motif. A failed save plays nothing and draws no star. Small talk does not move the camera. A reload of the whole sky plays nothing. With reduced motion on, the star holds filament instead of performing. A muted tab still shows the motif and stays quiet.
```

---

# specs/spark-memory-gesture/spec.md

```markdown
## ADDED Requirements

### Requirement: Gesture only after the resulting state
The open SPARK SOL page MUST play a memory gesture only after it has the resulting record: a citation list for a recall, or one new star for a birth. The page MUST NOT play a gesture when the request is merely sent, when the write failed, when the retrieval is empty, or when the turn cites no record.

#### Scenario: Failed save
- GIVEN the galaxy page is open
- WHEN the operator asks to remember a fact and the store rejects the write
- THEN no new star appears
- AND no motif plays
- AND the floor shows the failure

#### Scenario: Successful save
- GIVEN the galaxy page is open
- WHEN one new memory row is present on the sky
- THEN that star plays its birth motif once
- AND the motif ends by opening that star

### Requirement: Two families, stable per record
The page MUST treat recall and birth as different families. For a given category and key, the recall motif MUST be the same on every later recall, and the birth motif MUST be the same if that birth is shown again. The birth motif and the recall motif of that same key MUST differ. A motif MUST be drawn with that record’s dye or with filament, on that star or on its existing leader line.

#### Scenario: Same memory, asked twice
- GIVEN a record is already a star
- WHEN the operator asks a question that cites only that record, and later asks again
- THEN both recalls play the same motif
- AND that motif is not the motif the star used when it was born

#### Scenario: Two memories
- GIVEN two records with different keys
- WHEN each is cited alone
- THEN their motifs differ in shape or in dye

### Requirement: The chart stays readable
A motif MUST leave the star, the plate, and the floor sentence visible. The page MUST keep a single camera. A one-to-three-note recall MUST still fly once. Small talk MUST NOT fly and MUST NOT play a motif. A reload that changes more than one star MUST NOT play a motif. A reload that adds exactly one star MUST play that star’s birth motif once.

#### Scenario: Whole sky reload
- GIVEN the page reloads and more than one star is new or moved
- WHEN the sky finishes swapping
- THEN no motif plays

#### Scenario: Reduced motion and mute
- GIVEN the operating system requests reduced motion
- WHEN a recall or a birth would have played a motif
- THEN that star holds filament instead
- AND the status line still changes
- AND a tab opened with mute still shows that hold or motif and plays no sound

### Requirement: Closed page does not queue a show
A memory write that commits while the SPARK SOL page is not open MUST remain a normal write. The page MUST NOT store that write as a gesture to perform on the next open.

#### Scenario: Written while the galaxy is closed
- GIVEN the galaxy page is not open
- WHEN a new memory row is committed
- THEN the row is stored
- AND opening the galaxy later shows the star without playing its birth motif

## MODIFIED Requirements

## REMOVED Requirements
```

---

# design.md

```markdown
# Design: SPARK SOL memory gestures

## Technical Approach

The open page already receives a birth and a citation list, and it already reloads the sky in place. The gesture is a reading of those results. A finite motif table is indexed by a stable hash of category and key, with the birth family offset from the recall family so one key cannot draw both. The drawing uses the star and the leader line that are already on the chart. Nothing is fetched, and nothing is queued for a closed page.

## Architecture Decisions

### Decision: Two families inside the existing grammar
Using the sky’s dye, filament, and leader line because:
- The design spec already forbids shake, confetti, and a second camera
- A confirmed recall and a confirmed birth have to be distinguishable (Norman AXIOM-017)
- Polish here is one small choice, not a new effect system (AXIOM-026, GAME_DESIGN_PLAYFUL_PRODUCTION)

(Rejected: a particle layer or a second canvas — an effect that covers the event already shipped once, MISTAKE-004, MERGE_CATS_DEFENDER.)

### Decision: Stable seed, not a new show per visit
Using category + key because:
- Feedback has to be the record, not the command (Norman RULE-007, AXIOM-009)
- The operator can learn a memory’s gesture

(Rejected: a random motif each time — that reports the click.)

### Decision: No catch-up queue
Using “the star is there on next open” because:
- Replaying every write that happened while the page was closed would perform the command late, after the state is already visible

(Rejected: a pending-gesture list in the server.)

## File Changes
- `SPARK SOL PROTOCOL/viewer/index.html` (modified)
- `SPARK SOL PROTOCOL/tests` or the existing page test, only if one already drives births and citations (modified)
```

---

# tasks.md

```markdown
# Tasks

## 1. Motif table
- [ ] 1.1 Add a finite recall family and a finite birth family, indexed by category and key, birth offset so the same key never picks the same family
- [ ] 1.2 Draw a motif only on that star or its existing leader line, under a second, using that star’s dye or filament

## 2. Wire the two moments
- [ ] 2.1 Play the recall motif for the cited set when a turn cites one or more records, and still fly once
- [ ] 2.2 Play the birth motif once when one new star arrives from a turn or from a reload whose diff is exactly one star, then open it
- [ ] 2.3 Play nothing for a failed write, an empty retrieval, small talk, and any other reload

## 3. Edges
- [ ] 3.1 Reduced motion holds filament instead of performing
- [ ] 3.2 A muted tab still shows the motif and stays silent
- [ ] 3.3 A write while the page is closed leaves no pending gesture
```
