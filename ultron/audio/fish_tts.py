"""Fish Audio TTS client - the "Ultron" character voice.

Used for everything Ultron speaks, live, via ses_motoru.py - not just the
pre-warmed fixed phrase set (see warm_fish_cache.py). Latency depends on
which voice model is configured (some Fish Audio models are near-instant,
others have several seconds of fixed overhead per request regardless of
text length); ses_motoru.py falls back to the local Edge TTS voice if a
call fails or the key isn't configured, and caches every result on disk
so repeats of the same text are always instant either way.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import requests

_API_URL = "https://api.fish.audio/v1/tts"
_DEFAULT_MODEL = "s2.1-pro-free"

FISH_CACHE_DIR = Path.home() / ".ultron" / "tts_cache" / "fish"


def fish_api_key() -> str:
    return os.getenv("FISH_AUDIO_API_KEY", "").strip()


def fish_voice_id() -> str:
    return os.getenv("FISH_AUDIO_VOICE_ID", "").strip()


def fish_model() -> str:
    return os.getenv("FISH_AUDIO_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL


def fish_enabled() -> bool:
    return bool(fish_api_key() and fish_voice_id())


def fish_cache_path(text: str) -> Path:
    key = hashlib.sha256(f"{fish_voice_id()}|{text}".encode("utf-8")).hexdigest()
    return FISH_CACHE_DIR / f"{key}.mp3"


def synthesize(text: str, *, timeout: float = 40.0) -> bytes | None:
    """Call Fish Audio's TTS API and return MP3 bytes, or None on failure."""

    if not fish_enabled():
        return None

    headers = {
        "Authorization": f"Bearer {fish_api_key()}",
        "Content-Type": "application/json",
        "model": fish_model(),
    }
    payload = {"text": text, "reference_id": fish_voice_id(), "format": "mp3"}

    try:
        response = requests.post(_API_URL, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException:
        return None

    if response.status_code != 200 or not response.content:
        return None

    return response.content


__all__ = [
    "FISH_CACHE_DIR",
    "fish_api_key",
    "fish_cache_path",
    "fish_enabled",
    "fish_model",
    "fish_voice_id",
    "synthesize",
]
