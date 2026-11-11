# TDD — F.L.A.X.E.O.N SPARK SOL Protocol

**Status:** context baseline for implementation. Decisions live in `UNIFIED_DECISION_MANIFEST_SPARK_SOL.md` (2026-11-10). The page's visual contract lives in `SPARK_SOL_IMPECCABLE_DESIGN_SPEC.md`.

**What this is.** A local protocol that turns a folder of markdown notes into a 3D galaxy, answers only from those notes, speaks with a cloned voice, and hears through Whisper on the same machine. The packs this replaces called that system Jarvis. Here the product is F.L.A.X.E.O.N's SPARK SOL Protocol. It is a sibling process to the Desk HUD and to TEMPEST SOL. It does not create a Qt widget and it does not attach to the HUD Live microphone.

**Assumptions, stated.**

- The operator's machine is Windows, the same host this document was written on, with Python 3.11.8 available. Memory size and GPU are not yet measured. The floor brain is `qwen3.5:9b`. A larger tag is a config change after Install 01's proof, not a rewrite.
- The first page reads the parent F.L.A.X.E.O.N memory database. Neon is canonical, through the parent's `memory/neon_store.py`. The local mirror is the parent's `memory/long_term.json`. The connection string stays in the parent's `config/api_keys.json` and is never copied here or sent to the browser. The markdown allowlist is a later index. New captures still go to this protocol's `notes/captures/`. The persona document stays a document in that store. It is not a second database.
- VoiceStudio and Ollama are installed and proven before Phase 1's `/chat` proof is treated as final. The server still boots if they are absent.
- The November 2026 pack supplies the hardware table, the Windows voice engine, and the combined switch-and-drill. The October 2026 pack supplies `preflight.py`. Both were read in full.

---

## TDD SECTION 1 — SYSTEM ARCHITECTURE OVERVIEW

### 1.1 Architectural Pattern

**Modular monolith with two soft-imported bays, talking to loopback engines.**

`server.py` is the core. It serves `viewer/`, scores notes, calls the brain, and is the only writer of new notes. `voice.py` and `hear.py` are plug-ins imported inside try/except so a missing wheel does not kill the process. Ollama (`127.0.0.1:11434`) and VoiceStudio (`127.0.0.1:3900`) are separate processes reached with `urllib`. They are remote plug-ins that happen to live on the same machine. They are not services we deploy, and they are not imported into the Desk HUD.

This shape won because the driving characteristics are privacy, honesty, and a chain one person can test. One operator and one characteristic set do not need a network of services. A React application and an npm build were rejected because the protocol is one HTML file plus the Python standard library, with `faster-whisper` as the single allowed third-party import inside `hear.py`.

The turn itself is a pipeline that stays inside that process: capture audio, transcribe, strip the wake alias, score notes, complete, chunk the answer, speak. Stages share one failure domain on purpose. Splitting them would add the latency a local brain already spends.

### 1.2 High-Level Component Diagram

```
 OPERATOR
   │  speech in the room, or text in the bottom bar
   ▼
 ┌──────────────────────────────────────────────────────┐
 │ viewer/index.html                                     │
 │  galaxy (3d-force-graph 1.80.2, one camera)          │
 │  status line · bottom input · node plate · badge    │
 │  play()  ← the only function that emits sound       │
 │  addNote() ← the only function that births a star   │
 └───────────────┬──────────────────────────────────────┘
                 │  HTTP 127.0.0.1:4700
                 │  POST /hear  /chat  /tts  /remember
                 │  GET  /health /drill/connections
                 ▼
 ┌──────────────────────────────────────────────────────┐
 │ server.py                                             │
 │  persona prefix (stable, first, <300 words)          │
 │  keyword score → top 6 → chat completions            │
 │  commit_note() ← the only note writer                │
 │  voice routes checked BEFORE the brain               │
 │  outbound HTTP wrapper → host log                    │
 └───┬──────────────┬──────────────┬────────────────────┘
     │              │              │
     ▼              ▼              ▼
 hear.py        voice.py       Ollama :11434
 faster-whisper VoiceStudio    model from the shelf
 large + small  :3900 VoxCPM2  boot_brain = local
     │              │
     ▼              ▼
 notes/*.md     WAV cache on disk
 captures/      keyed by text+profile hash
 graph-data.js  (rewritten only by commit_note / build.py)
 config.json    PROJECT ROOT. Never inside viewer/
```

