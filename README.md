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

It is read-only. It never asks, listens, speaks or posts. The server answers it only on
those two routes, and only for the `https://crimsun-dev.github.io` origin. Opened anywhere
else, the page shows an empty sky and says that SPARK SOL is not running on that machine.
`?port=4701` points it at a second server on the same machine.

Chrome may ask once to allow the site to reach devices on the local network. Allow it.
