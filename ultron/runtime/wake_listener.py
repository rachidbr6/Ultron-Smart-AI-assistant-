"""Wake-word listener helpers."""

from __future__ import annotations

import os
import time

import speech_recognition as sr

from ultron.audio.speech_backend import recognition_mode, transcribe_audio, SounddeviceMicrophone
from ultron.audio.wake_word import build_wake_word_config, fuzzy_wake_word_score, wake_word_detected
from ultron.health.observability import record_runtime_event

WAKE_WORD_CONFIG = build_wake_word_config()
WAKE_WORD = str(WAKE_WORD_CONFIG["wake_word"])
ACTIVE_TIMEOUT = int(os.getenv("JARVIS_ACTIVE_TIMEOUT", "60"))

_wake_recognizer = sr.Recognizer()
_wake_recognizer.energy_threshold = int(os.getenv("JARVIS_ENERGY_THRESHOLD", "200"))
_wake_recognizer.dynamic_energy_threshold = False  # Disable for better performance
_wake_recognizer.pause_threshold = 0.5  # Shorter pause detection for better responsiveness

active = False


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
                text = transcribe_audio(_wake_recognizer, audio, language="en-US", prefer_offline=True)
                triggered = False
                if text:
                    score = fuzzy_wake_word_score(text, WAKE_WORD)
                    logger.info(f"Heard (offline): {text!r} (fuzzy score={score:.2f})")
                    if wake_word_detected(text, config=WAKE_WORD_CONFIG):
                        triggered = True
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
                            triggered = wake_word_detected(online_text, config=WAKE_WORD_CONFIG)
                if triggered:
                    print("\n🟢 Wake word detected!")
                    send_log("WAKE WORD DETECTED")
                    record_runtime_event("wake_word", "Wake word detected", "info", {"mode": recognition_mode()})
                    if speak is not None:
                        # Speak fully before marking active, so the main
                        # loop never opens the command microphone while
                        # this thread's speaker output is still playing.
                        speak("At your service, sir.")
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