Subsystems on this diagram: indexer (`build.py`), server, viewer, brain shelf, voice bay, hearing bay, note door, drill, preflight. The Desk HUD and TEMPEST are outside the box. They may later GET `127.0.0.1:4700`. This TDD does not build that link.

### 1.3 Data Flow Topology

1. **Index, once and on each capture.** `build.py` walks the allowlist for `.md`, skipping any path segment named `chunks`, `_build_snhu`, `node_modules`, or `venv`. Each file becomes a node: numeric `id` equal to its index, `label` from the filename, `pool` the allowlist root (this is the color), `group` the first directory under that root whose name is not `chunk_modules` (this is the neighborhood), `excerpt` of about 700 characters. The layout clusters each `group` inside its `pool`. The plate shows both names. A link exists when one note mentions another's title or they share a `[[wikilink]]`. The file written is `viewer/graph-data.js` as `const GRAPH = {nodes, links}`.
2. **A turn enters** as text from the input bar, or as a 16 kHz mono 16-bit WAV from the page. The browser encodes the WAV. There is no ffmpeg in the page.
3. **Hearing.** With the hands-free toggle on, the small model runs first. A leading alias (`spark`, `hey spark`, `flaxeon`, `hey flaxeon`, case-insensitive) is stripped. The remainder goes to the large model, then to `/chat`. An alias with nothing after it speaks the boot attention line and holds the next utterance as the command. Audio with no alias is discarded: not logged, not posted. Push-to-talk skips the small model. While SPARK is speaking, the page listens only for "stop" and "wait", at a raised loudness threshold.
4. **Routes before the brain.** A voice-route table matches the utterance first. Routes cover local voice, browser voice, switch local, switch big, switch Claude, which brain, go local, go cloud, and the remember prefixes. A matched route never spends a chat completion.
5. **Chat.** The server scores every note by keyword overlap, weights a title match higher, takes six. The request body is OpenAI-style chat completions. The system message is identical on every turn and is first. Retrieved notes, the date, and the question come after it. `extra_body` from config is merged into the body, including `reasoning_effort: "none"`. `max_tokens` starts at 600. An empty `content` with `finish_reason` `"length"` retries once with a larger budget. The response is `{"answer", "nodes"}` where `nodes` are indexes. A short server-side history supports follow-ups. The model is instructed to say, plainly, when the notes do not cover the question.
6. **Proof on the galaxy.** If the question was about the notes and one to three nodes were used, the camera flies to the top source and opens its plate while the answer plays. Four or more nodes light the cluster and the camera stays wide. Small talk does not move the camera. That decision happens before any camera call. The idle sky draws one faint region name per region and no per-star labels. A star's name is drawn when that star is focused, cited by the answer, or under the cursor.
7. **Speech.** The answer is split on sentence boundaries into chunks of about 170 characters. Chunk one is requested, played, and chunk two is fetched during playback. A chunk is never cut inside a sentence, and chunk one is not made shorter to start faster. `POST /tts` is capped at 600 characters. WAVs are cached by a hash of text plus profile. Every ten idle minutes the bay renders "Standing by." and discards the audio so the engine stays warm.
8. **Remember.** Phrases that start with "remember that", "note to self", "don't let me forget", or "log this" call `commit_note()`. That function writes the markdown file under `notes/captures/`, appends the node to `graph-data.js`, inserts it into the live search index, and returns the index. The page's `addNote()` births the star at the most related existing node, pulses, and flies the camera. The next `/chat` can retrieve it without `build.py`. A failed write is spoken.
9. **Switch.** Runtime only. Restart reads `boot_brain`, default `local`. A swap confirmation is spoken by the destination brain. An unloaded Ollama tag speaks one waiting line while it loads. A cloud request with no key, or with the network absent, speaks one line and does not pretend.

### 1.4 State Management Contract

