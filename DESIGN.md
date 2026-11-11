---
name: SPARK SOL
description: F.L.A.X.E.O.N's fully local notes instrument, drawn as an observatory chart over the operator's memory.
colors:
  void: "#0c1224"
  void-lift: "#161d33"
  bone: "#efe6d4"
  bone-dim: "#a39886"
  star-core: "#f4f0e6"
  warning: "#e36a4a"
  filament: "#7dbea8"
  dye-identity: "#c4b48a"
  dye-preferences: "#b8a0c4"
  dye-projects: "#8aa0b8"
  dye-relationships: "#b8929a"
  dye-wishes: "#c4a48a"
  dye-notes: "#8eaa96"
  dye-documents: "#8d99a6"
  dye-sessions: "#7f93a8"
typography:
  headline:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "26px"
    fontWeight: 400
    lineHeight: 1.28
  title:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "21px"
    fontWeight: 500
    lineHeight: 1.22
    letterSpacing: "-0.005em"
  body:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.62
  body-ui:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
  input:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1
  chart-region:
    fontFamily: "Literata, Georgia, serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.03em"
  chart-name:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.01em"
  chart-name-focus:
    fontFamily: "Schibsted Grotesk, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "0.01em"
  label:
    fontFamily: "Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.04em"
  label-meta:
    fontFamily: "Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.02em"
rounded:
  none: "0px"
  dot: "50%"
spacing:
  gutter: "24px"
  gutter-compact: "16px"
  plate-inset: "20px"
  plate-stack: "22px"
  floor-gap: "24px"
components:
  floor:
    backgroundColor: "{colors.void}"
    textColor: "{colors.bone-dim}"
    height: "72px"
    padding: "0 24px"
  floor-status:
    textColor: "{colors.bone-dim}"
    typography: "{typography.label}"
  floor-status-warning:
    textColor: "{colors.warning}"
    typography: "{typography.label}"
  floor-word:
    textColor: "{colors.bone-dim}"
    typography: "{typography.label}"
    padding: "6px 0"
  ask-input:
    textColor: "{colors.bone}"
    typography: "{typography.input}"
    rounded: "{rounded.none}"
    height: "28px"
    padding: "0 0 4px"
  plate:
    backgroundColor: "{colors.void-lift}"
    textColor: "{colors.bone}"
    rounded: "{rounded.none}"
    width: "380px"
  plate-head:
    textColor: "{colors.bone-dim}"
    typography: "{typography.label-meta}"
    padding: "14px 16px 13px 20px"
  plate-body:
    textColor: "{colors.bone}"
    padding: "22px 20px 24px"
  plate-close:
    textColor: "{colors.bone-dim}"
    typography: "{typography.label-meta}"
    padding: "6px 4px"
  plate-close-hover:
    textColor: "{colors.bone}"
  plate-dye:
    rounded: "{rounded.dot}"
    size: "8px"
  region-name:
    textColor: "{colors.bone-dim}"
    typography: "{typography.chart-region}"
  star-name:
    textColor: "{colors.bone}"
    typography: "{typography.chart-name}"
  star-name-focus:
    textColor: "{colors.bone}"
    typography: "{typography.chart-name-focus}"
  protocol-plate:
    width: "236px"
  protocol-count:
    textColor: "{colors.bone-dim}"
    typography: "{typography.label-meta}"
---

# Design System: SPARK SOL

## Overview

**Creative North Star: "The Observatory Floor"**

The notes are already a sky. SPARK SOL is the floor of the observatory under it: a dark room, one instrument reading at the bottom edge, and the stars taking everything else. The F.L.A.X.E.O.N memory renders as a slowly turning 3D chart in an indigo void, each fact category a loose constellation with one italic name written under it the way a paper star chart names its figures. Chrome is a hairline and a flat plate, nothing more. The page is operated, not browsed: the operator glances at it from an evening desk where the display is the lamp, so the status line must read at a glance and the sky must never shout.

Density is extremely low by design. At rest the screen holds the lockup and a note count in the upper left, the sky, and a 72px floor carrying the source reading, the voice reading, an inert `Ask the notes` input, and two floor words. Opening a star flies the camera to it, rings it, pins its name on a hairline leader, and slides a 380px plate in from the right with the real record. Nothing else appears. The world is restrained to the point of austerity: the void is the color, bone is the ink, and the category dyes are dim chalk.

Confirmed rejections, carried from the direction contract and the binding brand commitments: no card dashboard, no chat column beside a toy graph, no helmet HUD or visor chrome, no glass, no glow stacks, no tiles, no light theme, no cyan terminal glow. The ember X lives inside the lockup raster and nowhere else.

