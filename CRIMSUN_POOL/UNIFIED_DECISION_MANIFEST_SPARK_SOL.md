# UNIFIED DECISION MANIFEST
# Project: F.L.A.X.E.O.N — SPARK SOL Protocol
# Generated: 2026-11-10 | Understanding index: CRIMSUN_POOL/POOL_INDEX_*.md (same day)
# Experience index: CRIMSUN_POOL/EXPERIENCE_INDEX.md — 4 modules, 115 entries, ~13,076 tokens
# Understanding snapshot: FSA 366 entries; FSJS 625; FST 287 (header declares 12 — distrust totals); SYSTEM_DESIGN module; DOET 58 parsed (header declares 42)
# Audit: PASSED with 3 corrections — (1) did not inherit the older voice manifest's use of FSA RULE-024, which is about leaving a monolith when scale exceeds it; (2) TINY_SWORDS RULE-001 is Phaser-specific, so the graph-camera application is bridge B-01, not a direct citation; (3) sample-note placement is not FSJS AXIOM-071, which is about PII in caches.
# Session breadcrumbs at generation: 4 produced / 2 confirmations / 0 repeats
# Revision Log: v1 initial | v1.1: operator lockup binds the swirl mark and the ember X as the family letter only. Page live-color stays verdigris. Thin-ring prompt retired. | v1.2: first corpus is the real CrimSun allowlist in SPARK_SOL_CORPUS.md. Synthetic samples refused. Raw repos are a compile backlog, not stars. | v1.3: the first page reads the parent memory database (Neon, then long_term.json). Sky labels are one region name at rest, and a star name on focus, citation, or hover.
# Unified: expert-pipeline v2 + adaptation-growth CONSUME. One manifest. OpenSpec omitted — this is a whole protocol, not one named change.
# Sources read in full: Build-Jarvis-Fully-Offline-Prompt-Pack.pdf (18 pp, Nov 2026); Run-Jarvis-Fully-Local-Prompt-Pack.pdf (18 pp, Oct 2026); F.L.A.X.E.O.N persona.md charter; JARVIS_FOUNDATIONAL_EXPERIENCE.md (heading-form archaeology, absent from the experience index).

Every product string that the packs call Jarvis is SPARK SOL Protocol, a local protocol of F.L.A.X.E.O.N. The speakable wake is a short alias. The legal name stays on the plate.

---

## 0. POOL INDEX SUMMARY & MODULE SELECTION

| Module | Family | Why selected / near-miss | Read strategy |
|---|---|---|---|
| FUNDAMENTALS_SOFTWARE_ARCHITECTURE | Understanding | Style choice for one operator, one machine, three local engines | Extracted (master ledger, ~40k tokens) |
| FULL_STACK_JS_STRATEGIES | Understanding | Secrets stay off the page; backend is the security boundary; errors map to honest lines | Extracted |
| FULL_STACK_TESTING | Understanding | Pyramid vs the packs' live preflight. Count-mismatch warning: cite extracted entries only | Extracted |
| SYSTEM_DESIGN_FULLSTACK_PRODUCTION | Understanding | Single-machine baseline before any scale-out | Extracted (thin on this domain) |
| DESIGN_PSYCHOLOGY_NORMAN_DOET | Understanding | Status line, false feedback, discriminability from Desk and Tempest | Extracted (small; axioms read via extract-all) |
| EXCEL_WORKFLOW_HISTORY | Experience | Closest desktop-Python trail. "Done" that is not proven. `[NEVER_RESOLVED]` on MISTAKE-003 | Extracted HIGH + TIMELESS |
| TINY_SWORDS_LAST_STAND_HISTORY | Experience | TIMELESS single-owner rule for a view that also scales | Extracted |
| SUNNYSIDE_WORLD_HISTORY | Experience | Silent boot stall; UI placed in the wrong camera | Extracted HIGH |
| JARVIS_FOUNDATIONAL_EXPERIENCE | Experience (archaeology, not indexer-shaped) | Python 3.11, Ollama as the offline path, Whisper CUDA-then-CPU | Read in full |
| Prior FLAXEON voice manifests | Project law, not a pool module | VETO-R03: Whisper stays off the HUD Live microphone | Cited as prior manifest law |
| FULL_STACK_WEB_DEV_GUIDE | Near-miss, not selected | MERN/React/Mongo tutorial. This protocol forbids npm and a framework | Indexed, not extracted |
| React 19, Postgres, game-engine ledgers | Not selected | Wrong runtime. Phaser lessons used only where tagged TIMELESS and mechanism-level | — |
| SNHU / Sophia / Sampoerna | Not selected | Coursework. No decision here is a homework exercise | — |

