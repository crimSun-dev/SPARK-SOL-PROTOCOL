## 1. Server

- [x] 1.1 Add the pairing code, `GET /pair/code` (local origin only), `POST /pair`, token hashes in `cache/web_tokens.json`, and the five-miss and on-success code replacement. Verify that another origin cannot read the code, that a right code returns a token, and that five wrong codes replace it.
- [x] 1.2 Allow `POST /chat` from the Pages origin only with a valid token, with a preflight for `/chat` and `/pair`. Verify that `/chat` without a token, `/remember`, `/reload` and `/shutdown` from that origin are refused, and that `/chat` with a token answers.

## 2. Pages

- [x] 2.1 Add the `WEB CODE` word to the local floor. Verify that clicking it shows the current code.
- [x] 2.2 Show the ask line on the web viewer, with code mode for pairing, the token sent on `/chat`, and no speech. Verify end to end that pairing works, that the answer shows and the cited star opens, and that the token survives a reload of the page and a restart of the server.