| State | Owner | Mutated through | Seen by |
|---|---|---|---|
| Note corpus on disk | `commit_note()` and `build.py` only | Those two. `build.py` is the full rebuild. `commit_note()` is the incremental door | Next `/chat` via the live index; the page via `addNote()` or a reload |
| `viewer/graph-data.js` | Same door | Atomic replace of the JS file | The page reads `GRAPH` at load. Live births do not reload |
| Live search index | Server process | `commit_note()` after the file hits disk | `/chat` of this process. A restart rebuilds from disk |
| Chat history | Server process, bounded | `/chat` appends | Follow-up turns. Not written to the notes |
| Active brain and voice | Server process | Route handlers | `GET /health` and the badge. Restart restores `boot_brain` |
| Playback | `play()` in the page | `play()` | Status line: speaking. `?mute=1` makes `play()` return before any audio node |
| Mic session | The page | `getUserMedia` in this document only | Status line: listening, heard text |
| Camera | The `3d-force-graph` instance | Fly, cluster-light, and idle rotation helpers | The canvas. CSS does not scale or center a second time |
| Secrets | `config.json` at the project root | The operator, in an editor | Server only. The static handler cannot see the parent directory |

There is no React store, no `localStorage` replica of the notes, and no second in-memory graph that can drift from `graph-data.js`. The page holds a mirror. The server holds the searchable index. Disk is the corpus.

---

## TDD SECTION 2 — TECHNOLOGY STACK & DEPENDENCY MATRIX

| Layer | Technology | Version | Justification |
|---|---|---|---|
| Language | Python | 3.11.x (this machine: 3.11.8) | Family install target. `faster-whisper` 1.2.1 supports it. Do not use 3.14 |
| Server | `http.server` + `urllib` | stdlib of that 3.11 | Pack law: no SDK. The same completion function retargets by `base_url`, `model`, and `api_key`, except Anthropic, which has its own builder beside it |
| Indexer | `build.py` | stdlib only | The galaxy has to be rebuildable with nothing installed beyond Python |
| Page | One HTML file, no bundler | — | Pack law. Vendored script tags |
| Galaxy | 3d-force-graph | **1.80.2** (npm, 5 Nov 2026, MIT) | Pinned. Downloaded into `viewer/vendor/`. The `three` build it ships is recorded in `VERSIONS.txt` from the package that was actually saved, not guessed |
| Brain | Ollama, OpenAI-compatible `/v1/chat/completions` | Pin the version that passes Install 01 into root `VERSIONS.txt` | Floor tag `qwen3.5:9b`. `reasoning_effort: none` on every local body |
| Voice | VoiceStudio on `127.0.0.1:3900` | Pin after `/health` succeeds | Windows engine `voxcpm2`, model id `voxcpm2`, Apache-2.0. Profile name `Spark`. Mac block `mlx-community/csm-1b-8bit` is present and unselected |
| Ears | faster-whisper | **1.2.1** | Windows and Linux path. Large `large-v3-turbo`, wake size `small`. Both loaded once at boot and warmed on one second of silence |
| Audio decode pin | PyAV (`av`) | **`av>=18,<19`**, prefer `av==18.1.0` | `faster-whisper` 1.2.1 still passes `metadata_errors` to `av.open`. PyAV 19 removed that argument (September 2026). A plain `pip install faster-whisper` pulls a broken pair |
| Tests | pytest | 8.x | Unit tests for pure functions. `preflight.py` is a script, not a pytest module, because it must hit live ports |
| Config | `config.json` at project root | — | Never inside `viewer/` |

**Memory floor, from the November pack, applied as config comments rather than code branches.** 16 GB comfortable brain: `qwen3.5:9b` (~6 GB). 32 GB: Qwen 3.8 27B, with the 9B kept for chatter. Leave about 30 percent of memory free for context, voice, and Whisper. A model that "fits" with 2 GB spare does not fit.

**Dependency risk.**

- `faster-whisper==1.2.1` plus unpinned PyAV is a known break. The pin above is the mitigation. A future faster-whisper release that contains the September 2026 fix may relax `av<19`. Until that release exists, the pin stays.
- VoiceStudio's Windows installer is unsigned. The install script checks release checksums. The default voice pack inside the app is non-commercial. The protocol selects `voxcpm2` on every boot with `POST /engines/select` so the default cannot sneak back.
- Ollama and VoiceStudio have no pool pin. They are recorded after the proof commands, then frozen.
- `3d-force-graph` 1.80.2 is MIT and had no published vulnerabilities on the day this TDD was written. It still gets vendored. A CDN script is an outbound host, and the drill would fail.
- No other high-risk dependency is in the core. The server does not take an OpenAI SDK, a web framework, or a database driver.

---

## TDD SECTION 3 — COMPONENT INTERFACE SPECIFICATIONS

