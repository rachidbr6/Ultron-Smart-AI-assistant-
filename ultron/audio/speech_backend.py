"""Speech recognition helpers with an optional offline Vosk fallback."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from json import JSONDecodeError
from pathlib import Path

import speech_recognition as sr

# Try to use sounddevice as fallback for PyAudio
try:
    import sounddevice
    import numpy as np
    SOUNDDEVICE_AVAILABLE = True
    
    # Configure default sample rate
    sounddevice.default.samplerate = 16000
except ImportError:
    SOUNDDEVICE_AVAILABLE = False


def _candidate_model_roots() -> list[Path]:
    candidates = []

    env_path = os.getenv("JARVIS_VOSK_MODEL_PATH") or os.getenv("VOSK_MODEL_PATH")
    if env_path:
        candidates.append(Path(env_path))

    home = Path.home()
    candidates.extend(
        [
            home / ".ultron" / "vosk_models",
            home / ".ultron" / "vosk_model",
            home / "AppData" / "Local" / "Open.Jarvis" / "vosk_models",
            Path(__file__).resolve().parent / "model",
            Path(__file__).resolve().parent / "models" / "vosk-model-small-en-us-0.15",
        ]
    )

    return candidates


def _looks_like_model(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    return any((path / marker).exists() for marker in ["am", "graph", "conf"])


def resolve_vosk_model_path() -> Path | None:
    """Resolve a usable Vosk model directory if one is available."""

    for root in _candidate_model_roots():
        if root.is_dir() and (root / "am").exists():
            return root
        if root.is_dir():
            for child in root.iterdir():
                if _looks_like_model(child):
                    return child
    return None


@lru_cache(maxsize=1)
def _load_vosk_model():
    model_path = resolve_vosk_model_path()
    if model_path is None:
        return None

    try:
        from vosk import Model

        return Model(str(model_path))
    except (ImportError, OSError, RuntimeError, ValueError):
        return None


def offline_stt_available() -> bool:
    """Return True when an offline model can be loaded."""

    return _load_vosk_model() is not None


def transcribe_audio_offline(audio: sr.AudioData) -> str | None:
    """Transcribe audio using Vosk when available."""

    model = _load_vosk_model()
    if model is None:
        return None

    try:
        from vosk import KaldiRecognizer

        recognizer = KaldiRecognizer(model, 16000)
        recognizer.AcceptWaveform(audio.get_raw_data(convert_rate=16000, convert_width=2))
        result = json.loads(recognizer.FinalResult())
        text = result.get("text", "").strip()
        return text or None
    except (ImportError, OSError, RuntimeError, ValueError, JSONDecodeError):
        return None


def transcribe_audio(
    recognizer: sr.Recognizer,
    audio: sr.AudioData,
    language: str = "en-US",
    prefer_offline: bool = False,
) -> str | None:
    """Try online speech recognition first, then offline fallback."""

    if prefer_offline and offline_stt_available():
        offline = transcribe_audio_offline(audio)
        if offline:
            return offline

    try:
        return recognizer.recognize_google(audio, language=language)
    except (sr.UnknownValueError, sr.RequestError):
        if offline_stt_available():
            return transcribe_audio_offline(audio)
        return None


def recognition_mode() -> str:
    """Expose the currently available recognition mode for health checks."""

    return "offline" if offline_stt_available() else "online"


class SounddeviceMicrophone(sr.AudioSource):
    """Context manager for recording audio using sounddevice instead of PyAudio."""
    
    def __init__(self, device_index=None, sample_rate=16000):
        self.sample_rate = sample_rate
        
        # Auto-detect best microphone if not specified
        if device_index is None:
            self.device_index = self._find_best_microphone()
        else:
            self.device_index = device_index
            
        self.audio_data = None
        self.CHUNK = 1024
        self.format = 2  # 16-bit
        self.channels = 1
    
    @staticmethod
    def _find_best_microphone():
        """Find the best available microphone device."""
        if not SOUNDDEVICE_AVAILABLE:
            return None
        
        try:
            devices = sd.query_devices()
            best_mic = None
            
            # Priority 1: Realtek Mic Array (usually the best)
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = device['name'].lower()
                    if 'realtek' in name and 'mic array' in name:
                        return i
            
            # Priority 2: Regular Realtek microphone
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = device['name'].lower()
                    if 'realtek' in name and 'mic' in name:
                        return i
            
            # Priority 3: Any microphone device
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = device['name'].lower()
                    if 'microphone' in name or 'mic' in name:
                        return i
            
            # Fall back to first input device with 2+ channels (usually works better)
            for i, device in enumerate(devices):
                if device['max_input_channels'] >= 2:
                    return i
            
            # Last resort: any input device
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    return i
            
            return None
        except Exception:
            return None
        
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
        
    def listen(self, recognizer, timeout=None, phrase_time_limit=None):
        """Record audio using sounddevice and return sr.AudioData."""
        
        if not SOUNDDEVICE_AVAILABLE:
            raise RuntimeError("sounddevice not available")
        
        # Record audio
        duration = phrase_time_limit or 5  # Default 5 second recording
        try:
            audio = sounddevice.rec(int(self.sample_rate * duration), 
                                   samplerate=self.sample_rate, 
                                   channels=self.channels, 
                                   dtype='int16',
                                   device=self.device_index)
            sounddevice.wait()
            
            # Convert numpy array to bytes
            audio_bytes = audio.tobytes()
            
            # Return as sr.AudioData
            return sr.AudioData(audio_bytes, self.sample_rate, 2)
        except Exception as e:
            raise RuntimeError(f"Error recording audio: {e}")
    
    def adjust_for_ambient_noise(self, recognizer=None, duration=1):
        """Placeholder for ambient noise adjustment."""
        # sounddevice doesn't need explicit ambient noise adjustment
        pass