Index warnings that changed this run: FST and DOET declare fewer entries than the parser found. Totals in those headers are untrusted. IDs inside FSA and FSJS are continuous, so citations do not need a chunk qualifier, and the chunk is still named where the extract carried one. JARVIS_FOUNDATIONAL_EXPERIENCE uses `### RULE-001` headings, so `build_experience_index.py` cannot see it. It was read directly and tagged as archaeology.

---

## 1. STACK DOMAIN GRAPH

```
  operator (voice or the bottom bar)
        │  WAV 16 kHz mono, or text
        ▼
  viewer/index.html          graph-data.js (served snapshot)
  one camera · one play()    note count read from GRAPH
        │  POST /hear /chat /tts /remember     never config.json
        ▼
  server.py :4700  bind 127.0.0.1 only
  stable persona prefix FIRST · notes and question LAST
  one door: commit_note()
        │
        ├── hear.py     faster-whisper 1.2.1 (Windows)   soft-import
        ├── voice.py    VoiceStudio :3900  VoxCPM2       soft-import
        └── brain shelf Ollama :11434/v1   urllib, no SDK
                notes/*.md  ← captures/ written only through commit_note()
                config.json stays in the project root, outside viewer/
```

Governing edges:

- Page → server: FSJS AXIOM-030. The page is not a security boundary. `config.json`, keys, and note files are not served.
- Server → Ollama / VoiceStudio: FSA RULE-060. These are remote plug-ins on loopback. Binding them to `0.0.0.0` would change the privacy characteristic. It is refused.
- Hear → chat → speak: one process, one characteristic set (FSA RULE-038). The latency budget is measured (FSA RULE-032). It is not a reason to split services (FSA RULE-040).
- Viewer camera: bridge B-01 (TINY_SWORDS MISTAKE-001's two-owner pattern, TIMELESS). `3d-force-graph` is the only camera owner.
- New notes: one server function and one viewer function. A second writer is the two-owner failure the Tiny Swords trail already paid for.

Driving characteristics, capped at three (FSA RULE-030):

1. **Privacy.** A local turn opens no host except `localhost` and `127.0.0.1`.
2. **Honesty.** A spoken "done" exists only when the code returned a receipt. Feedback shows the resulting state (DOET AXIOM-009, RULE-007).
3. **Simplicity of the local chain.** Stdlib server, soft-imported bays, one preflight that runs the live chain.

Performance is measured and printed. It is not allowed to evict those three.

---

## 2. ACTIVE AXIOMS

- **FSA RULE-038 (FUNDAMENTALS_SOFTWARE_ARCHITECTURE / chunk 7):** One characteristic set selects a monolith. ──► *Impact:* SPARK SOL is one Python process plus loopback engines, not a service mesh. ──► *Evidence:* DIRECT
- **FSA RULE-054:** Domain alignment without distributed-system cost selects a modular monolith. ──► *Impact:* `server.py` owns HTTP and the note door; `voice.py` and `hear.py` are modules. ──► *Evidence:* DIRECT
- **FSA RULE-059:** Shared core plus local customization selects in-process plug-ins. ──► *Impact:* voice and ears soft-import. The page still boots when either bay is absent. ──► *Evidence:* DIRECT
- **FSJS AXIOM-030:** The backend is the security boundary. ──► *Impact:* the viewer never receives `config.json` or an API key. ──► *Evidence:* DIRECT
- **FSJS TRAP-064:** Secrets placed where the frontend build can see them leak. ──► *Impact:* the Anthropic placeholder stays in root `config.json`. Grep of `viewer/` must be empty. ──► *Evidence:* DIRECT
- **FSJS AXIOM-036:** Third-party engines change without notice. ──► *Impact:* Ollama, VoiceStudio, and the graph library are pinned. "Latest" is not a configuration. ──► *Evidence:* DIRECT
- **DOET AXIOM-009 / RULE-007:** Feedback reports the resulting state. ──► *Impact:* the status line and the BRAIN/VOICE badge read what the server last did, not what the page hoped. ──► *Evidence:* DIRECT
- **DOET AXIOM-018:** The picture the operator sees stays simple while the mechanism stays complex. ──► *Impact:* one galaxy, one status line, one input. Engine ports stay off the page. ──► *Evidence:* DIRECT
- **DOET RULE-008:** A new object that sits beside an old one must be discriminable. ──► *Impact:* SPARK's void and filament are not the Desk ember (`#ff3b1f`) and not the Tempest gold (`#ffb300`). v1.1 exception: the X in the family wordmark is that ember, and it does not enter the sky or the status line. ──► *Evidence:* DIRECT, applied to sibling SOL protocols, exception pinned by the operator lockup
- **SYS AXIOM-002 (SYSTEM_DESIGN_FULLSTACK_PRODUCTION):** One machine running every component is the baseline, before any scale-out. ──► *Impact:* no second host, no database server. ──► *Evidence:* THIN — see GAP-01. The packs already require this; the entry only confirms the baseline exists in the pool.
- **JARVIS archaeology RULE-001 [TIER-0]:** This family's install target is Python 3.11. ──► *Impact:* the venv is 3.11. The machine already has 3.11.8. ──► *Evidence:* DIRECT on the archaeology file
- **JARVIS archaeology PROGRESS-001 [TIER-0] [TIMELESS]:** Ollama is the offline brain, selected by config. ──► *Impact:* the shelf's `local` entry is Ollama. Boot brain is `local`. ──► *Evidence:* DIRECT
- **TINY_SWORDS RULE-001 [TIER-0] [TIMELESS]:** In that repo the Phaser Scale Manager is the only scale and centering owner, because a second fit owner double-scales the view. ──► *Impact on SPARK:* recorded as bridge B-01, applied to the graph camera. The entry itself does not mention a force-directed graph. ──► *Evidence:* INFERRED via B-01
- **EXCEL MISTAKE-003 [TIER-0] [NEVER_RESOLVED] IMPACT-MEDIUM**, with **GROWN-004** still an open checkbox in that repo: a task list marked done while the files were uncommitted. ──► *Impact:* "done" on a SPARK phase means `preflight.py` exited 0 and its two summary lines were pasted. The bar is adopted because the home repo never closed it. ──► *Evidence:* DIRECT on the mistake; the grown bar is unmet at its source

---

## 3. ARCHITECTURAL DECISIONS

| Fork | Rule applied | Decision | Rejected | Why | Tier |
|---|---|---|---|---|---|
| Process shape | FSA RULE-038, RULE-054, SYS AXIOM-002 | Modular monolith on `127.0.0.1:4700` | Microservices, a second FLAXEON `QApplication` | One operator, one characteristic set. AGENTS.md already forbids a widget from a worker | DIRECT |
| Engines | FSA RULE-059, RULE-060 | Soft-imported bays. Ollama and VoiceStudio stay loopback processes | Importing them into `ui.py`; binding `0.0.0.0` | Remote plug-ins are accepted only on loopback. LAN would change privacy | DIRECT |
| Brain wire | Pack law + FSJS AXIOM-036 | OpenAI-style chat completions via `urllib`. `extra_body.reasoning_effort = "none"` merged into every body | An SDK; a "disable thinking" flag the 9B ignores | The packs recorded that only `reasoning_effort: none` stopped empty answers | DIRECT (pack) |
| Retrieval | Pack Prompt 01 | Keyword overlap, title weighted higher, top 6 notes | Embeddings, a vector database | The pack's brain is the overlap scorer. Embeddings are a gap, not a silent upgrade | DIRECT (pack) / GAP-02 |
| Prompt shape | Pack Prompt 04 + persona.md | Stable prefix under 300 words, first in the request. Persona is Flaxeon's needle-and-ledger, cut to one sentence plus the facts | British butler, "sir", "Hello, sir" | The charter is this product's voice. The pack's budget and receipt laws stay | RESOLVED CONFLICT-01 |
| Wake | Pack hearing law, renamed | "Spark", "hey Spark", "Flaxeon", "hey Flaxeon". Anything else is discarded and never logged | The full string "F.L.A.X.E.O.N's SPARK SOL Protocol" as the wake | A wake has to be sayable in one breath. The plate keeps the full name | INFERRED — GAP-03 names the missing pool entry |
| Page | Pack Prompt 01 | One HTML file. `3d-force-graph` 1.80.2 vendored before the offline claim | React, npm, a build step | The pack forbids the toolchain. FSJS React state rules lose on specificity | RESOLVED CONFLICT-02 |
| Notes door | Pack Prompt 05 + TINY_SWORDS RULE-001 | `commit_note()` on the server, `addNote()` on the page | A second writer, a reload, writing into the Neon `persona` document | Writing a file is not the same as indexing it. The charter document is a different store | DIRECT |
| Proof | Run pack Prompt 07 + FST RULE-063 + EXCEL GROWN-004 | `preflight.py` hits the live chain. Unit tests sit under it. Voice and ears missing are WARN | A mock-only suite that can pass while the chain is dead | Hardware and loopback engines are the product. FST RULE-020 still caps how many UI tests exist | RESOLVED CONFLICT-03 |
| HUD mic | Prior manifest VETO-R03 | SPARK's ears use this page's `getUserMedia` only | Attaching Whisper to the Desk Live microphone | That veto is still in force on the HUD | DIRECT (project law) |
| Which pack wins | Nov 2026 build pack vs Oct 2026 run pack | Windows voice is VoxCPM2. Memory table is the November one. Preflight is kept from October because November folded the drill and dropped the harness | Apple-only CSM as the Windows engine; dropping preflight | This machine is Windows. A proof the later pack forgot is still a proof | INFERRED |

**Conditional:** IF the operator later types a real Anthropic key into `config.json` THEN the `claude` shelf uses the Messages API shape, and `drill.py` must fail naming `api.anthropic.com`. IF the key is still the placeholder THEN "switch to Claude" speaks one dry line and stays local. The key is typed into the file by the operator. The chat never asks for it.

**RESOLVED CONFLICT-01:** Pack Prompt 04 ("dry British butler", address "sir", boot "Hello, sir.") vs `persona.md` (Flaxeon, needle then ledger, no pet names, she/her for Flaxeon). Winner: the charter, on specificity to this product. The pack still wins the budget: one witty-or-dry sentence plus the facts, under 300 words, stable prefix first, no invented source, no "done" without a receipt, cost of a local turn is electricity. Loser kept so a later session does not restore the butler costume.

**RESOLVED CONFLICT-02:** FSJS RULE-077 through RULE-082 (useState, context, Redux, an external store) vs the pack's single page with no npm. Winner: the pack, on specificity. Viewer state is one `GRAPH` array plus a small session object in the page. Loser kept so nobody "modernizes" this into a React app.

**RESOLVED CONFLICT-03:** FST RULE-020 (about 10× unit, 5× service, 1× UI) vs the run pack's law that the failures which hurt are the ones where every unit test passes and the live chain is dead. Winner: both, split by layer. Unit tests own the pure functions (chunking, wake strip, keyword score, mute gate, note door). `preflight.py` owns the live chain and is the exit gate. A UI-only suite is refused (FST RULE-004, TRAP-012).

**RESOLVED CONFLICT-04:** The November buying guide says a headless machine is talked to from any browser on the network. Prompt 01 binds `127.0.0.1` and serves only `viewer/`. Winner: the bind. Privacy is characteristic 1. A household LAN bind is a later, explicit decision (GAP-04), not the default.

---

## 4. ARCHITECTURAL VETOES

- **VETO-01 [BLOCK | FSJS TRAP-064 + AXIOM-030]:** The viewer does not contain `config.json`, an API key, a note file, or a CDN URL once the drill phase has landed. The server refuses to serve anything outside `viewer/`.
- **VETO-02 [BLOCK | pack hearing law]:** No browser speech recognition. That API sends audio to a cloud. Ears are Whisper on this machine, or the push-to-talk path through `POST /hear`.
- **VETO-03 [BLOCK | prior voice manifest VETO-R03]:** Whisper does not attach to the Desk HUD Live microphone. SPARK listens only through the protocol page.
- **VETO-04 [BLOCK | FSA RULE-060 + CONFLICT-04]:** The server does not bind `0.0.0.0`.
- **VETO-05 [BLOCK | TINY_SWORDS MISTAKE-001 IMPACT-HIGH, pattern via B-01]:** The page does not add a second camera, a CSS scale on the graph canvas, or a second function that writes notes.
- **VETO-06 [BLOCK | pack voice law]:** Playback is sentence-packed chunks of about 170 characters. The first chunk is not shortened to start sooner. One function, `play()`, owns audio, and it returns immediately when `?mute=1` is set.
- **VETO-07 [BLOCK | pack character law + EXCEL GROWN-004]:** The model and the implementer do not say an action happened unless a receipt came back. "Done" on a phase means the named test or `preflight.py` was run.
- **VETO-08 [BLOCK | persona.md + CONFLICT-01]:** The persona block does not restore "Jarvis", "sir", or the butler bio. The string Jarvis does not ship in source, UI, or the voice-profile name.
- **VETO-09 [WARN | FSA RULE-059]:** Voice and ears missing must not crash boot. They are WARN in preflight. The page falls back to the browser speech synthesizer and the badge reads `VOICE browser`.
- **VETO-10 [WARN | DOET RULE-011]:** Do not add live web research, tools, or a second galaxy view in this build. The paradox of technology spends the 300-word budget. Research stays on the honest list as a feature this protocol does not have.
- **VETO-11 [WARN | DOET TRAP-001]:** The status line, the mute state, and the badge stay visible as instrument readings. A cinematic void does not hide them.
- **VETO-12 [OBSERVE | SUNNYSIDE MISTAKE-006 IMPACT-HIGH]:** Screen-space type (status, input, plate) stays in the page, not parented to the rotating 3D scene.

---

## 5. CROSS-MODULE INFERENCE MAP

| Inference | Contributing entries | Why it holds here |
|---|---|---|
| The turn is a pipeline inside one process: hear, score, complete, speak. Stages are not separate deployables | FSA RULE-038, RULE-040, RULE-058 | Splitting them adds the latency the local brain already spends, and synchronous calls across different speeds fail |
| Keyword top-6 plus a 300-word prefix is the caching strategy. A prompt cache product is not required | Pack stable-prefix law; FSJS AXIOM-133 | A cache that can go stale is how a note written this minute disappears from the next answer. The live index is the consistency mechanism |
| The badge is a forcing function for the system image | DOET AXIOM-003, AXIOM-009; pack badge law | Operators will trust a silent success. The badge shows the brain and the voice that actually answered, for 5 seconds, then hides |
| Sample notes, if generated, are labeled synthetic and live under this protocol's `./notes`, never in the Neon persona document | persona.md (charter is its own document); pack sample-note instruction | The charter is identity. A demo corpus is a different folder. AXIOM-071 was considered and does not say this |

---

## 6. POOL GAPS

- **GAP-01:** System-design coverage of a loopback LLM plus a local TTS daemon is one baseline axiom. ──► *Resolution:* the packs are the authority for ports, models, and the drill. Ingest a local-LLM serving source later if a second protocol needs it.
- **GAP-02:** No selected entry compares keyword overlap with embeddings for a few hundred markdown notes. ──► *Resolution:* ship the pack's scorer. An embeddings spike waits until preflight's think-time is the bottleneck on this machine.
- **GAP-03:** No pool entry on wake-word aliases versus a legal product name. ──► *Resolution:* breadcrumb B1. Confirm after one day of real speech, the same way the packs say to tune `SILENCE_MS` and `FINISH_MS`.
- **GAP-04:** No entry on a safe household bind (Tailscale, mDNS, TLS) for a headless mini. ──► *Resolution:* stay on `127.0.0.1` until that spike is its own change.
- **GAP-05:** VoiceStudio and Ollama versions move. The pool has no pin table. ──► *Resolution:* `viewer/vendor/VERSIONS.txt` plus a root `VERSIONS.txt` record the proven versions after Install 01–03. Do not float them afterward.
- **GAP-06:** Experience index still cannot see `JARVIS_FOUNDATIONAL_EXPERIENCE.md`. ──► *Resolution:* recompile that file into dash-bold entries so the next index counts it.

---

## 7. THE VERTICAL IMPLEMENTATION SEQUENCE

Maps 1:1 onto the TDD phases.

**PHASE 1 — STEEL THREAD.** Indexer, server, galaxy, `/chat`, single camera, single note-score function. Exit gate: a real `/chat` prints the answer and the seconds. Graph node count is on screen from `GRAPH`, not a hardcoded number. Unit tests for scoring, ids, and the mute gate exist even though voice is not wired. CDN use, if any, is written on the honest list the same day. (FSA RULE-036 testability. EXCEL GROWN-004.)

**PHASE 2 — MUTATION AND THE BAYS.** `voice.py`, `hear.py`, `commit_note()`, live index, sentence chunks, wake strip, finish window. Exit gate: a capture is retrievable by the next `/chat` without rerunning `build.py`. A failed write is spoken. `?mute=1` stays silent. (Pack laws. VETO-05, VETO-06, VETO-09.)

**PHASE 3 — PRESENTATION.** The design spec's first viewport: void, one status line, bottom bar, node plate, birth pulse, cluster light, badge. Exit gate: an operator can see who is talking, which note answered, and that small talk did not move the camera. (DOET AXIOM-009, AXIOM-018, VETO-11, VETO-12.)

**PHASE 4 — HARDENING.** Vendor `3d-force-graph@1.80.2`. `drill.py`. `preflight.py` with the latency budget. Persona token count printed before and after. Exit gate: local drill host list is empty; preflight prints both lines and exits 0; cloud mode fails the drill on purpose and names `api.anthropic.com` when a real key is present. (FST RULE-063. VETO-01, VETO-07.)

---

## 8. SKILL COMMAND SUGGESTIONS

- **tdd-generator** — already applied this session. The TDD in this folder is the build contract.
- **impeccable** — when implementation of the page starts. The design spec is the pinned brief. The galaxy world is already chosen. Do not reopen a visual-world tournament unless the operator rejects that spec.
- A later **pool-ingestion** of a local-LLM serving source only if GAP-01 starts blocking a second protocol.

---

## 9. PROMPT-READY CONSTRAINT BLOCK

```
PROJECT CONSTRAINTS (Pool: FSA, FSJS, FST, SYSTEM_DESIGN, DOET;
Experience: EXCEL_WORKFLOW, TINY_SWORDS, SUNNYSIDE, JARVIS archaeology;
Manifest: 2026-11-10 SPARK SOL v1):

AXIOMS:
- One process, loopback only, modular monolith with soft-imported voice and ears.
- Backend is the security boundary. viewer/ is static and keyless.
- Feedback shows the state that resulted, including which brain and which voice.
- Python 3.11. Boot brain is local Ollama. Desk HUD mic is not SPARK's mic.
- Flaxeon charter voice, pack budget: under 300 words, stable prefix first, one sentence plus the facts, receipt or silence.

VETOES — BLOCK:
- No Jarvis string, no butler, no "sir", no browser speech recognition.
- No bind to 0.0.0.0. No config or key under viewer/. No CDN left in the shipped page.
- No second camera, no second note writer, no Whisper on the HUD Live mic.
- No shortened first audio chunk. No "done" without preflight or the named test.
- Mute lives inside the one play() function.

VETOES — WARN:
- Missing voice or ears warn, they do not crash boot. Badge must show the browser voice.
- Do not add web research or tools in this build.
- Do not hide the status line for the sake of the void.

DECISIONS MADE:
- Windows engine VoxCPM2; Mac block exists and is not selected on this machine.
- Retrieval is keyword overlap, top 6, title-weighted.
- Wake aliases: Spark, hey Spark, Flaxeon, hey Flaxeon.
- November pack wins hardware and voice. October pack's preflight stays.
- Notes live in this protocol's notes directory, not in the persona document.

LOOP: log breadcrumbs at every novel fork. "Done" means preflight passed.
```

## 10. OPEN SPEC

Omitted. A six-phase protocol is not one nameable change. Slice OpenSpec proposals from the TDD phases when implementation starts.

---

## Growth half — carried forward, vetoes, bridges, breadcrumbs

### Carried-forward progress

- **PROGRESS-001 (TINY_SWORDS) [TIER-0] [TIMELESS] (confirmed across that repo's design trails):** Four layers, the view does not own the rules. ──► *Applied here as:* the page mirrors `GRAPH` and session status. Scoring, writes, and engine calls stay in Python.
- **PROGRESS-001 (JARVIS archaeology) [TIER-0]:** Config-selected Ollama beside a cloud brain. ──► *Applied here as:* the shelf. Boot stays local.
- **PROGRESS-002 (JARVIS archaeology) [TIER-0]:** Whisper tries CUDA, then CPU int8, without aborting. ──► *Applied here as:* `hear.py` records the device it actually loaded. A CPU fallback is a status fact, not a crash.
- **PROGRESS-005 (TINY_SWORDS) [TIER-0] [TIMELESS]:** Missing art is a placeholder, and the loop is still provable. ──► *Applied here as:* missing voice engine falls back to the browser synthesizer and is labeled.

### Adaptive vetoes already in §4

VETO-05 blocks TINY_SWORDS MISTAKE-001. VETO-07 blocks treating EXCEL MISTAKE-003's "all boxes checked" as done. VETO-12 observes SUNNYSIDE MISTAKE-006.

### Bridges

| Bridge | Experience | rel. | Understanding | Effect |
|---|---|---|---|---|
| B-01 | TINY_SWORDS RULE-001 single owner | agrees with | FSA RULE-022 (connascence stays inside the boundary) | Camera and note door confidence raised to CONVERGENT |
| B-02 | EXCEL GROWN-004 done means the artifact exists | agrees with | FST RULE-063 hardware needs a real chain, not only the pyramid bottom | Preflight is the exit gate |
| B-03 | SUNNYSIDE MISTAKE-005 silent boot stall | agrees with | DOET TRAP-004 false feedback | A bay that failed to import must show on the status line at boot |
| B-04 | Prior voice VETO-R03 | does not contradict | FSA RULE-024 | RULE-024 is about scale, not microphones. No contradiction to resolve. The old citation was wrong; it is not reused |

No unresolved contradiction bridge.

### Breadcrumb log (compiler-ready, [TIER-0])

**B1 — RULE draft.** Fork: the packs' wake word is the product name "Jarvis"; the replacement name is a sentence. Decision: wake aliases are "Spark", "hey Spark", "Flaxeon", "hey Flaxeon". The plate reads F.L.A.X.E.O.N · SPARK SOL. Because a wake that cannot be said will be whispered past, and the hearing law discards utterances that miss the alias. Suggested impact: HIGH. Source: this session, both packs' Prompt 03 plus the rename instruction.

**B2 — RULE draft.** Fork: November pack merges switch and drill and drops the standalone preflight; October pack has `preflight.py` as the definition of done. Decision: keep both the November Windows voice table and the October preflight. Because this machine is Windows, and a live chain with no harness is how EXCEL MISTAKE-003 happens. Suggested impact: HIGH. Source: this session.

**B3 — confirmation, not a new entry.** TINY_SWORDS RULE-001 still holds: one camera owner, one note door. Do not duplicate the entry.

**B4 — confirmation, not a new entry.** persona.md remains the charter. SPARK SOL speaks in that register inside the pack's 300-word budget. Do not duplicate the charter into a second persona file inside this protocol; the prefix in `server.py` is a short projection of it.

Tally: 4 breadcrumbs written, 2 of them confirmations, 0 logged mistakes repeated. No Growth Alert.

Offer: append B1 and B2 to a new `SPARK_SOL_EXPERIENCE.md` in this folder when the first implementation session starts. They are drafts until a later compile pass assigns sequential IDs beside the archaeology module.
