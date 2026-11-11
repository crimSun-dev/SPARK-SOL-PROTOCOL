"""Every outbound connection this process opens, with host and reason.

All HTTP from server.py and voice.py goes through `open_url`. Connections that
are not urllib (the Neon read through psycopg, a Whisper model download) are
recorded with `note`. The drill reads this list; nothing here is written to disk.
"""
from __future__ import annotations

import threading
import time
import urllib.request
from urllib.parse import urlsplit

_LOCK = threading.Lock()
LOG: list[dict] = []          # {"t": epoch seconds, "host": str, "reason": str}
LOCAL = {"localhost", "127.0.0.1", "::1"}


def note(host: str, reason: str) -> None:
    with _LOCK:
        LOG.append({"t": time.time(), "host": host or "?", "reason": reason})
        del LOG[:-500]


def open_url(req, reason: str, timeout: float):
    """urllib.request.urlopen, logged first. Accepts a Request or a URL."""
    url = req.full_url if isinstance(req, urllib.request.Request) else str(req)
    note(urlsplit(url).hostname or "?", reason)
    return urllib.request.urlopen(req, timeout=timeout)


def since(t: float) -> list[dict]:
    with _LOCK:
        return [dict(e) for e in LOG if e["t"] >= t]
