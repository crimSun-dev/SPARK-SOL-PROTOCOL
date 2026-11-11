"""The connection drill. One real turn, then every host it touched.

/chat a real question, /tts that answer, /hear that WAV, then print every host
that is not localhost or 127.0.0.1, from the server's log and from the page's
own resource list. Passes only when that list is empty AND the page has posted
its half. Run it with the page open in a browser tab (use ?mute=1).

    python drill.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "http://127.0.0.1:4700"
LOCAL = {"localhost", "127.0.0.1", "::1"}
QUESTION = "What is my favourite tea?"


def post(path: str, body: bytes, ctype="application/json", timeout=600):
    req = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def get(path: str, timeout=10):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.loads(r.read())


def drill_once(say=print) -> tuple[bool, list[str], dict]:
    """Returns (passed, outside_hosts, notes)."""
    start = time.time() - 0.5
    notes = {}
    st, _, raw = post("/chat", json.dumps({"text": QUESTION}).encode())
    d = json.loads(raw)
    notes["brain"] = f"{d.get('brain')} · {d.get('model')} on {d.get('where')}"
    say(f"  chat   {st}  brain={notes['brain']}  {d.get('seconds')}s")
    st, h, wav = post("/tts", json.dumps({"text": d.get("answer", "")[:600]}).encode())
    notes["voice"] = h.get("X-Spark-Voice")
    say(f"  tts    {st}  X-Spark-Voice={notes['voice']}")
    if st == 200 and wav[:4] == b"RIFF":
        st, _, raw = post("/hear?model=command", wav, "audio/wav")
        say(f"  hear   {st}  " + (f"{json.loads(raw).get('seconds')}s" if st == 200 else raw.decode()[:80]))
    else:
        say("  hear   skipped: no local voice WAV to feed it")
    conn = get(f"/drill/connections?since={start}")
    outside = sorted({e["host"] + "  (" + e["reason"] + ")" for e in conn["server"]
                      if e["host"] not in LOCAL})
    browser = conn.get("browser")
    if browser is None:
        say("  browser: the page never posted its resource hosts. Open the page; this half is missing, not empty.")
    else:
        outside += sorted("browser: " + h for h in browser if h not in LOCAL)
    return (browser is not None and not outside), outside, notes


def honest_list() -> list[str]:
    """What still opens a non-local host, read from the config and the source."""
    out = []
    try:
        cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        cl = cfg.get("brains", {}).get("claude", {})
        if cl.get("api_key") and cl["api_key"] != "PUT-YOUR-KEY-HERE":
            out.append("Cloud brain: api.anthropic.com, only after 'switch to Claude' or 'go cloud' (a key is set).")
        else:
            out.append("Cloud brain: none. The key is still the placeholder, so a cloud switch stays local.")
    except Exception:
        out.append("Cloud brain: config.json unreadable; check it.")
    out.append("Memory read at start: Neon is remote. With Wi-Fi off the reader falls back to "
               "the parent's memory/long_term.json and the floor says MIRROR.")
    out.append("Whisper models: one download from huggingface.co the first time only; after that, local files.")
    remote = []
    pat = re.compile(r"""(?:src|href)\s*=\s*["'](https?:)?//|import\s*\(?\s*["']https?://|fetch\(\s*["']https?://|url\(\s*["']?https?://""", re.I)
    for f in (HERE / "viewer").rglob("*"):
        if f.suffix.lower() in {".html", ".js", ".mjs", ".css"} and f.name != "graph-data.js":
            if pat.search(f.read_text(encoding="utf-8", errors="ignore")):
                remote.append(str(f.relative_to(HERE)))
    out.append("Page resources: " + (", ".join(remote) + " load a remote target." if remote
                                     else "every src, href, import, fetch and url( target is a local file."))
    out.append("Live web research: not a feature. No function for it exists.")
    return out


def main() -> int:
    print("SPARK SOL drill")
    try:
        passed, outside, _ = drill_once()
    except Exception as e:
        print(f"  the server did not answer ({type(e).__name__}). Start server.py first.")
        return 2
    print("Hosts outside this machine during the turn:")
    print("\n".join("  " + h for h in outside) if outside else "  none")
    print("Honest list:")
    for line in honest_list():
        print("  - " + line)
    print("DRILL " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