**Key Characteristics:**
- A full-bleed WebGL sky in an indigo void (not black), with a far bone dust field for depth and slow idle yaw.
- Chart lettering over the sky: italic Literata region names, Schibsted star names on 1px hairline leaders, a thin bone ring on the focused star.
- A 72px observatory floor separated from the sky by a single bone-dim hairline.
- A flat void-lift plate with a 1px bone-dim edge, square corners, no shadow, no blur.
- Three faces with three jobs: Literata reads, Schibsted Grotesk works, Atkinson Hyperlegible gauges.
- All fonts and scripts served from `viewer/vendor/`; the page opens no outside host.

## Colors

A restrained night palette: one indigo ground, one warm bone ink in two strengths, one warning red, eight dim chalk dyes that mean category, and one verdigris held in reserve.

### Primary
- **Bone Ink** (bone): Every primary reading. Plate titles, the short fact value, excerpts, typed input, the focused and hovered star names, the leader tick ring, the bold numeral in the note count. Constellation links draw in bone at 30% inside a region and 62% when a link touches the focused or hovered star.

### Secondary
- **Verdigris Filament** (filament): Reserved for "this is local and live": the speaking pulse, `VOICE local`, the born-star pulse, `HANDS-FREE ON`. Declared on `:root` and deliberately unused in this build, because the voice server does not run yet. Its absence is information.

### Tertiary
- **Fault Red** (warning): Readings that are not the healthy path. On this build it marks `MIRROR` (Neon was not read, the local copy was), `No notes indexed`, and the WebGL refusal sentence. Enough red to read as a fault, and deliberately not the Desk HUD ember.

### Neutral
- **Indigo Void** (void): Page ground, floor ground, and the WebGL clear color. Deep indigo rather than `#000` so the starfield does not crush.
- **Void Lift** (void-lift): The plate surface, one small step up from the void. The only raised tone in the system.
- **Chalk Bone** (bone-dim): Secondary text and every hairline. Idle status, floor words, the placeholder, plate meta, region names, leaders. Hairlines also use it at reduced alpha: 35% under the plate head, 25% above the plate source, 45% under the input, 50% for the 11px status separator.
- **Star Core** (star-core): The 2px core of the focused star only. A near-white with bone warmth, so focus reads as the brightest point in the sky without leaving the palette.

### Category Dyes
Eight dims, one per memory category, applied to each star's halo and core: identity (dye-identity), preferences (dye-preferences), projects (dye-projects), relationships (dye-relationships), wishes (dye-wishes), notes (dye-notes), documents (dye-documents), sessions (dye-sessions). The plate head repeats the dye as an 8px dot beside the region name. All eight clear 5.8:1 on the void.

