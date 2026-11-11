## Why

The GitHub Pages viewer can show and search the sky, but it cannot ask SPARK SOL a question. Its origin, `crimsun-dev.github.io`, is shared by every Pages site on the account, and `/chat` can write memory through its remember door. So asking must be allowed only for a browser the operator has paired on purpose.

## What Changes

- The local server keeps a six-digit pairing code. The local page (`127.0.0.1:4700`) shows it on request through a new `WEB CODE` word on the floor. The code is never sent to another origin.
- The web viewer shows its ask line. The first question asks for the code. The page sends it to `POST /pair`, receives a random token, and keeps it in that browser's storage.
- The server accepts `POST /chat` from the Pages origin only with a valid token, sent in an `X-Spark-Token` header. Every other POST from that origin is still refused: `/remember`, `/tts`, `/hear`, `/reload`, `/shutdown` and the drill routes. Token hashes persist in `cache/web_tokens.json`, so a restart keeps the pairing, and deleting that file unpairs every browser.
- Five wrong codes in a row replace the code. A successful pairing replaces it too, so each code pairs one browser.
- On the web viewer, answers appear as text and drive the sky (fly, cited stars, birth) as on the local page. The web viewer does not speak or listen.

## Capabilities

### New Capabilities

- `web-ask`: a paired web viewer can ask SPARK SOL questions through the local server; nothing on the shared Pages origin can without the pairing.

### Modified Capabilities

- None.

## Impact

- `server.py` (pairing, token check, CORS for `/chat` and `/pair`), `viewer/index.html` (ask on the web viewer, the `WEB CODE` word on the local page).
