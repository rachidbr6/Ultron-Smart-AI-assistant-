"""
VOICE ENGINE - Microsoft Edge TTS
Manages ULTRON speech output.
"""

import asyncio
import hashlib
import io
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import edge_tts
import numpy as np
from edge_tts.exceptions import EdgeTTSException

from ultron.audio.fish_tts import fish_cache_path
from ultron.runtime.ui_bridge import send_log, send_state

AUDIO_AVAILABLE = False
try:
    import pygame

    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except ImportError:
    send_log("[WARN] pygame not installed. Voice output disabled.")
except pygame.error as exc:  # pragma: no cover - depends on local audio hardware
    send_log(f"[WARN] Audio device initialization failed: {exc}")

VOICE = "en-GB-RyanNeural"
RATE = "+15%"  # Faster than natural pace - every spoken response is shorter
PITCH = "-20Hz"  # Deeper register for a more synthetic, Ultron-like tone

# Fixed phrases (wake acknowledgement, jokes, tips, boilerplate errors) are
# spoken identically every time - cache their fully processed audio on disk
# so repeats skip both the network round-trip and the effect processing below.
_TTS_CACHE_DIR = Path.home() / ".ultron" / "tts_cache"


def _cache_path(text: str) -> Path:
    key = hashlib.sha256(f"{VOICE}|{RATE}|{PITCH}|{text}".encode("utf-8")).hexdigest()
    return _TTS_CACHE_DIR / f"{key}.wav"


def _resolve_ffmpeg() -> str | None:
    """Locate ffmpeg even when a stale PATH hasn't picked up a fresh install yet."""

    on_path = shutil.which("ffmpeg")
    if on_path:
        return on_path

    search_roots = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
        Path("C:/ffmpeg"),
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "ffmpeg",
    ]
    for root in search_roots:
        if not root.is_dir():
            continue
        for candidate in root.rglob("ffmpeg.exe"):
            return str(candidate)
    return None


def _mp3_to_pcm(mp3_bytes: bytes) -> tuple[np.ndarray, int] | None:
    """Decode MP3 bytes to mono 16-bit PCM samples via ffmpeg. None if unavailable."""

    ffmpeg_path = _resolve_ffmpeg()
    if not ffmpeg_path:
        return None

    sample_rate = 24000
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as handle:
        handle.write(mp3_bytes)
        mp3_path = handle.name
    wav_path = mp3_path[:-4] + ".wav"
    try:
        result = subprocess.run(
            [ffmpeg_path, "-y", "-i", mp3_path, "-ar", str(sample_rate), "-ac", "1", "-sample_fmt", "s16", wav_path],
            capture_output=True,
            timeout=10,
        )
        if result.returncode != 0 or not os.path.exists(wav_path):
            return None
        with wave.open(wav_path, "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            actual_rate = wav_file.getframerate()
        return np.frombuffer(frames, dtype=np.int16).astype(np.float32), actual_rate
    finally:
        for path in (mp3_path, wav_path):
            if os.path.exists(path):
                os.unlink(path)


def _robotize(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    """Blend in a subtle ring-modulated, slightly gritty texture for a synthetic AI tone."""

    t = np.arange(len(samples)) / sample_rate
    modulator = np.sin(2 * np.pi * 45.0 * t)
    modulated = samples * modulator
    mixed = samples * 0.82 + modulated * 0.18

    step = 600.0  # light bit-depth reduction for subtle digital grit
    mixed = np.round(mixed / step) * step

    peak = np.max(np.abs(mixed)) or 1.0
    original_peak = np.max(np.abs(samples)) or 1.0
    mixed = mixed / peak * original_peak
    return np.clip(mixed, -32768, 32767).astype(np.int16)


def _pcm_to_wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples.tobytes())
    return buffer.getvalue()


async def _synthesize_raw(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=RATE, pitch=PITCH)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


async def _synthesize(text: str) -> bytes:
    """Synthesize speech and apply the robotic effect, falling back to the plain voice on failure."""

    mp3_data = await _synthesize_raw(text)
    if not mp3_data:
        return mp3_data

    try:
        decoded = _mp3_to_pcm(mp3_data)
        if decoded is None:
            return mp3_data
        samples, sample_rate = decoded
        processed = _robotize(samples, sample_rate)
        return _pcm_to_wav_bytes(processed, sample_rate)
    except (OSError, RuntimeError, ValueError) as exc:
        send_log(f"[WARN] Voice effect processing failed, using plain voice: {exc}")
        return mp3_data


async def _get_audio(text: str) -> bytes:
    # Fish Audio's "Ultron" character voice is pre-generated offline for the
    # known fixed phrase set (see warm_fish_cache.py) - it costs ~18s per
    # call so it is never synthesized live here, only read back if cached.
    fish_cache_file = fish_cache_path(text)
    if fish_cache_file.exists():
        try:
            return fish_cache_file.read_bytes()
        except OSError:
            pass

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