Language is Python 3.11 for everything except the page, which is specified as the functions the single HTML file must contain. Types are real. Exceptions are caught at the HTTP boundary and returned as JSON. Libraries do not raise out of `run`-style entry points. A bay that failed to import is reported by `/health`, not by a stack trace in the page.

### Interface: config

```python
# config.json at the project root. Server refuses to serve it.
# notes_dir is an absolute path or a path relative to the project root.

{
  "notes_roots": ["<allowlist paths from SPARK_SOL_CORPUS.md>"],
  "captures_dir": "./notes/captures",
  "boot_brain": "local",
  "brain": {
    "base_url": "http://127.0.0.1:11434/v1",
    "model": "qwen3.5:9b",
    "api_key": "ollama",
    "extra_body": {"reasoning_effort": "none"}
  },
  "brains": {
    "local": {"base_url": "http://127.0.0.1:11434/v1", "model": "qwen3.5:9b",
              "api_key": "ollama", "extra_body": {"reasoning_effort": "none"}},
    "big": {"base_url": "http://127.0.0.1:11434/v1", "model": "",
            "api_key": "ollama", "extra_body": {"reasoning_effort": "none"}},
    "claude": {"base_url": "https://api.anthropic.com", "model": "claude-opus-5-5",
               "api_key": "PUT-YOUR-KEY-HERE"}
  },
  "voice": {
    "url": "http://127.0.0.1:3900",
    "engine": "voxcpm2",
    "model_id": "voxcpm2",
    "profile": "Spark",
    "language": "en"
  },
  "hearing": {"model": "large-v3-turbo", "wake_model": "small"}
}
```

`load_config(path: Path) -> dict` raises `ConfigError` if the file is missing or the `brain` object has an empty `model`. It does not print the key.

### Interface: Indexer (`build.py`)

```python
@dataclass(frozen=True)
class NoteNode:
    id: int
    label: str
    pool: str
    group: str
    excerpt: str
    path: str

def scan_notes(notes_dir: Path) -> tuple[list[NoteNode], list[tuple[int, int]]]:
    """Every .md file. id == index in the returned list. Links are (source_id, target_id)."""

def write_graph(nodes: list[NoteNode], links: list[tuple[int, int]], dest: Path) -> None:
    """Writes viewer/graph-data.js. Replaces the file. Does not touch config.json."""
```

`scan_notes` skips nothing silently. An unreadable file is reported on stdout and omitted, and the count of omitted files is part of the script's exit summary.

### Interface: Brain

```python
@dataclass
class ChatResult:
    answer: str
    nodes: list[int]
    seconds: float
    brain_name: str
    model: str

def complete(brain: dict, system: str, history: list[dict], user: str,
             max_tokens: int = 600) -> str:
    """OpenAI-style for Ollama. Messages API for base_url containing api.anthropic.com.
    Merges brain['extra_body'] into the JSON body. Retries once if content is empty
    and finish_reason == 'length'. Raises BrainError on transport failure.
    Never logs the api_key."""

def score_notes(question: str, nodes: list[NoteNode]) -> list[int]:
    """Keyword overlap. Title match outweighs body match. Returns up to 6 ids,
    highest score first. Empty question returns []."""

def chat(question: str) -> ChatResult:
    """Routes first. Otherwise scores, completes, appends history, returns indexes used."""
```

The persona block is one commented constant at the top of `server.py`, `PERSONA`. It is the Flaxeon projection: short, dry, geological, one sentence plus the facts, address nobody as "sir", never claim an action without a receipt, say when the notes do not cover it, and answer "electricity" when asked what a local turn costs. Control tags live in that same block. `len(PERSONA.split()) < 300` is a unit test.

Stable order of the system message: `PERSONA`, then the control-tag list. The user message carries the date, the six excerpts, and the question.

### Interface: Voice bay (`voice.py`)

```python
def select_engine(cfg: dict) -> str:
    """POST /engines/select {family:'tts', backend_id, model_id}. Returns profile id
    looked up by cfg['voice']['profile'] from GET /profiles. Raises VoiceUnavailable
    if /health does not answer within 1.0 second."""

def synthesize(text: str) -> tuple[bytes, str]:
    """Returns (wav_bytes, header_value). header_value is 'local:Spark' or, when the
    caller catches VoiceUnavailable and uses the browser, the page sets 'browser'.
    Caps text at 600 characters. Serves the disk cache when the hash hits."""

def keep_warm(stop: threading.Event) -> None:
    """Every 600 seconds of idle, synthesize 'Standing by.' and discard the bytes."""

def split_chunks(answer: str, limit: int = 170) -> list[str]:
    """Sentence-packed. No chunk breaks inside a sentence. The first chunk is not
    shorter than the others on purpose."""
```

