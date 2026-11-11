# SPARK SOL — Impeccable design specification

**Status:** pinned brief for the protocol page. This is not `DESIGN.md`. That file is written after the page is built and reviewed. A later impeccable build treats this document as the brief the operator already pinned. The visual world is not open: the November pack requires a cinematic black field, a starfield, nodes glowing by folder, and a slow idle rotation. This spec makes that requirement specific enough that the page cannot collapse into a generic force-graph demo or into an Iron Man visor.

**Visitor mode:** Operate. The person at the screen is in a dark room, often not looking at the display, checking with a glance which of them is talking and which note answered. The galaxy is the instrument, not a landing page.

**seed:** none (brief-pinned by the prompt packs; concept-seed was not run). Reopen a world tournament only if this spec is rejected.

**Sibling discrimination.** The Desk HUD is ember on brown-black (`#ff3b1f` on `#0a0402`). TEMPEST SOL is gold on blue-black (`#ffb300` on `#020305`). SPARK SOL stays identifiable beside both because the sky and the live states are indigo and verdigris. The one ember pixel is the X in the family wordmark. That exception is recorded in `PRODUCT.md` and does not spread into the floor, the stars, or the status line.

---

## 1. Job and audience

The operator of F.L.A.X.E.O.N, at the Windows desk, asking a private folder of markdown notes a question with the network unplugged. They need to know four things without a manual: that the machine is listening, what it thinks it heard, which note the answer came from, and that the voice and the brain are the local ones.

Success is a turn they can trust. The star flies to the note while the cloned voice speaks the sentence. A capture becomes a new star without a reload. A muted tab stays quiet.

What is true here and would be false of a generic chatbot: the corpus is a sky the operator can fly, every answer points at the stars it used, and the badge can show that nothing left the machine.

## 2. Direction

**THESIS.** The notes are already a sky. The page is the observatory floor under that sky: one instrument reading at the bottom, the stars taking the rest. Refused: a dashboard of cards, a chat column beside a toy graph, a helmet HUD, a neon cyan terminal.

**OWN-WORLD.** Indigo void, bone ink, a verdigris filament used only for "this is local and live." A star's color is its source pool. Courses sit as tight neighborhoods inside that pool's region. The plate names the course. Chrome is a hairline and a plate, the way a paper star chart sits on a black table. No glass, no outer glow stacks, no grid of icon tiles.

**STORY.** The operator understands that SPARK SOL is F.L.A.X.E.O.N speaking from the notes on this machine, believes the highlighted stars are the source, and either speaks a wake alias or types in the bottom bar.

**FIRST VIEWPORT.** The entire first screen is the sky. No top navigation. The protocol plate sits in the upper left at a small size: the mark, then `F.L.A.X.E.O.N`, then `SPARK SOL`, then the live note count taken from `GRAPH.nodes.length` (`128 notes` as a shape, the real number in the build). The sky rotates slowly. The bottom 72 pixels are the floor: a one-line status (`LISTENING` / the heard words / `THINKING` / `SPEAKING`) and, under it, a single hairline input whose placeholder is `Ask the notes`. The primary action is that input, and equally the wake alias when hands-free is on. Hands-free is a word on the floor, `HANDS-FREE ON`, not a floating round button.

**FORM.** Observatory chart under an open night, which is the pack's pinned galaxy made into a specific instrument. Position: the packs required the sky; this spec chooses the chart-and-floor so the sky has a job. seed: none (unavailable — brief-pinned).

**FINISH.** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

### Raises kept from the category defaults we are not shipping

- From the helmet-HUD default: the discipline of one status line that always tells who has the floor. The visor chrome, the rings, and the targeting brackets stay out.
- From the chat-app default: the discipline that the latest answer is readable as a sentence on the floor while it is spoken. A transcript log stays out.

## 3. Color, type, material

Strategy: **Restrained.** The void is the color. One filament color earns the live states. Pool dyes are dim at rest and full on the answer cluster or the focused star. Color never means "course," because dozens of courses would have to share a dye.

Scene that forces dark: evening desk, the display is the lamp, the operator looks up from a notebook. A light theme would glare. A pure `#000` OLED void crushes the starfield, so the ground is a deep indigo, not a dead black.

| Role | Hex | Use |
|---|---|---|
| Void | `#0c1224` | Page ground, the WebGL clear color |
| Void lift | `#161d33` | Node plate surface |
| Bone | `#efe6d4` | Answer sentence, note titles, input text |
| Bone dim | `#a39886` | Placeholder, folder name, idle status |
| Filament | `#7dbea8` | Local-live only: speaking pulse, `VOICE local`, the born-star pulse, the hands-free word when on |
| Family ember | `#ff3b1f` | The X in `F.L.A.X.E.O.N` on the plate, and nowhere else |
| Warning | `#e36a4a` | Ears down, write failed, cloud unreachable. Not the Desk ember; enough red to read as a fault |
| Star core | `#f4f0e6` | The focused node |
| Pool dyes | see the twelve below | One dye per allowlist root. No two pools share a dye. Dim at rest, full when that star is focused or cited. |

