"""Voice bay. VoiceStudio on this machine, pinned engine, the Spark profile.

Routes checked against VoiceStudio 0.5.7's own /openapi.json on 2026-11-11:
POST /engines/select {family, backend_id, model_id}; GET /profiles (a list of
{id, name, ...}); POST /v1/audio/speech {model, input, voice, response_format,
language}. Speech itself is NOT YET VERIFIED: the voxcpm2 backend was still
installing and no Spark profile existed. Every failure raises VoiceUnavailable
and the page falls back to the browser.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import netlog

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache" / "tts"
MAX_CHARS = 600
IDLE_WARM_S = 600


class VoiceUnavailable(Exception):
    pass


_CFG: dict = {}
_STATE = {"profile_id": None, "selected_for": None, "error": "not started",
          "last_use": time.time()}
_LOCK = threading.Lock()


def configure(cfg: dict) -> None:
    _CFG.clear()
    _CFG.update(cfg)


def _url(path: str) -> str:
    return _CFG.get("url", "http://127.0.0.1:3900").rstrip("/") + path


def _json(method: str, path: str, body=None, timeout: float = 5.0, reason="voice"):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(_url(path), data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with netlog.open_url(req, reason, timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def health() -> dict:
    """One second, or the voice is unavailable."""
    try:
        return _json("GET", "/health", timeout=1.0, reason="voice health")
    except Exception as e:
        _STATE["error"] = f"/health: {type(e).__name__}"
        raise VoiceUnavailable(_STATE["error"]) from e


def _profiles(data) -> list:
    if isinstance(data, list):
        return data
    for k in ("profiles", "data", "items"):
        if isinstance(data, dict) and isinstance(data.get(k), list):
            return data[k]
    return []


def select_engine() -> str:
    """POST /engines/select with the pinned engine, then resolve Spark by name.
    Runs at boot and again whenever VoiceStudio's run changes."""
    h = health()
    run = json.dumps({k: h.get(k) for k in ("pid", "started_at", "uptime_id", "run_id")},
                     sort_keys=True)
    with _LOCK:
        if _STATE["profile_id"] and _STATE["selected_for"] == run:
            return _STATE["profile_id"]
        try:
            _json("POST", "/engines/select",
                  {"family": "tts", "backend_id": _CFG.get("engine", "voxcpm2"),
                   "model_id": _CFG.get("model_id", "voxcpm2")},
                  timeout=30, reason="voice engine select")
            want = _CFG.get("profile", "Spark").lower()
            for p in _profiles(_json("GET", "/profiles", reason="voice profiles")):
                if isinstance(p, dict) and str(p.get("name", "")).lower() == want:
                    _STATE["profile_id"] = p.get("id") or p.get("profile_id")
                    break
            else:
                raise VoiceUnavailable(f"no profile named {_CFG.get('profile', 'Spark')}")
        except VoiceUnavailable as e:
            _STATE["error"] = str(e)
            raise
        except urllib.error.HTTPError as e:
            try:
                detail = json.loads(e.read()).get("detail", "")
            except Exception:
                detail = ""
            _STATE["error"] = f"select: HTTP {e.code} {str(detail)[:140]}".strip()
            raise VoiceUnavailable(_STATE["error"]) from e
        except Exception as e:
            _STATE["error"] = f"select: {type(e).__name__}"
            raise VoiceUnavailable(_STATE["error"]) from e
        _STATE["selected_for"] = run
        _STATE["error"] = None
        return _STATE["profile_id"]


_SEEN = {"status": "down", "health": None, "t": 0.0}


def watch(stop: threading.Event, every: float = 5.0) -> None:
    """Poll /health in the background so no request waits on a closed port.
    When VoiceStudio comes up (or restarts), select the pinned engine again."""
    # VoiceStudio 0.5.7's /health is {status, device, version}: no run id. A new
    # engine run shows up as down-then-up, which forces a fresh select.
    last_fail = 0.0
    while True:
        try:
            h = health()
            if _SEEN["status"] == "down":
                _STATE["profile_id"] = None
            if _STATE["profile_id"] or time.time() - last_fail > 60:
                try:
                    select_engine()
                    _SEEN.update(status="ready", health=h)
                except VoiceUnavailable:
                    last_fail = time.time()          # do not re-post a failing select every 5 s
                    _SEEN.update(status="selecting", health=h)
        except VoiceUnavailable:
            _SEEN.update(status="down", health=None)
        _SEEN["t"] = time.time()
        if stop.wait(every):
            return


def is_up() -> bool:
    return _SEEN["status"] == "ready"


def status() -> dict:
    """The last reading from watch(). Never blocks."""
    return {"status": _SEEN["status"], "engine": _CFG.get("engine"),
            "model_id": _CFG.get("model_id"), "profile": _CFG.get("profile"),
            "health": _SEEN["health"], "checked": _SEEN["t"], "error": _STATE["error"]}


def header() -> str:
    return "local:" + _CFG.get("profile", "Spark")


def synthesize(text: str) -> bytes:
    """WAV bytes for at most 600 characters. Disk cache by text plus profile."""
    text = re.sub(r"\s+", " ", text or "").strip()[:MAX_CHARS]
    if not text:
        raise ValueError("empty text")
    profile_id = select_engine()
    key = hashlib.sha256((str(profile_id) + "\n" + _CFG.get("profile", "") + "\n" + text)
                         .encode()).hexdigest()[:32]
    path = CACHE / (key + ".wav")
    _STATE["last_use"] = time.time()
    if path.exists():
        return path.read_bytes()
    body = {"model": _CFG.get("model_id", "voxcpm2"), "input": text,
            "voice": profile_id, "response_format": "wav",
            "language": _CFG.get("language", "en")}
    req = urllib.request.Request(_url("/v1/audio/speech"), data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with netlog.open_url(req, "voice speech", 120) as r:
            wav = r.read()
    except Exception as e:
        _STATE["profile_id"] = None          # force a re-select on the next call
        raise VoiceUnavailable(f"speech: {type(e).__name__}") from e
    if wav[:4] != b"RIFF":
        raise VoiceUnavailable("speech: reply was not a WAV")
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(wav)
    tmp.replace(path)
    return wav


def keep_warm(stop: threading.Event) -> None:
    """Every ten idle minutes, render 'Standing by.' and throw the audio away."""
    while not stop.wait(30):
        if time.time() - _STATE["last_use"] < IDLE_WARM_S:
            continue
        try:
            profile_id = select_engine()
            body = {"model": _CFG.get("model_id", "voxcpm2"), "input": "Standing by.",
                    "voice": profile_id, "response_format": "wav",
                    "language": _CFG.get("language", "en")}
            req = urllib.request.Request(_url("/v1/audio/speech"),
                                         data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with netlog.open_url(req, "voice keep-warm", 120) as r:
                r.read()
        except Exception:
            pass
        _STATE["last_use"] = time.time()


def split_chunks(answer: str, limit: int = 170) -> list[str]:
    """Sentence-packed, about `limit` characters. Never cuts inside a sentence;
    the first chunk is not shortened to start sooner."""
    sentences = [s for s in re.split(r"(?<=[.!?…])\s+", (answer or "").strip()) if s]
    out, cur = [], ""
    for s in sentences:
        if cur and len(cur) + 1 + len(s) > limit:
            out.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        out.append(cur)
    return out