HTTP: `POST /tts` body `{"text": str}` → `200 audio/wav` with header `X-Spark-Voice: local:Spark`, or `503` with `{"fallback": "browser"}` when `/health` missed the one-second budget. The process does not crash.

### Interface: Hearing bay (`hear.py`)

```python
SILENCE_MS = 700
FINISH_MS = 900
MIN_UTTERANCE_MS = 300

def load_models(cfg: dict) -> None:
    """Once per process. CUDA if present, else CPU int8. Warm each model with
    one second of silence. Records the device string for /health."""

def transcribe(wav: bytes, which: str) -> tuple[str, float]:
    """which is 'wake' or 'command'. Returns (text, seconds)."""
```

HTTP: `POST /hear` body is the WAV bytes → `200 {"text": str, "seconds": float}`.

Page constants of the same names govern the end of an utterance and the finish window. More speech inside `FINISH_MS` appends and restarts the timer. The page discards clips under `MIN_UTTERANCE_MS`.

Wake aliases, after lowercasing and collapsing whitespace: `spark`, `hey spark`, `flaxeon`, `hey flaxeon`.

### Interface: Note door

```python
@dataclass(frozen=True)
class CommitReceipt:
    index: int
    path: str
    title: str

def commit_note(text: str, notes_dir: Path) -> CommitReceipt:
    """Writes notes/captures/<slug>.md with today's date in the body and a title
    from the first words. Appends the node to graph-data.js. Inserts the live index.
    Returns the receipt. Raises NoteWriteError if the file or the graph write fails.
    The HTTP layer turns that into a spoken failure, never an empty 200."""

def add_note_event(receipt: CommitReceipt, related_index: int) -> dict:
    """JSON the page feeds to addNote(node, relatedIndex)."""
```

HTTP: `POST /remember` `{"text": str}` → `201` and the receipt, or `500 {"error": str}`.

Page:

```javascript
function addNote(node, relatedIndex) { /* birth at that node's position, pulse, fly */ }
function play(urlOrBlob) { /* if (new URLSearchParams(location.search).has('mute') && location.search.includes('mute=1')) return; */ }
```

`mute=1` is checked only inside `play`. Hearing still runs on a muted tab.

### Interface: Routes and shelf

Checked before `chat()`. Match is case-insensitive on the stripped utterance.

| Utterance prefix or exact phrase | Effect |
|---|---|
| use your local voice | Select VoiceStudio. Badge will show `local:Spark` |
| use the browser voice | Next replies carry `X-Spark-Voice: browser` |
| switch to your local brain / go local | Brain, voice, and ears local. Spoken by the local brain |
| switch to your big brain | Shelf entry `big`. If `model` is empty, one spoken line and no swap |
| switch to claude / go cloud | If the key is still `PUT-YOUR-KEY-HERE`, one spoken line, stay local |
| which brain are you on | One spoken line: name, model, machine (this machine / cloud) |
| remember that … / note to self … / don't let me forget … / log this … | `commit_note` on the remainder |

Swaps are not written back to `boot_brain`.

### Interface: HTTP surface

```
GET    /                         -> 200 viewer/index.html
GET    /graph-data.js            -> 200 the generated file
GET    /vendor/*                 -> 200 vendored assets only
POST   /chat      {text}         -> 200 {answer, nodes, seconds, brain, voice}
POST   /tts       {text}         -> 200 audio/wav | 503 {fallback:"browser"}
POST   /hear      <wav bytes>    -> 200 {text, seconds}
POST   /remember  {text}         -> 201 {index, path, title} | 500 {error}
GET    /health                   -> 200 {brain, voice, hearing, note_count, device}
GET    /drill/connections        -> 200 {server: [{host, reason}], browser: [host]}
```

Anything outside `viewer/` returns 404, including `GET /config.json` and `GET /../config.json`. Bind address is `127.0.0.1`. Port is `4700`.

### Interface: Drill and preflight

