# spark-memory-gesture

## Purpose

On the open SPARK SOL galaxy, a confirmed memory recall and a confirmed one-row birth each play a short, stable sky motif that the operator can tell apart, without covering the chart.

## Requirements

### Requirement: Gesture only after the resulting state
The open SPARK SOL page MUST play a memory gesture only after it has the resulting record: a citation list for a recall, or one new star for a birth. The page MUST NOT play a gesture when the request is merely sent, when the write failed, when the retrieval is empty, or when the turn cites no record.

#### Scenario: Failed save
- **GIVEN** the galaxy page is open
- **WHEN** the operator asks to remember a fact and the store rejects the write
- **THEN** no new star appears
- **AND** no motif plays
- **AND** the floor shows the failure

#### Scenario: Successful save
- **GIVEN** the galaxy page is open
- **WHEN** one new memory row is present on the sky
- **THEN** that star plays its birth motif once
- **AND** the motif ends by opening that star

### Requirement: Two families, stable per record
The page MUST treat recall and birth as different families. For a given category and key, the recall motif MUST be the same on every later recall, and the birth motif MUST be the same if that birth is shown again, unless the motif table has doubled or a new key of that category has taken its slot in between. The birth motif and the recall motif of that same key MUST differ in shape. The motif table MUST hold at least twice as many slots as the largest category has keys, and two different keys of one category MUST NOT share a motif slot. Each key MUST carry its own small tempo and size variation. A motif MUST be drawn with that record’s dye or with filament, on that star or on its existing leader line, and MUST last under a second.

#### Scenario: Same memory, asked twice
- **GIVEN** a record is already a star
- **WHEN** the operator asks a question that cites only that record, and later asks again
- **THEN** both recalls play the same motif
- **AND** that motif is not the motif the star used when it was born

#### Scenario: Two memories in one category
- **GIVEN** two records with different keys in the same category
- **WHEN** each is cited alone
- **THEN** their motifs use different slots
- **AND** each record repeats its motif on the next ask

#### Scenario: Shared slot across categories
- **GIVEN** two records in different categories that land on the same slot
- **WHEN** each is cited alone
- **THEN** their dyes differ

#### Scenario: The largest category grows
- **GIVEN** a category gains keys until it holds more than half the table
- **WHEN** the next motif is chosen
- **THEN** the table has doubled
- **AND** no two keys of one category share a slot

### Requirement: The chart stays readable
A motif MUST leave the star, the plate, and the floor sentence visible. The page MUST keep a single camera. A one-to-three-note recall MUST still fly once. Small talk MUST NOT fly and MUST NOT play a motif. A reload that changes more than one star MUST NOT play a motif. A reload that adds exactly one star MUST play that star’s birth motif once.

#### Scenario: Whole sky reload
- **GIVEN** the page reloads and more than one star is new or moved
- **WHEN** the sky finishes swapping
- **THEN** no motif plays

#### Scenario: Reduced motion and mute
- **GIVEN** the operating system requests reduced motion
- **WHEN** a recall or a birth would have played a motif
- **THEN** that star holds filament instead
- **AND** the status line still changes
- **AND** a tab opened with mute still shows that hold or motif and plays no sound

### Requirement: Closed page does not queue a show
A memory write that commits while the SPARK SOL page is not open MUST remain a normal write. The page MUST NOT store that write as a gesture to perform on the next open.

#### Scenario: Written while the galaxy is closed
- **GIVEN** the galaxy page is not open
- **WHEN** a new memory row is committed
- **THEN** the row is stored
- **AND** opening the galaxy later shows the star without playing its birth motif
