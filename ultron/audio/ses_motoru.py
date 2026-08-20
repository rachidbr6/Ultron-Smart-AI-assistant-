"""
VOICE ENGINE - Microsoft Edge TTS
Manages JARVIS speech output.
"""

import asyncio
import hashlib
import io
from pathlib import Path

import edge_tts
from edge_tts.exceptions import EdgeTTSException

from ultron.runtime.ui_bridge import send_log, send_state

# Play synthesized MP3 audio directly through pygame's mixer (no ffmpeg/WAV
# conversion round-trip needed - it decodes MP3 natively).
AUDIO_AVAILABLE = False
try:
    import pygame

    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except ImportError:
    send_log("[WARN] pygame not installed. Voice output disabled.")
except pygame.error as exc:  # pragma: no cover - depends on local audio hardware
    send_log(f"[WARN] Audio device initialization failed: {exc}")

VOICE = "en-GB-RyanNeural"  # Closest to Iron Man JARVIS voice
RATE = "+15%"  # Faster than natural pace - every spoken response is shorter
PITCH = "-12Hz"

# Fixed phrases (wake acknowledgement, jokes, tips, boilerplate errors) are
# spoken identically every time - cache their synthesized audio on disk so
# repeats skip the network round-trip to Edge TTS entirely.
_TTS_CACHE_DIR = Path.home() / ".ultron" / "tts_cache"


def _cache_path(text: str) -> Path:
    key = hashlib.sha256(f"{VOICE}|{RATE}|{PITCH}|{text}".encode("utf-8")).hexdigest()
    return _TTS_CACHE_DIR / f"{key}.mp3"


async def _synthesize(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE, pitch=PITCH)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


async def _get_audio(text: str) -> bytes:
    cache_file = _cache_path(text)
    if cache_file.exists():
        try:
            return cache_file.read_bytes()
        except OSError:
            pass  # fall through and re-synthesize

    audio_data = await _synthesize(text)
    if audio_data:
        try:
            _TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file.write_bytes(audio_data)
        except OSError:
            pass  # caching is an optimization, not a requirement
    return audio_data


async def _speak_async(text: str):
    if not AUDIO_AVAILABLE:
        return

    audio_data = await _get_audio(text)

    if not audio_data:
        return

    try:
        pygame.mixer.music.load(io.BytesIO(audio_data))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.05)
    except (OSError, RuntimeError, pygame.error) as exc:
        send_log(f"[WARN] Audio playback failed: {exc}")


def speak(text: str):
    send_state("SPEAKING", "Voice response active")
    send_log(f"[SPEAKING] Speaking started: {text[:120]}")
    print(f"ULTRON: {text}")
    try:
        asyncio.run(_speak_async(text))
    except (EdgeTTSException, OSError, RuntimeError) as exc:
        send_log(f"[WARN] Voice output failed: {exc}")
    finally:
        send_log("[OK] Speaking completed")


if __name__ == "__main__":
    speak("All systems online. Ultron is ready, sir.")