```python
def drill_once() -> list[str]:
    """One real /chat, /tts of that answer, /hear of that WAV, then hosts that are
    not localhost and not 127.0.0.1. Empty list is a pass. If the active brain is
    the cloud shelf with a real key, the list must contain api.anthropic.com and
    the script's exit code is non-zero on purpose."""

def honest_list() -> list[str]:
    """Features that still need a network, read from config and the source:
    cloud brain when a real key is set; any CDN url still under viewer/;
    live web research if a function for it exists. This build has no research function."""
```

`preflight.py` runs against the live server, in order, each as a tick or a cross:

- Server up and serving the viewer
- Graph loads and node count > 0
- Ollama `/v1/models` lists the configured brain, else print the exact `ollama pull` line
- `/chat` returns `answer` and `nodes` for a real question, with seconds
- VoiceStudio `/health`, selected engine matches config, `/tts` returns a WAV and seconds-to-first-byte
- Loop: a known sentence through `/tts`, that WAV through `/hear`, same words back, small differences allowed
- `/remember` writes a file, `/chat` retrieves it, then the test note is removed
- Bytes the browser is served match the files on disk
- `GET /config.json` does not return the file
- The mute gate in `play` refuses when the flag is set (static check of the one function, plus a headless assertion if a browser is available; the static check is the required one)
- No cloud key string under `viewer/`

Last two lines of stdout: `LATENCY hear=X.XXs think=Y.YYs speak=Z.ZZs total=T.TTs` and `SUMMARY pass=N fail=N warn=N`. Exit non-zero on any failure. Missing voice and missing ears are WARN. From Phase 4 on, a change is done when this script has been run and both lines pasted.

### Interface: Persona control tags

When the operator asks for an action the model cannot perform by talking, the model emits one tag and the server executes it. The first tag list is only:

```
[REMEMBER] text
[SWITCH local|big|claude]
```

The route table is still the primary path. Tags exist so a paraphrase still hits the door. The Phase 2 test asks five times. More than one miss means the instruction in `PERSONA` gets shorter, not longer.

---

## TDD SECTION 4 — IMPLEMENTATION PHASES & TEST SUITE STRATEGY

Phases match the manifest sequence. Each one leaves something runnable.

### Phase 1 — Core engine

