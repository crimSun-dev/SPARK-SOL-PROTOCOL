"""Hearing bay. Local Whisper, loaded once, kept resident.

`wake` is the small model: it only listens for an alias. `command` is
large-v3-turbo: it hears what Draven actually asked. Nothing here sends audio
anywhere; the only network this file can open is the one-time model download,
and that is logged when it happens.

One third-party import: faster-whisper==1.2.1 (with av==18.1.0 pinned beside it).
"""
from __future__ import annotations

import io
import struct
import threading
import time

from faster_whisper import WhisperModel, decode_audio

import netlog

SILENCE_MS = 700        # the page's constants carry the same names and values
FINISH_MS = 900
MIN_UTTERANCE_MS = 300

_MODELS: dict[str, WhisperModel] = {}
_STATE = {"status": "loading", "device": None, "error": None, "names": {}}
_LOCK = threading.Lock()          # one transcription at a time per model is plenty


def _silence_wav(seconds: float = 1.0, rate: int = 16000) -> bytes:
    n = int(seconds * rate)
    data = b"\x00\x00" * n
    head = b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " + struct.pack(
        "<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16) + b"data" + struct.pack("<I", len(data))
    return head + data


def _make(name: str, device: str, compute: str) -> WhisperModel:
    try:
        return WhisperModel(name, device=device, compute_type=compute,
                            local_files_only=True)
    except Exception:
        netlog.note("huggingface.co", f"one-time download of Whisper {name}")
        return WhisperModel(name, device=device, compute_type=compute)


def _warm(m: WhisperModel) -> None:
    segs, _ = m.transcribe(decode_audio(io.BytesIO(_silence_wav())),
                           language="en", beam_size=1)
    list(segs)                               # one second of silence


def _load_one(name: str) -> tuple[WhisperModel, str]:
    """CUDA float16 when the CUDA 12 libraries load; otherwise CPU int8.
    A CUDA failure often shows only at the first transcription, so warm here.
    After one CUDA failure, never try CUDA again in this process: on this
    machine (no cublas64_12.dll) a second CUDA model hangs in encode() forever
    instead of raising, found 2026-11-11."""
    if not _STATE.get("cuda_error"):
        try:
            m = _make(name, "cuda", "float16")
            _warm(m)
            return m, "cuda float16"
        except Exception as e:
            _STATE["cuda_error"] = f"{type(e).__name__}: {e}"[:200]
    m = _make(name, "cpu", "int8")
    _warm(m)
    return m, "cpu int8"


def load_models(cfg: dict) -> None:
    """Blocking. Run it on a thread so the server answers while the ears load."""
    names = {"wake": cfg.get("wake_model", "small"),
             "command": cfg.get("model", "large-v3-turbo")}
    _STATE["names"] = names
    try:
        for which, name in names.items():
            m, dev = _load_one(name)
            _MODELS[which] = m
            _STATE["device"] = dev
        _STATE["status"] = "ready"
    except Exception as e:                   # missing CUDA DLLs, no disk, no network
        _STATE["status"] = "down"
        _STATE["error"] = f"{type(e).__name__}: {e}"[:200]


def status() -> dict:
    return {"status": _STATE["status"], "device": _STATE["device"],
            "models": _STATE["names"], "error": _STATE["error"],
            "cuda_error": _STATE.get("cuda_error")}


def transcribe(wav: bytes, which: str = "command") -> tuple[str, float]:
    """Returns (text, seconds). `which` is 'wake' or 'command'."""
    if _STATE["status"] != "ready":
        raise RuntimeError("ears not ready: " + _STATE["status"])
    model = _MODELS["wake" if which == "wake" else "command"]
    t0 = time.perf_counter()
    audio = decode_audio(io.BytesIO(wav), sampling_rate=16000)
    with _LOCK:
        segs, _ = model.transcribe(audio, language="en",
                                   beam_size=1 if which == "wake" else 5,
                                   condition_on_previous_text=False,
                                   vad_filter=False)
        text = " ".join(s.text.strip() for s in segs).strip()
    return text, round(time.perf_counter() - t0, 3)
