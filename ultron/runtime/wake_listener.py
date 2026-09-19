"""Wake-word listener helpers."""

from __future__ import annotations

import os
import threading
import time

import numpy as np
import speech_recognition as sr

from ultron.audio.speech_backend import recognition_mode, transcribe_audio, SounddeviceMicrophone
from ultron.audio.wake_word import ALTERNATE_ULTRON_NAMES, analyze_wake_word, build_wake_word_config, fuzzy_wake_word_score
from ultron.health.observability import record_runtime_event

WAKE_WORD_CONFIG = build_wake_word_config()
WAKE_WORD = str(WAKE_WORD_CONFIG["wake_word"])
ACTIVE_TIMEOUT = int(os.getenv("JARVIS_ACTIVE_TIMEOUT", "60"))

# Said instead of the normal greeting when the user actually said one of the
# alternate names (e.g. "Jarvis") rather than "Ultron" itself, so the
# assistant still answers but is clear about its actual name.
ALTERNATE_NAME_GREETING = "My name is Ultron. How can I help you, boss?"
DEFAULT_GREETING = "At your service, sir."

_wake_recognizer = sr.Recognizer()
_wake_recognizer.energy_threshold = int(os.getenv("JARVIS_ENERGY_THRESHOLD", "200"))
_wake_recognizer.dynamic_energy_threshold = False  # Disable for better performance
_wake_recognizer.pause_threshold = 0.5  # Shorter pause detection for better responsiveness

active = False

# Real captured-audio level, shared with the UI so its voice meter reflects
# what the microphone actually picked up rather than a decorative animation.
_mic_level_lock = threading.Lock()
_mic_level = 0.0
_mic_level_updated_at = 0.0


def _update_mic_level(audio: sr.AudioData) -> float:
    """Compute a normalized 0-1 loudness level from a captured audio clip."""

    global _mic_level, _mic_level_updated_at
    try:
        samples = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32)
        rms = float(np.sqrt(np.mean(np.square(samples)))) if samples.size else 0.0
    except (ValueError, TypeError):
        rms = 0.0
    level = min(1.0, rms / 6000.0)
    with _mic_level_lock:
        _mic_level = level
        _mic_level_updated_at = time.time()
    return level


def _online_confirmation_match(online_text: str) -> str | None:
    """Decide whether an online-recognizer confirmation counts as the wake word.

    Only called after the offline fuzzy pre-filter already gated entry into
    this branch, so it can afford to accept a bit more than the strict
    offline alias list would - real usage logs repeatedly showed Google's
    recognizer clipping the trailing "n" and returning bare "Ultra" for a
    genuine "Ultron". "ultra" is not a general offline alias (too common a
    standalone word for that), but it is accepted here specifically.

    Returns the matched phrase (for greeting selection) or None.
    """

    analysis = analyze_wake_word(online_text, config=WAKE_WORD_CONFIG)
    if analysis["detected"]:
        return str(analysis["matched_phrase"])
    if "ultra" in online_text.lower().split():
        return "ultra"
    return None


def _greeting_for(matched_phrase: str | None) -> str:
    """Pick the spoken greeting based on which phrase actually triggered the wake."""

    if matched_phrase in ALTERNATE_ULTRON_NAMES:
        return ALTERNATE_NAME_GREETING
    return DEFAULT_GREETING


def get_mic_level(max_age: float = 1.5) -> float:
    """Return the most recent real microphone level, or 0.0 if it's stale."""

    with _mic_level_lock:
        level, updated_at = _mic_level, _mic_level_updated_at
    if time.time() - updated_at > max_age:
        return 0.0
    return level