### Family Ember (lockup only)
- **Family Ember** (#ff3b1f): Exists only as the X in `F.L.A.X.E.O.N` inside the lockup raster `vendor/brand/spark-sol-lockup.png`. It is not a page token and is not declared in CSS.

### Named Rules
**The Void Is The Color Rule.** The indigo void and bone ink carry the page. Dyes stay dim at rest (halo at 50%, core at 78%) and only the focused star brightens. No second accent is added "to make it pop."

**The Filament Reserve Rule.** Verdigris means local and live, and nothing else. It is never decoration, never a dye, never a hover color. Until a local system is actually acting, it does not appear.

**The One Ember Pixel Rule.** The family ember appears once, as the X inside the lockup image. It never spreads to the floor, the stars, the status line, or the warning color.

**The Dye Means Category Rule.** On the memory sky a dye means fact category. The planned markdown sky reuses the same hexes as pool dyes per the pinned spec, and the two skies never share a graph, so one hex never carries two meanings on one screen.

## Typography

**Reading Font:** Literata (with Georgia, serif)
**Working Font:** Schibsted Grotesk (with system-ui, sans-serif)
**Gauge Font:** Atkinson Hyperlegible (with system-ui, sans-serif)

**Character:** A bookish serif for anything read as content, a plain grotesk for names and the controls you type into, and a hyperlegible sans for instrument readings that must survive a tired glance. Monospace was refused for status on purpose: "technical status equals mono" is the category habit.

### Hierarchy
- **Headline** (Literata 400, 26px, 1.28): The value of a short fact (90 characters or fewer) on the plate, such as a city name. The largest type on the page and only appears on focus.
- **Title** (Schibsted Grotesk 500, 21px, 1.22, -0.005em): The record name at the top of the plate. Balanced wrapping.
- **Body** (Literata 400, 16px, 1.62): Longer record excerpts on the plate, line breaks preserved, hyphenated.
- **Body UI** (Schibsted Grotesk 400, 15px, 1.45): The page base.
- **Input** (Schibsted Grotesk 400, 16px): Typed text and the `Ask the notes` placeholder.
- **Chart Region** (Literata italic 400, 15px, 0.03em): One region name under each constellation.
- **Chart Name** (Schibsted Grotesk 400, 13px, 0.01em; focused 500, 14px): A star's own name on its leader.
- **Label** (Atkinson Hyperlegible 400, 14px, 0.04em): Floor status and floor words. Uppercase where the text is an instrument reading (`MIRROR`, `NEON`, `HANDS-FREE OFF`, `HOLD TO TALK`).
- **Label Meta** (Atkinson Hyperlegible 400, 13px, 0.02em to 0.04em): Plate head, plate key line, protocol note count. Numerals are tabular in the count; the count's number is set at 700 in bone.

### Named Rules
**The Three Faces Rule.** Literata reads, Schibsted works, Atkinson gauges. A string's job picks its face; never swap them for variety.

**The Uppercase Is A Reading Rule.** Uppercase is reserved for instrument readings on the floor and for the plate's `Close` control. Names, titles, regions and excerpts stay in their own case.

**The Local Type Rule.** Every face is a self-hosted woff2 under `viewer/vendor/fonts/`. No font CDN, because that host would fail the offline drill.

## Layout

The body is a two-row grid: the sky takes `minmax(0, 1fr)` and the floor takes a fixed 72px. Nothing scrolls at page level. The protocol plate (lockup at 236px wide, note count indented to sit under the wordmark) is pinned at the gutter in the upper left over the sky. The record plate is pinned at the gutter in the upper right, 380px wide, and caps its height to the sky so its body scrolls internally with a thin bone-dim scrollbar.

The floor is a two-column grid: a flexible left column holding the status line (22px row) over the input (30px row), and an auto right column holding the floor words, 22px apart, vertically centered across both rows. Column gap is 24px; side padding is the gutter.

Star names flip their leader toward open sky: if the space to the right (less the plate when it is open) cannot hold the label plus 56px, the leader turns left. Region names are placed each frame under the core of their own cluster, searched downward in 10px steps and sideways in 20px steps until they touch no star, no star name, and no other region.

The sky is seeded: every star starts near its region center from a hash of its group, key and id, so the same memory always draws the same chart.

**Under 800px wide** the gutter drops to 16px, the lockup to 176px, the floor words to 13px at 0.02em with a 10px gap, and the status line spans the full floor width above the input and words. When a star is focused the plate leaves its overlay position and becomes a grid row under the sky, splitting the space 54 to 46 so the sky keeps more than half the height. The status and input never leave the floor.

### Named Rules
**The Floor Never Moves Rule.** The 72px floor holds the status and the input at every width and in every state. Plates and skies rearrange around it.

## Elevation & Depth

The interface layer is completely flat: no `box-shadow`, no `backdrop-filter`, no radius on the plate. Separation comes from tone (void-lift on void) and from 1px bone-dim hairlines. All depth lives inside the WebGL sky: perspective, a far field of 1,600 non-interactive dust points at 1,500 to 3,100 units lerped between void and bone, and additive halos on the stars.

### Star Vocabulary
- **Rest:** an 8px-falloff halo (20px across; documents 20 to 30px by size; sessions 22px) at 50% in the category dye, additive, over a 2px core at 78%.
- **Hover:** halo to 74%, core to 100%, scale 1.18. The star's name appears on a leader.
- **Focus:** halo to 95%, core switches to star core, scale 1.5, a 13px-radius bone ring at 70% around it, and its name in the focus weight.
- **Links:** 1px. Same-region links at 30% bone. Cross-region bridges are invisible until they touch the focused or hovered star, then 62% bone.

### Named Rules
**The Flat Plate Rule.** Chrome is a flat rectangle with a hairline edge. Glow belongs to stars, never to UI.

## Shapes

Square corners everywhere in the interface. The only round forms are the 8px category dot in the plate head, the stars themselves, and the focus ring. Lines are 1px: the floor rule, the plate edge, the plate dividers, the input underline, the leaders (a 22px diagonal then a 10px horizontal shelf), and the 11px status separator. The input has no box, only an underline.

## Components

### Observatory Floor
Quiet, legible, always there.
- **Structure:** void ground, 1px bone-dim top rule, 72px tall, gutter padding.
- **Status line:** Label type in bone-dim. Readings are separated by a 1px by 11px bone-dim rule at 50% with 12px either side. Source reading first (`NEON`, or `MIRROR · 10 NOV` in fault red, with a title explaining why), then `VOICE not running`. A missing index reads `No notes indexed` in fault red. Truncates with an ellipsis rather than wrapping.
- **Planned, not built:** `LISTENING`, the heard words, `THINKING`, `SPEAKING`, the answer sentence on the floor (Literata 18px), and the brain and voice badge. These are specified in `SPARK_SOL_IMPECCABLE_DESIGN_SPEC.md` and are out of scope for this build.

### Floor Words
Controls written as words, not icons.
- **Style:** Label type in bone-dim, no background, no border, 6px vertical padding.
- **State:** `HANDS-FREE OFF` and `HOLD TO TALK` are `aria-disabled` with a not-allowed cursor and a title reading "Needs the voice server." The planned on state is `HANDS-FREE ON` in filament.

### Ask Input
- **Style:** transparent, no box, a single 45% bone-dim underline, square, 28px tall, bone text, bone-dim placeholder at full opacity.
- **State:** disabled in this build with a not-allowed cursor and a title reading "Answers wait for the server." The underline is about 2.3:1 on the void. That ratio counts only once the input is enabled. Do not copy it onto a control the operator can use.

### Record Plate
The real record, read like a card from a drawer.
- **Corner Style:** square (0px).
- **Background:** void lift, 1px bone-dim edge, no shadow.
- **Head:** 8px category dot, region name in bone, an optional `· kind` in bone-dim, and `Close` pushed right in uppercase bone-dim, turning bone on hover. A 35% bone-dim hairline beneath.
- **Body:** title, a meta line (`category / key · updated 6 Sept 2026`, middle-dot separated), then either the headline value for short facts or the Literata excerpt for longer records, then an optional source block under a 25% hairline.
- **Motion:** opens from 24px right with a 0.42s transform and 0.3s fade on `cubic-bezier(.16, 1, .3, 1)`; closes faster, 0.28s ease-in.
- **Under 800px:** becomes a row under the sky with only its top edge drawn.

### Chart Lettering (signature)
- **Region names:** Chart Region type in bone-dim at 84% (4.97:1 on the void), one per visible category, placed under the cluster core and never on a star or another label. Eased to 80% while any star is focused; the focused star's own region lifts to 100%.
- **Star names:** shown only for the focused star and the hovered (or keyboard-cursored) star, on a 1px bone-dim leader that flips toward open sky.
- **Focus ring:** a 13px-radius bone circle at 70% around the focused star.

### Protocol Plate
- The binding lockup raster (mark, `F.L.A.X.E.O.N` with the ember X, `SPARK SOL` between hairlines) at 236px (176px under 800px), with the live note count beneath in Label Meta: number in bold bone, the word in bone-dim.

### Sky Camera
- Idle yaw at autorotate speed 0.22, paused on any drag and resumed after 6 seconds without a focused star. Damped orbit, no pan, distance 30 to 1,400.
- A fly to a star takes 1.3s from overview and 0.9s between stars; closing returns to the fitted overview in 1.1s.
- Reduced motion: no idle rotation, zero-length flies, no plate or region transitions.
- Keyboard: the sky is a focusable region; arrows move a cursor through stars in region order, Enter opens, Escape closes. Interactive controls show a 1px bone outline offset 3px on focus.

## Do's and Don'ts

### Do:
- **Do** keep the void (#0c1224) as the page ground and the WebGL clear color, and let it carry the mood.
- **Do** use bone for content and bone-dim for readings, meta and hairlines; reach for reduced-alpha bone-dim when a divider must sit quieter than an edge.
- **Do** give every star its category dye, dim at rest, and reserve star core (#f4f0e6) for the one focused star.
- **Do** write controls as uppercase Atkinson words on the floor (14px, 0.04em), never as icon buttons or floating circles.
- **Do** keep the plate flat: void lift, 1px bone-dim edge, square corners, 380px wide on desktop.
- **Do** show a star's name only on focus, hover, keyboard cursor, or (once built) citation.
- **Do** respect reduced motion: stop idle yaw, cut flies, drop transitions.
- **Do** serve every font and script from `viewer/vendor/`.

### Don't:
- **Don't** use verdigris (#7dbea8) for anything except a local system that is actually acting.
- **Don't** let the family ember (#ff3b1f) leave the lockup raster, and don't paint the sky, floor or stars in Desk ember or Tempest gold.
- **Don't** add glass, backdrop blur, outer glow stacks, drop shadows or rounded cards to the chrome.
- **Don't** label every star on the idle sky or print instructions on it.
- **Don't** set status in a monospace face.
- **Don't** add a chat transcript column, a card grid, a left nav, a hamburger, a light theme, or helmet and visor chrome.
- **Don't** show a dye on the memory sky that means anything other than its category.