Filament is withheld from decoration. A star at rest shows its pool dye, turned down. Filament means "the local system is acting," and it is not one of the twelve dyes.

| Pool | Dye |
|---|---|
| Books | `#c4b48a` |
| Sampoerna | `#8aa0b8` |
| SNHU | `#b8929a` |
| Sophia | `#8eaa96` |
| Study.com | `#b8a0c4` |
| Writing prose | `#c4a48a` |
| Manga | `#7f93a8` |
| Full stack | `#9aa57a` |
| Game-dev books | `#b08968` |
| Engine guides | `#8d99a6` |
| Experience | `#6f8f78` |
| FLAXEON records | `#a6847c` |

Captures born from a remember-phrase stay bone until the plate can name them. They do not borrow a pool dye. Sophia is one dye. Pre-Calculus is a dense neighborhood inside that dye, not a second color. The plate reads the course name.

**Memory-region dyes, this first load.** The memory sky and the markdown sky are never one graph. On this load a dye means the category. On the later load the same chalk means its pool. A near-miss hex would still look like the pool it was avoiding, so these eight are eight of the twelve chalks, assigned here and not recolored.

| Region | Dye | Same chalk as |
|---|---|---|
| identity | `#c4b48a` | Books |
| preferences | `#b8a0c4` | Study.com |
| projects | `#8aa0b8` | Sampoerna |
| relationships | `#b8929a` | SNHU |
| wishes | `#c4a48a` | Writing prose |
| notes | `#8eaa96` | Sophia |
| documents | `#8d99a6` | Engine guides |
| sessions | `#7f93a8` | Manga |

Full stack `#9aa57a`, Game-dev books `#b08968`, Experience `#6f8f78`, and FLAXEON records `#a6847c` are unused on this page. Filament, warning, ember, and Tempest gold are not region dyes. A region name is drawn only when that region has at least one star. An empty category is absent.

The source word sits on the floor, not on a star. `Neon` is bone dim: the store answered, and it is not local, so it is not filament. `mirror` is warning: the canonical store did not answer. The sky still renders from the mirror.

**Type.**

- Answer sentence and note excerpt: **Literata**, 18 px on the floor, 16 px in the plate. It is a reading face because the answer is one sentence the operator reads while hearing it.
- Plate labels, the protocol name, the input: **Schibsted Grotesk**. Workhorse, not a display costume.
- Status line: **Atkinson Hyperlegible**, 14 px, tracking 0.04 em. The status is an instrument reading and has to survive a glance from a tired operator. A mono face was refused because "technical status equals monospace" is the category habit.

Serve the font files from `viewer/vendor/fonts/`. No Google Fonts stylesheet. That host would fail the drill.

**Material.** Stars are points with a 2 px core and a soft 8 px falloff in the pool dye. Links are 1 px at 30% bone. The plate is a flat void-lift rectangle with a 1 px bone-dim edge, no shadow, no blur. The floor is a 1 px line in bone-dim separating sky from the reading strip. Idle rotation is the sky's only always-on motion.

## 4. Layout and interaction

Desktop first. The pack's page is a desk instrument. The phone is a later problem; if the window is under 800 px wide the plate becomes full-width under the sky and the sky keeps at least 50% of the height. The status and the input never leave the floor.

**Hierarchy, top to bottom of attention, not of the document:**

1. The star that just took focus, or the cluster that lit.
2. The status line, which is the system image.
3. The answer sentence, on the floor, one or two lines, replaced by the next answer. It is not a scrolling chat log. The note is on the plate; the sentence does not recite it.
4. The input.

**Node plate.** Opens from the right, 380 px, when a star is focused or an answer cites one to three notes. Shows the label, the folder, the excerpt. Closes when the operator clicks the void. Four or more sources do not open four plates; the cluster lights and the floor sentence stands.

**Badge.** Under the status, hidden. On a real change of brain or voice, including a fall to the browser synthesizer: `BRAIN local · qwen3.5:9b` and `VOICE local · Spark`, filament when local, warning color when the voice is `browser` or the brain is `claude`. Visible 5 seconds. The same voice on the next reply does not show it again.

**Hands-free.** The word on the floor toggles it. On: filament. Off: bone dim, and the mic button is the push-to-talk control, a word `HOLD TO TALK`, not an icon-only circle. Push-to-talk skips the wake alias.

**Birth.** The new star appears at the related node's position, filament pulse for about 700 ms, then the camera flies. If the write failed, no star appears and the floor shows the error in the warning color while the voice says it.

