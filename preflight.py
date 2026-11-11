"""SPARK SOL preflight. Live: it hits the running server, Ollama and VoiceStudio.

Not a mock and not a pytest module. Start server.py, open the page in a tab
(?mute=1 is fine, the drill needs the page's half), then:

    python preflight.py

Ends with two lines: the latency budget measured on this run, and the counts.
Exit code is non-zero on any FAIL. Missing voice or missing ears are WARN.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIEWER = HERE / "viewer"
BASE = "http://127.0.0.1:4700"
RESULTS = {"pass": 0, "fail": 0, "warn": 0}
LAT = {"hear": None, "think": None, "speak": None}
MARK = {"pass": "✓", "fail": "✗", "warn": "!"}


def out(kind: str, what: str, detail: str = "") -> None:
    RESULTS[kind] += 1
    print(f" {MARK[kind]} {kind.upper():4}  {what}" + (f"  — {detail}" if detail else ""), flush=True)


def req(url: str, body=None, ctype="application/json", timeout=600, method=None):
    data = json.dumps(body).encode() if isinstance(body, dict) else body
    r = urllib.request.Request(url, data=data, method=method,
                               headers={"Content-Type": ctype} if data is not None else {})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            first = resp.read(1)
            ttfb = time.perf_counter() - t0
            rest = resp.read()
            return resp.status, resp.headers, first + rest, ttfb
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read(), time.perf_counter() - t0


def jbody(raw: bytes):
    try:
        return json.loads(raw)
    except ValueError:
        return {}


def words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower())


def main() -> int:
    print("SPARK SOL preflight —", time.strftime("%Y-%m-%d %H:%M"))
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    brain = cfg["brains"].get(cfg.get("boot_brain", "local")) or cfg["brain"]

    # 1 server up and serving the viewer
    try:
        st, _, body, _ = req(BASE + "/", timeout=5)
        ok = st == 200 and b"SPARK SOL" in body
        out("pass" if ok else "fail", "server up and serving the viewer", f"HTTP {st}")
    except Exception as e:
        out("fail", "server up and serving the viewer", f"{type(e).__name__}: start server.py")
        return finish()

    # 2 graph data loads, node count > 0
    st, _, js, _ = req(BASE + "/graph-data.js", timeout=5)
    try:
        g = json.loads(js[js.index(b"{"):js.rindex(b"}") + 1])
        n = len(g["nodes"])
        out("pass" if n > 0 else "fail", "graph data loads", f"{n} notes, source {g.get('source')}")
    except Exception:
        out("fail", "graph data loads", "graph-data.js did not parse")

    # 3 Ollama lists the configured brain
    if "api.anthropic.com" in brain["base_url"]:
        out("warn", "Ollama brain check", "boot brain is the cloud; skipped")
    else:
        try:
            st, _, raw, _ = req(brain["base_url"].rstrip("/") + "/models", timeout=5)
            ids = [m.get("id") for m in jbody(raw).get("data", [])]
            if brain["model"] in ids:
                out("pass", "Ollama answers /v1/models with the configured brain", brain["model"])
            else:
                out("fail", "configured brain not in Ollama", f"run: ollama pull {brain['model']}")
        except Exception as e:
            out("fail", "Ollama answers /v1/models", f"{type(e).__name__}; then: ollama pull {brain['model']}")

    # 4 /chat answers with nodes
    st, _, raw, _ = req(BASE + "/chat", {"text": "What is my favourite tea?"})
    d = jbody(raw)
    if st == 200 and d.get("answer") and isinstance(d.get("nodes"), list) and not d.get("error"):
        LAT["think"] = d.get("seconds")
        out("pass", "/chat returns an answer and a nodes array", f"{d['seconds']}s, {len(d['nodes'])} cited")
    else:
        out("fail", "/chat returns an answer and a nodes array", d.get("error") or f"HTTP {st}")

    # 5 VoiceStudio health and /tts
    h = jbody(req(BASE + "/health", timeout=5)[2])
    vb = h.get("voice_bay", {})
    voice_ok = False
    if vb.get("status") != "ready":
        out("warn", "VoiceStudio voice", f"{vb.get('status')}: {vb.get('error') or 'not answering on 3900'}; "
            "the page falls back to the browser voice")
    else:
        pinned = cfg["voice"]
        if vb.get("engine") == pinned["engine"] and vb.get("model_id") == pinned["model_id"]:
            st, hd, wav, ttfb = req(BASE + "/tts", {"text": "Still here."})
            if st == 200 and wav[:4] == b"RIFF":
                voice_ok = True
                LAT["speak"] = round(ttfb, 2)
                out("pass", "VoiceStudio pinned engine, /tts returns a WAV",
                    f"{pinned['engine']}/{pinned['model_id']}, first byte {ttfb:.2f}s, {hd.get('X-Spark-Voice')}")
            else:
                out("fail", "/tts returns a WAV", f"HTTP {st}, {hd.get('X-Spark-Voice')}")
        else:
            out("fail", "VoiceStudio engine matches the pin", f"{vb.get('engine')}/{vb.get('model_id')}")

    # 6 the loop: voice -> ears -> same words
    ears = h.get("hearing", {})
    sentence = "The spare lantern is on the second shelf of the observatory."
    if ears.get("status") != "ready":
        out("warn", "ears", f"{ears.get('status')}: {ears.get('error') or ''}".strip(": "))
    elif not voice_ok:
        out("warn", "voice to ears loop", "no local voice WAV to feed the ears")
    else:
        st, _, wav, ttfb = req(BASE + "/tts", {"text": sentence})
        st2, _, raw, _ = req(BASE + "/hear?model=command", wav, "audio/wav")
        heard = jbody(raw).get("text", "")
        ratio = difflib.SequenceMatcher(None, words(sentence), words(heard)).ratio()
        LAT["hear"] = jbody(raw).get("seconds")
        out("pass" if ratio >= .8 else "fail", "voice to ears loop",
            f"{ratio:.0%} word match, hear {LAT['hear']}s on {ears.get('device')}")

    # 7 /remember writes a file, /chat retrieves it, then the test note is removed
    token = "preflight quartz heron " + time.strftime("%H%M%S")
    st, _, raw, _ = req(BASE + "/remember", {"text": f"the {token} sits on the windowsill"})
    r = jbody(raw)
    path = HERE / r.get("path", "missing")
    if st == 201 and path.exists():
        st2, _, raw2, _ = req(BASE + "/chat", {"text": f"Where does the {token} sit?"})
        got = jbody(raw2)
        found = r.get("index") in (got.get("nodes") or [])
        und = req(BASE + "/remember/undo", {"path": r["path"]})[0]
        gone = not path.exists()
        out("pass" if found and gone and und == 200 else "fail", "/remember writes, /chat retrieves, test note removed",
            f"file {r['path']}, retrieved={found}, removed={gone}")
    else:
        out("fail", "/remember writes a real file", r.get("error") or f"HTTP {st}")

    # 8 bytes served match bytes on disk
    bad = []
    for rel in ["index.html", "vendor/3d-force-graph.min.js", "vendor/three/three.module.js",
                "vendor/brand/spark-sol-lockup.png"]:
        served = req(BASE + "/" + rel, timeout=10)[2]
        if hashlib.sha256(served).digest() != hashlib.sha256((VIEWER / rel).read_bytes()).digest():
            bad.append(rel)
    out("fail" if bad else "pass", "served bytes match disk", ", ".join(bad) or "4 files by sha256")

    # 9 config.json must not be reachable
    leaks = []
    for p in ["/config.json", "/../config.json", "/%2e%2e/config.json", "/..%2fconfig.json"]:
        st = req(BASE + p, timeout=5)[0]
        if st == 200:
            leaks.append(p)
    out("fail" if leaks else "pass", "config.json is not reachable from the browser", ", ".join(leaks) or "all 404")

    # 10 ?mute=1 makes play() refuse — static check of the one function
    html = (VIEWER / "index.html").read_text(encoding="utf-8")
    m = re.search(r"function play\(what\) \{(.*?)\n\}", html, re.S)
    body = m.group(1) if m else ""
    first = body.strip().splitlines()[0] if body.strip() else ""
    sound_sites = len(re.findall(r"new Audio\(|speechSynthesis\.speak\(", html))
    in_play = len(re.findall(r"new Audio\(|speechSynthesis\.speak\(", body))
    ok = 'get("mute") === "1"' in first and "return" in first and sound_sites == in_play > 0
    out("pass" if ok else "fail", "?mute=1 makes play() refuse, and play() is the only sound site",
        f"{in_play} sound calls, all inside play()")

    # 11 no cloud key under viewer/
    hits = []
    key = cfg["brains"].get("claude", {}).get("api_key", "")
    for f in VIEWER.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in {".html", ".js", ".mjs", ".css", ".json", ".txt"}:
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"\bsk-[A-Za-z0-9_\-]{12,}", t) or "PUT-YOUR-KEY-HERE" in t or \
                re.search(r"\bAIza[0-9A-Za-z_\-]{20,}", t) or (len(key) > 20 and key in t):
            hits.append(str(f.relative_to(HERE)))
    out("fail" if hits else "pass", "no cloud key under viewer/", ", ".join(hits) or "none")

    # 12 no remote load targets under viewer/
    pat = re.compile(r"""(?:\bsrc|\bhref)\s*=\s*["'](?:https?:)?//[^"']+|\bimport\s*\(?\s*["']https?://[^"']+|"""
                     r"""\bfetch\(\s*["']https?://[^"']+|\burl\(\s*["']?https?://[^)"']+""", re.I)
    remote = []
    for f in VIEWER.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".html", ".js", ".mjs", ".css"} and f.name != "graph-data.js":
            for hit in pat.findall(f.read_text(encoding="utf-8", errors="ignore")):
                remote.append(f"{f.relative_to(HERE)}: {hit[:60]}")
    out("fail" if remote else "pass", "no remote src/href/import/fetch/url( under viewer/",
        "; ".join(remote[:3]) or "SVG namespace and comment URLs not counted")

    # 13 the drill passes in local mode
    sys.path.insert(0, str(HERE))
    import drill
    try:
        passed, outside, notes = drill.drill_once(say=lambda *_: None)
        detail = "no host outside this machine" if passed else (
            "; ".join(outside) if outside else "the page never posted its half: open the page")
        out("pass" if passed else "fail", "drill in local mode", detail)
    except Exception as e:
        out("fail", "drill in local mode", type(e).__name__)
    return finish()


def finish() -> int:
    def f(x):
        return f"{x:.2f} s" if isinstance(x, (int, float)) else "n/a"
    parts = [LAT[k] for k in ("hear", "think", "speak")]
    total = sum(p for p in parts if isinstance(p, (int, float)))
    full = all(isinstance(p, (int, float)) for p in parts)
    print(f"hear {f(LAT['hear'])}, think {f(LAT['think'])}, speak {f(LAT['speak'])}, "
          f"total {f(total) if full else f(total) + ' (partial)'}")
    print(f"{RESULTS['pass']} pass, {RESULTS['fail']} fail, {RESULTS['warn']} warn")
    return 1 if RESULTS["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
