"""Runtime loop for ULTRON."""

from __future__ import annotations

import threading
import time

from open_jarvis.audio.ses_motoru import speak
from open_jarvis.audio.speech_backend import recognition_mode
from open_jarvis.commands.komutlar import process_command
from open_jarvis.health.observability import record_runtime_event
from open_jarvis.runtime import orchestrator as runtime_orchestrator
from open_jarvis.runtime import readiness as runtime_readiness
from open_jarvis.runtime import timer as timer_runtime
from open_jarvis.runtime import ui_bridge
from open_jarvis.runtime import voice_personality as personality_runtime
from open_jarvis.runtime import wake_listener as wake_state
from open_jarvis.runtime import wake_word as voice_runtime
from open_jarvis.utils.jarvis_logging import get_logger

logger = get_logger("main")

_state = {"command_count": 0, "joke_interval": 5}


def set_ui_callback(fn):
    ui_bridge.set_ui_callback(fn)


def send_log(message):
    ui_bridge.send_log(message)


def maybe_tell_joke():
    personality_runtime.maybe_tell_joke(
        speak=speak,
        send_log=send_log,
        logger=logger,
        state=_state,
    )


def say_goodbye():
    personality_runtime.say_goodbye(speak=speak, send_log=send_log, logger=logger)


def parse_duration(command):
    return timer_runtime.parse_duration(command)


def start_timer(seconds, message="Time is up, sir."):
    return timer_runtime.start_timer(seconds, message, speak=speak, send_log=send_log, logger=logger)


def handle_timer_command(command):
    return timer_runtime.handle_timer_command(command, speak=speak, send_log=send_log, logger=logger)


def listen_for_wake_word():
    return wake_state.listen_for_wake_word(logger=logger, send_log=send_log, speak=speak)


def listen_for_command():
    return voice_runtime.listen_for_command(speak=speak, send_log=send_log, logger=logger)


def start_jarvis():
    """Run the main voice loop."""

    print(
        """
╔═══════════════════════════════════════════════╗
║            ULTRON  Starting...               ║
╚═══════════════════════════════════════════════╝
        """
    )

    logger.info("ULTRON startup sequence initiated.")
    record_runtime_event("startup", "ULTRON startup sequence initiated", "info", {"offline_stt": recognition_mode()})
    runtime_readiness.emit_startup_readiness(send_log=send_log, recognition_mode=recognition_mode)

    threading.Thread(target=listen_for_wake_word, daemon=True).start()
    logger.info("Wake word listener thread started.")
    print(f'💤 Standby mode — say "{voice_runtime.WAKE_WORD}" to activate...')

    running = True
    while running:
        if not wake_state.active:
            time.sleep(0.2)
            continue

        command = listen_for_command()

        if command:
            running = runtime_orchestrator.handle_runtime_command(
                command,
                logger=logger,
                process_command=process_command,
                handle_timer_command=handle_timer_command,
                say_goodbye=say_goodbye,
                maybe_tell_joke=maybe_tell_joke,
                record_runtime_event=record_runtime_event,
                wake_state=wake_state,
            )
            if not running:
                continue

        # Siri-style: handle exactly one command per wake word, then require
        # "Jarvis" again instead of continuing to listen in the background.
        wake_state.active = False
        logger.info("Returned to standby mode.")
        print(f'💤 Returned to standby — say "{voice_runtime.WAKE_WORD}" to activate...')