**Names on the sky.** The idle sky does not label every star. One faint region name sits on each region, the way a chart names a constellation: the fact category on the memory sky, the pool name when the markdown index is the sky. A star's own name shows in three cases only: it has focus, an answer cites it, or the cursor is on it. The plate still carries the full name, the folder or category, and the excerpt.

**Camera.** One `3d-force-graph` camera. The page does not scale the canvas with CSS. Idle rotation is slow enough to read a region name. A fly eases. Small talk calls no camera method.

**Mute.** `?mute=1` removes sound and leaves every visual, including the heard text.

**First load.** The sky is the parent F.L.A.X.E.O.N memory database: Neon when it answers, otherwise `memory/long_term.json` in the parent folder. The note count is that read. Fact categories are the regions, colored by the memory-region table above. The markdown allowlist is not this load. Chat, voice, hearing, the badge, and births are absent until the server exists, and the page does not invent replies. The floor does not say `LISTENING`, `THINKING`, or `SPEAKING` on this build. It says the source (`Neon` or `mirror`) and `VOICE not running`. Boot is not spoken. **Empty** is the failure state only: if both the database and the mirror return nothing, the floor reads `No notes indexed`.

**Boot copy, spoken once.** `Still here.` The note count is on the plate, not in the sentence.

**Answer copy.** Whatever the model returned, one sentence plus the facts, shown on the floor as text while it plays. The page does not add a second caption track.

## 5. Motion

One grammar:

- Idle: sky yaw, continuous, low rate.
- Fly: on focus and on a one-to-three-note answer.
- Pulse: filament, on birth and while `SPEAKING` is the status. The pulse sits on the focused star, or on the protocol mark when no star is focused.
- Cluster: selected dyes go to full for the cited set. No shake, no confetti.

Reduced motion: if the operator's OS asks for it, idle rotation stops, flies cut, pulses become a filament hold. The status line still changes.

## 6. States the build has to show

| State | Floor | Sky | Sound |
|---|---|---|---|
| Boot | `Still here.` already spoken; status `STANDING BY` | Note count matches `GRAPH` | One line, then silence |
| Listening | `LISTENING` in filament | Unchanged | None |
| Heard | The transcript in bone | Unchanged | None |
| Thinking | `THINKING` | Unchanged | None |
| Speaking | The answer sentence; status `SPEAKING` | Fly or cluster, unless small talk | Chunked local voice |
| Muted tab | Same visuals | Same | `play()` returns |
| Alias missed | Status returns to standing by. Nothing is logged on screen | Unchanged | None |
| Write failed | Warning sentence from the server error | No new star | The failure, spoken |
| Voice engine down | Badge `VOICE browser` for 5 seconds | Unchanged | Browser synthesizer |
| Ears down | Status `EARS DOWN` in warning, input still works | Unchanged | Answers still speak |
| Cloud unreachable | One warning sentence | Unchanged | That sentence, local voice |
| Wi-Fi off | No change from a local turn | Sky still renders from `vendor/` | Local |

## 7. Boundaries

In scope for the first built page: the sky, the floor, the plate, the badge, birth, the states above.

Out of scope: a chat history column, settings screens, a model picker UI (the voice routes are the picker), accounts, a second theme, embedding inside the Qt HUD, a phone layout beyond the 800 px rule.

Anti-goals: the word Jarvis, a robot face, a helmet, an arc reactor, cyan-on-black terminal glow, glassmorphism, a card grid, a left nav, a hamburger, instructions on the sky.

## 8. Logo — binding lockup

The approved lockup is `brand/Flaxoen Spiral Spark Logo.png` in this folder. The filename is spelled Flaxoen on purpose; that is the name of the file. The same bytes live at `F.L.A.X.E.O.N/assets/Flaxoen Spiral Spark Logo.png`. The thin-ring generation prompt is retired. Do not regenerate a competing mark.

What the file contains, so a builder can crop it without redrawing it:

- Ground `#0c1224`.
- Mark: a bone swirl of crescent strokes, a four-point star at the center, one verdigris arc on the outer right. It reads at plate size and as a file icon.
- Wordmark: `F.L.A.X.E.O.N` in bone, the X alone in family ember `#ff3b1f`. Under it, `SPARK SOL` in bone, between two hairline rules.

The page plate uses this mark and this wordmark, small, upper left. Ember does not appear again on the page.

Alt text: `F.L.A.X.E.O.N SPARK SOL. A bone spiral with one verdigris arc, and an ember X in the family name.`

## 9. What the builder must not invent

- A second accent "to make it pop." Filament has a job. Group dyes are already the variety.
- A font from a CDN.
- A chat transcript that restates the plate.
- A wake word printed in a tutorial overlay. The floor word `HANDS-FREE ON` is the affordance. The aliases live in the README.
- Light mode.
- Painting the sky, the floor, or the stars in Desk ember or Tempest gold. The ember X in the family wordmark is the only exception, and it is already in the lockup.