**Scope.** `build.py`, `server.py` bound to `127.0.0.1:4700`, `config.json`, `POST /chat`, `viewer/index.html` with the vendored graph already saved (do not wait for Phase 4 to remove a CDN; put the library in `vendor/` in this phase so the honest list is born empty). `build.py` walks the corpus allowlist and skips `chunks\`, `_build_snhu\`, `node_modules\`, `venv\`, and any filename containing `api_keys`, `.env`, or `credentials`. It does not generate sample notes. The first proof question uses a real ledger title from that allowlist.

**Deliverable.** The server is running. A browser on this machine loads the galaxy. `/chat` answers from a real note and prints the seconds.

**Unit tests, written first.**

1. `test_node_id_equals_index` — three markdown files yield ids 0, 1, 2 in scan order.
2. `test_link_on_title_mention_and_wikilink` — a body that names another file's title, and a `[[Title]]`, each produce one link. A shared ordinary word does not.
3. `test_score_weights_title_above_body` — a title hit outranks a longer body overlap and the result is capped at 6.
4. `test_excerpt_caps_near_700_characters` — a long note's excerpt length is at most 750 characters.
5. `test_persona_under_300_words_and_stable_prefix` — word count, and a second `complete()` request builder shows the system string identical and first.
6. `test_empty_content_retries_once` — a fake transport that returns `finish_reason=length` and empty content is called twice; the second call's `max_tokens` is larger.
7. `test_reasoning_effort_none_merged` — the JSON body contains `reasoning_effort` `none` and the placeholder key is absent from any log line the test captures.
8. `test_config_json_is_not_servable` — the static handler's root is `viewer/` and a path traversal to `config.json` returns 404.

### Phase 2 — State and the bays

**Scope.** Voice, hearing, chunks, cache, warm loop, wake, finish window, routes, `commit_note`, live index.

**Deliverable.** A remembered sentence is a file on disk and the next `/chat` returns its index. A muted tab does not construct an audio element.

**Integration tests.**

1. `test_commit_note_is_searchable_without_rebuild` — write through the door, score a question that only that file answers, assert the new id is in the top 6.
2. `test_failed_write_returns_error_not_200` — a read-only captures directory yields `NoteWriteError` and HTTP 500 with a non-empty `error`.
3. `test_split_chunks_never_breaks_a_sentence` — an 80-word answer with a 40-character sentence in the middle keeps that sentence whole, and no chunk is cut early to "start faster."
4. `test_wake_strips_aliases_and_discards_the_rest` — "hey spark, what is the finish window" yields the command; "what is the finish window" yields discard; "spark" alone yields the attention hold.
5. `test_finish_window_appends` — two clips separated by less than `FINISH_MS` become one dispatch; a gap longer than `FINISH_MS` dispatches the first.
6. `test_mute_flag_is_only_inside_play` — the source of `index.html` contains the `mute=1` check in `play` and nowhere else that calls `Audio` or `speechSynthesis`.
7. `test_switch_with_placeholder_key_stays_local` — "switch to claude" leaves `boot` runtime brain on `local` and the spoken line mentions the missing key.
8. `test_wav_cache_hits` — two `synthesize` calls with the same text and profile touch the engine once.

Voice and ears tests that need the daemons skip with a warning when `/health` or the whisper import is absent. They do not fail the unit suite. Preflight is what promotes them to a hard check.

### Phase 3 — The page

**Scope.** The design spec, wired to Phases 1 and 2. Status line, badge, plate, birth, cluster light, idle rotation, input bar.

**Deliverable.** An operator can sit at the page, speak or type, and see the note the answer used.

**Validation.**

1. After load, the spoken line is one short sentence ("Still here." or the equivalent in the persona block) and the note count on screen equals `GRAPH.nodes.length`.
2. Status text cycles through listening, the heard words, thinking, and speaking, in that order, on a hands-free turn. A `?mute=1` tab still shows the heard words and does not speak.
3. A question that hits four notes lights the cluster and does not fly to a single star. A "good morning" does not move the camera.
4. The badge shows `BRAIN` and `VOICE`, appears when either changes, and hides after five seconds. A warm reply on the same voice does not show it again.
5. First interaction paints within a frame budget of 16 ms of script work after the graph has settled, measured in the performance panel on this machine. The local model's think-time is excluded from that figure and reported by preflight instead. Target for the page's own response to a click is under 100 ms to start the camera fly.

### Phase 4 — Proof

**Scope.** `drill.py`, `preflight.py`, persona before/after timing, the Wi-Fi-off script in the README of this protocol.

**Deliverable.** Preflight's two lines, pasted. Drill host list empty in local mode.

**Exit.**

1. Phases 1 and 2 tests still pass.
2. `drill.py` prints no foreign host. With the cloud shelf forced active and a real key, it prints `api.anthropic.com` and exits non-zero.
3. Preflight latency budget is measured on this machine and written into `VERSIONS.txt` next to the Ollama tag. There is no universal seconds target. The November pack's rule is the memory headroom rule; the October pack's rule is to publish the three numbers rather than invent them.
4. No remote `src`, `href`, `import`, `fetch`, or `url(` target under `viewer/`. A bare `http://` or `https://` search is not the check: `index.html` needs the SVG namespace `http://www.w3.org/2000/svg`, and vendor comments contain documentation URLs. A grep for `PUT-YOUR-KEY-HERE` and for `\bsk-` under `viewer/` is empty. The Schibsted Grotesk files are named `schibsted-grotesk-…`, and a bare `sk-` search matches those names. The word boundary does not.
5. README states the four-step on-camera check: Wi-Fi off, reload, one question whose answer is one note, galaxy flies to that note, answer in the cloned voice.

Phase count stays at four. A separate "state" phase is Phase 2. A UI-less release is not the product, so Phase 3 is not skipped.

---

## TDD SECTION 5 — DESIGN VERIFICATION & EDGE CASES

### 5.1 Failure Mode Catalog

| Failure Mode | System Manifestation | Detection | Correct response |
|---|---|---|---|
| Local model spends its token budget thinking and returns empty `content` | The page would show a blank answer and the voice would have nothing to say | `finish_reason == length` and empty content | Retry once with a larger `max_tokens`. If still empty, speak one line that the brain returned nothing. Do not invent the answer |
| VoiceStudio closed, or the default non-commercial pack selected itself | First reply of the day takes many seconds, or the license is the wrong one | `/health` over 1 second, or `/engines/select` result differs from config | Fall back to the browser voice, set `X-Spark-Voice: browser`, show the badge. Reselect `voxcpm2` at every boot |
| Capture file written, live index not updated | The operator hears a confirmation and the next question cannot find the note | `test_commit_note_is_searchable_without_rebuild`; preflight's remember check | `commit_note` is one function. A partial write raises, the spoken line says it failed, and no star is born |
| Own voice through the speakers trips the mic | SPARK interrupts itself on "stop" it never heard from the operator | Status flips to listening while speaking, on a speaker setup | Raised threshold during playback. The README tells the operator to use headphones if the drill still self-triggers |
| PyAV 19 installed beside faster-whisper 1.2.1 | Every `/hear` throws `TypeError` on `metadata_errors` before decode | Preflight hearing cross; the traceback names `av.open` | The requirements pin `av==18.1.0`. Boot does not crash the server; hearing goes WARN and the status line says ears are down |
| Cloud shelf selected and the network is unplugged | A hang until the TCP timeout, then a fake apology | Drill, and the outbound wrapper | One spoken line that the cloud brain is unreachable. Stay able to switch back. Do not answer from imagination |

### 5.2 Performance Thresholds

| Metric | Target | Hard limit | Measurement |
|---|---|---|---|
| Page script after graph settle | Camera fly starts < 100 ms from click | 200 ms | Browser performance panel, Phase 3 |
| Think time | Recorded, not invented | A regression of more than 25% versus the number written in `VERSIONS.txt` after the first clean preflight, on the same brain tag | `preflight.py` `think=` |
| Time to first audio | A beat of wait is acceptable | A pause inside a sentence is a failure even if the first byte was faster | Phase 2 chunk test plus a listened 10-word and 80-word pass |
| Hearing on a 5-second clip | Under 2 seconds on the large model | If the large model is slower, switch both jobs to `small` and write that in config | Install 03's second run |
| Memory headroom | ~30% free with brain, voice, and both Whisper models resident | A model that leaves under 2 GB free is the wrong tag | Task Manager during a turn |
| Persona | < 300 words | A growth in token count that slows `think=` without a written waiver | Word-count test, printed before and after any persona edit |

### 5.3 Platform and environment edge cases

- **Windows SmartScreen** may warn on the VoiceStudio installer. The checksum step in the vendor install script is the check. The protocol does not bypass it with a custom downloader.
- **NVIDIA** uses the GPU for Ollama and faster-whisper automatically. **AMD** falls back to CPU unless ROCm is on. `/health` reports the device. A CPU ear is a WARN the operator can see, not a silent quality drop.
- **Sleep and wake.** The warm loop dies with the process. After sleep, the first "Standing by." miss is tolerated; the next real line may be a cold start. The badge does not claim `local` audio until a WAV has actually come back this session.
- **Two tabs.** Both may listen. Only a tab without `mute=1` may speak. Tests open with `?mute=1`.
- **Headphones versus speakers.** Documented in the README when the interrupt threshold cannot tell the operator from the speakers.
- **Wi-Fi off.** After Phase 4 the page reloads from disk, the graph renders, and a note-backed question still answers. The honest list is empty in that mode.
- **Placeholder key.** It never travels to the browser. Grep is a Phase 4 exit check.
- **Concurrent remember.** One writer. A second `commit_note` waits on a lock so two captures cannot append the same id.
- **Qt.** This protocol does not import PyQt. A future HUD button that opens the browser to `http://127.0.0.1:4700` is a one-line shell-open on the Qt thread's existing pattern, specified in a later change, not here.

---

## Next Steps

1. Measure this PC: RAM, whether the GPU is NVIDIA, and `ollama list`. Write the tag you will actually boot into `config.json` before any page work. The floor remains `qwen3.5:9b` until that measurement says a larger tag fits with 30 percent free.
2. Create the 3.11 venv and pin `faster-whisper==1.2.1` and `av==18.1.0`. Run the five-second Whisper proof from the November pack's Install 03 before writing `hear.py`.
3. Scaffold Phase 1 from the interfaces above: `build.py`, `server.py`, `config.json`, `viewer/index.html`, `viewer/vendor/` with 3d-force-graph 1.80.2 already on disk. Run the eight Phase 1 tests, then one live `/chat`, and record the seconds.

## Diagnostic Question

Which Ollama tag is already resident on this Windows machine, and how much memory can the model actually see (GPU VRAM, or system RAM if there is no discrete NVIDIA card)? Phase 1's `/chat` proof and the persona's rule count both change with that tag: a 9B brain keeps the five-rule prefix, and a 27B brain may add one rule, not a second page of character.
