"""Flaxeon's passkey for unattended indexer runs, kept with Windows DPAPI.

`cache/passkey.dpapi` holds the passkey encrypted for the current Windows user
on this machine (PowerShell `ConvertFrom-SecureString`, no key). Only that user
can decrypt it here. Git ignores `cache/`. The value is handed only to the
environment of one indexer run, and is never printed or logged.

    python passkey_store.py --check     # says whether the file decrypts and unlocks
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE = HERE / "cache" / "passkey.dpapi"


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def load() -> str | None:
    """The passkey, or None when there is no store or it does not decrypt."""
    try:
        raw = bytes.fromhex(STORE.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None
    buf = ctypes.create_string_buffer(raw, len(raw))
    blob_in, blob_out = _Blob(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), _Blob()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0,
                                                    ctypes.byref(blob_out)):
        return None
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData).decode("utf-16-le")
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


if __name__ == "__main__" and "--check" in sys.argv:
    key = load()
    if not key:
        print("no usable passkey store at", STORE)
        raise SystemExit(1)
    import os, subprocess
    env = {**os.environ, "FLAXEON_PASSKEY": key}
    code = ("import sys; sys.path.insert(0, '.'); from core.passkey import cloud_allowed; "
            "print('unlocks Flaxeon:', cloud_allowed())")
    out = subprocess.run([sys.executable, "-c", code], cwd=HERE.parent, env=env,
                         capture_output=True, text=True).stdout.strip()
    print(f"store decrypts ({len(key)} characters); {out}")
