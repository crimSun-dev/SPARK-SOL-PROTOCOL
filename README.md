# SPARK SOL PROTOCOL

A local voice companion and a star chart of Flaxeon's memory. `server.py` serves the
galaxy page at `http://127.0.0.1:4700/` and answers from the notes on this machine.

## Run

```
pip install -r requirements.txt
python server.py            # reads Neon at boot, then re-reads it every 60 s
python server.py --watch 0  # no live re-read
python preflight.py         # with the server running
```

`config.json` (brains and keys), `notes/`, `index/` and `viewer/graph-data.js` (the
memory itself) are local only and are never committed.

## The web viewer

GitHub Pages publishes `viewer/` with an empty `GRAPH`, so the site holds no memory.
Opened on the machine that runs `server.py`, it reads `/graph` and `/health` from
`http://127.0.0.1:4700` every 5 seconds and redraws the sky when memory changes:

- a note SPARK SOL saves, at once;
- a write Flaxeon makes to Neon, within one watch interval (60 s by default).

The server answers it only for the `https://crimsun-dev.github.io` origin. A browser
paired with the local page's WEB CODE can also ask. `?port=4701` points it at a second
server on the same machine.

## Feeding Flaxeon

Tell Flaxeon to index something and it lands on the sky. Its `spark_protocol` tool runs
`build.py`, then `cloud_sky.py`, in the background, and logs the outcome:

- "index my workspace": a full, incremental run.
- "index G:/Games/Ember" or "add my notes folder": a feed, sorted on its own. Sure signs
  sort it first (a Godot, Unity, Unreal, LÖVE or Phaser project goes in games, a SKILL.md
  in skills). Otherwise the model picks, and failing that the mix of file types.
- "index G:/Games/Ember under games": a feed in the category you name.
- "move Secret Game Dev to games": an indexed project changes region.
- "what categories do you have".

A category is any short name. A new one (games, music) becomes a new region of the sky,
with its own colour, on the PC and on the web page. The registry is `feeds.json`
(git-ignored: it holds local paths). It can also be edited with
`python feeds.py list|add|categorize|remove`.

## With the PC off: the cloud copy

When `127.0.0.1` does not answer, the page opens the cloud copy of Flaxeon's memory from
Firestore in the `flaxeon` Firebase project. Everything runs on GitHub Pages and Firebase.

- **Sign in once.** Press Enter in the ask line and sign in with Google. Only an account
  listed in `spark_access` can read (`firebase/firestore.rules`). The first time, the page
  shows the account's uid. On the PC, run `python cloud_firebase.py grant` to add it.
- **Claude key once.** Paste a Claude API key into the ask line. It is kept in
  `spark_private/brain`, which only that account can read. Answers come from Claude,
  called from the browser.
- **The same instrument.** The sky, the star search, asking (with the PC's persona and its
  search over each star's full text), "which brain are you on", and "remember that…" all
  work. A note saved with the PC off is born on the sky at once. It waits in
  `spark_inbox`, and `server.py` files it the next time it runs, with `commit_note`, into
  `notes/captures` and Neon, exactly as a spoken one. Voice and the microphone stay off
  on the web, as before.
- **What needs the PC.** The file search: the index is 5.3 GB, far over Firestore's free
  tier. The local and big brains. Captures in `notes/` and the Tempest pack store never
  leave the PC, so they are not on the cloud sky.
- **Fresh every 30 minutes.** The scheduled Action (`github-to-memory.yml`) runs
  `cloud_sky.py`. It reads Neon, builds the sky with `read_memory.build_graph`, and writes
  it to `spark_sky` in chunks. A new generation replaces the old one only after it is
  complete. An unchanged memory writes nothing.
- Repo secrets: `NEON_URL`, `FIREBASE_SERVICE_ACCOUNT` (the service account JSON).

```
python cloud_firebase.py plan      # read-only: what setup would change
python cloud_firebase.py apply     # web app, Pages domain, rules (the old rules saved to cache/)
python cloud_firebase.py grant     # after the first sign-in on the page
python cloud_firebase.py rollback  # the previous rules back
```

The rules also close a gap: Flaxeon's replica (`flaxeon/default`) was readable by *any*
signed-in account. Now only the paired phones (`phone-…` uids, which only meshgate can
mint) and the operator can read it.
