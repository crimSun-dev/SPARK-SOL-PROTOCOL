## Purpose

A web viewer that the operator has paired on purpose can ask SPARK SOL questions through the local server. Nothing else on the shared Pages origin can.

## ADDED Requirements

### Requirement: Pairing with a code shown only locally
The local server MUST keep a six-digit pairing code. It MUST reveal the code only to the local page on its own origin, and never to another origin. `POST /pair` from the Pages origin with the right code MUST return a new random token. A wrong code MUST be refused. Five wrong codes in a row, or one successful pairing, MUST replace the code.

#### Scenario: Pairing
- **WHEN** the operator types the code shown on the local page into the web viewer
- **THEN** the web viewer receives a token and can ask from then on

#### Scenario: Guessing
- **WHEN** five wrong codes are sent
- **THEN** the code is replaced and the earlier code no longer pairs

### Requirement: Asking needs a token
The server MUST answer `POST /chat` from the Pages origin only when it carries a valid token. Every other POST from that origin MUST be refused. Tokens MUST survive a server restart, and MUST be revocable by deleting the token file.

#### Scenario: No token
- **WHEN** a page on the Pages origin posts to `/chat` without a token
- **THEN** the server refuses it and nothing is written

#### Scenario: Other routes
- **WHEN** a paired web viewer posts to `/remember`, `/reload` or `/shutdown`
- **THEN** the server refuses it

### Requirement: The web viewer asks in text
The paired web viewer MUST show the answer as text and drive the sky as the local page does. It MUST NOT speak or use the microphone.

#### Scenario: A question on the web viewer
- **WHEN** the operator asks about a note on the paired web viewer
- **THEN** the answer appears on the floor and the cited star opens
