## Context

See proposal.md. The server already answers the Pages origin on `/graph`, `/health` and `/search` (GET) and refuses every POST from it. The web viewer hides its ask line.

## Goals / Non-Goals

**Goals:** asking from a paired web viewer only; nothing else becomes writable from the web.

**Non-Goals:** voice or microphone on the web viewer; accounts; access from another machine (the server stays on 127.0.0.1).

## Decisions

### 1. Code shown locally, token kept by the browser

- The code comes from `secrets.randbelow`. Tokens are 32 random bytes, and only their SHA-256 is stored, in `cache/web_tokens.json`, which git ignores.
- The local page reads the code from `GET /pair/code`. That route answers only loopback requests with no `Origin` header or the server's own origin, and it never carries CORS headers, so another origin cannot read it.
- The token travels in an `X-Spark-Token` header, so every web `/chat` request needs a CORS preflight. The preflight allows that header for `/chat` and `/pair` only.

Alternative considered: no code. Rejected, because every Pages site on the account shares the origin, and `/chat` can write memory.

### 2. Rate of guessing

Five wrong codes replace the code, so a page that guesses gets at most five tries per code shown. The code is also replaced after each successful pairing.

### 3. The web viewer's ask

`turn()` posts to `API + "/chat"` with the token. When the page is not on its own server, it skips speech: no `/tts`, no browser synthesis. A missing or refused token puts the ask line into code mode, where the next entry is sent to `/pair`.

## Risks / Trade-offs

- [The token sits in browser storage on this PC] → It works only from this machine, because the server binds to 127.0.0.1. Deleting `cache/web_tokens.json` revokes it.
