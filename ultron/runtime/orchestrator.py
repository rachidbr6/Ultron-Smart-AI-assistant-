"""High-level runtime orchestration helpers."""

from __future__ import annotations


def handle_runtime_command(
    command: str,
    *,
    logger,
    process_command,
    handle_timer_command,
    say_goodbye,
    maybe_tell_joke,
    record_runtime_event,
    wake_state,
) -> bool:
    """Handle one recognized command and return whether the loop should continue."""

    if any(k in command for k in ["goodbye ultron", "shut down ultron", "bye ultron", "goodbye jarvis", "shut down jarvis", "bye jarvis"]):
        logger.info("Shutdown command received.")
        record_runtime_event("shutdown", "Shutdown command received", "info")
        say_goodbye()
        return False

    if handle_timer_command(command):
        logger.info("Timer command handled without Groq.")
        wake_state.active = False
        return True

    running = process_command(command)
    logger.info("Process command returned %s", running)
    record_runtime_event("command_executed", command, "info", {"running": running})

    if running:
        maybe_tell_joke()
    return bool(running)