def listen_for_wake_word(*, logger, send_log, speak=None) -> None:
    """Listen for the wake word in the background."""

    global active
    if not WAKE_WORD_CONFIG["enabled"]:
        send_log("[WARN] Wake-word mode disabled. Use text commands or push-to-talk.")
        record_runtime_event("wake_word", "Wake-word mode disabled", "warning", {"mode": recognition_mode()})
        return
    
    # Try to use sr.Microphone first, fall back to sounddevice
    microphone = None
    error_count = 0
    max_errors = 5
    
    try:
        microphone = sr.Microphone()
    except (AttributeError, RuntimeError):
        microphone = SounddeviceMicrophone()
    
    send_log("[INFO] Starting wake-word listener")
    
    while True:
        if active:
            # A command is being listened to/processed on another thread via
            # its own microphone handle - don't contend for the same audio
            # device at the same time, or PyAudio/PortAudio can raise errors
            # that eventually kill this thread silently.
            time.sleep(0.2)
            continue
        try:
            with microphone as source:
                # Optimize: skip ambient noise adjustment for better performance
                # _wake_recognizer.adjust_for_ambient_noise(source, duration=0.1)
                
                # Use shorter timeout and phrase limits for faster response
                audio = _wake_recognizer.listen(source, timeout=2, phrase_time_limit=3)
            
            # Only transcribe if we got audio
            if audio.frame_data:
                level = _update_mic_level(audio)
                text = transcribe_audio(_wake_recognizer, audio, language="en-US", prefer_offline=True)
                triggered = False
                matched_phrase = None
                logger.info(f"Captured audio: level={level:.2f} recognized={text!r}")
                if text:
                    score = fuzzy_wake_word_score(text, WAKE_WORD)
                    analysis = analyze_wake_word(text, config=WAKE_WORD_CONFIG)
                    if analysis["detected"]:
                        triggered = True
                        matched_phrase = str(analysis["matched_phrase"])
                    elif score >= 0.32:
                        # The compact offline model may not know an unusual
                        # wake word and substitutes the closest real word it
                        # does know (e.g. "Ultron" heard as "outrun"). Rather
                        # than silently miss it, or trust a loose match that
                        # could false-trigger on an unrelated real word, ask
                        # the more accurate online recognizer to confirm on
                        # this same audio before deciding.
                        try:
                            online_text = _wake_recognizer.recognize_google(audio, language="en-US")
                        except (sr.UnknownValueError, sr.RequestError):
                            online_text = ""
                        logger.info(f"Online confirmation heard: {online_text!r}")
                        if online_text:
                            matched_phrase = _online_confirmation_match(online_text)
                            triggered = matched_phrase is not None
                if triggered:
                    print("\n🟢 Wake word detected!")
                    send_log("WAKE WORD DETECTED")
                    record_runtime_event("wake_word", "Wake word detected", "info", {"mode": recognition_mode()})
                    if speak is not None:
                        # Speak fully before marking active, so the main
                        # loop never opens the command microphone while
                        # this thread's speaker output is still playing.
                        speak(_greeting_for(matched_phrase))
                    active = True
                    error_count = 0
            
            # Small sleep to prevent CPU spinning
            time.sleep(0.1)
            
        except sr.WaitTimeoutError:
            # Normal timeout - just continue listening
            logger.debug("Listen timeout - continuing")
            time.sleep(0.05)
            error_count = 0
        except (OSError, RuntimeError, ValueError) as e:
            error_count += 1
            logger.debug(f"Wake-word listener error ({error_count}/{max_errors}): {e}")
            if error_count >= max_errors:
                send_log(f"[WARN] Too many microphone errors. Disabling wake-word mode.")
                record_runtime_event("wake_word", "Too many errors, disabling", "warning", {"errors": error_count})
                return
            time.sleep(0.5)
        except AttributeError as e:
            # PyAudio not available - switch to text-only mode
            if "pyaudio" in str(e).lower():
                send_log("[WARN] Microphone/PyAudio not available. Running in text-only mode.")
                record_runtime_event("wake_word", "PyAudio unavailable, text-only mode", "warning", {"mode": "text-only"})
                return
            else:
                logger.debug("Wake-word listener encountered an attribute error.", exc_info=True)
                time.sleep(0.5)
        except Exception as e:  # noqa: BLE001 - last-resort guard so an unexpected
            # error logs and recovers instead of silently ending this thread.
            error_count += 1
            logger.warning("Unexpected wake-word listener error: %s", e, exc_info=True)
            send_log(f"[WARN] Unexpected wake-word listener error: {e}")
            record_runtime_event("wake_word", "Unexpected error", "warning", {"error": str(e)})
            if error_count >= max_errors:
                send_log("[WARN] Too many wake-word listener errors. Disabling wake-word mode.")
                record_runtime_event("wake_word", "Too many errors, disabling", "warning", {"errors": error_count})
                return
            time.sleep(0.5)
