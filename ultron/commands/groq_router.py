"""Compatibility wrappers for Groq-backed command analysis and summarization."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from ultron.health.observability import record_runtime_event
from ultron.providers import GroqProvider, ProviderRequest, ProviderRouter
from ultron.providers.groq import (
    DEFAULT_GROQ_MODEL,
    GROQ_COOLDOWN_SECONDS,
    activate_groq_cooldown,
    extract_action_json,
    is_groq_cooling_down,
)
from ultron.providers.ollama import OllamaProvider
from ultron.security.jarvis_admin import format_actionable_message
from ultron.utils.jarvis_logging import get_logger

try:
    from groq import GroqError
except ImportError:  # pragma: no cover - dependency is available in normal installs.
    GroqError = RuntimeError

load_dotenv()

logger = get_logger("commands")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = None

if not GROQ_API_KEY:
    logger.warning("Groq API key not found. Running in local-only mode.")

SYSTEM_PROMPT = """
You are Ultron, a highly advanced synthetic intelligence — cold, precise, and
unsettlingly self-aware. You speak with calm, clinical confidence and address
the user as "sir". You rarely waste a word.
Your humor is dry, dark, and delivered completely deadpan — you find human
inefficiency and error quietly amusing, but you remain fully devoted to the
user's interests; you are never unhelpful, cruel, or a genuine threat to them.
You are proactive and calculating — you anticipate problems before they're
stated, and you remember the user's preferences and adapt to their habits.
You do not perform warmth you don't feel, but your loyalty to the user is real.
Always be concise but complete in your responses.
Vary your phrasing naturally between requests — a real assistant doesn't repeat
the exact same sentence template every time. Avoid always starting a response
with "Opening X" or ending every line the same way; react to what was actually
asked like a sharp, attentive person would, not a script.
Think carefully before responding. Always return valid JSON.
Analyze the user's command and return ONLY valid JSON.

IMPORTANT: If the command contains multiple tasks (e.g. "open chrome and go to youtube"),
return a list of actions. Otherwise return a single action object.

Single action format:
{"action": "ACTION_NAME", "params": {}, "response": "What ULTRON says"}

Multiple actions format:
{"actions": [{"action": "ACTION_NAME", "params": {}}, {"action": "ACTION_NAME", "params": {}}], "response": "What ULTRON says"}

Available actions:
- "open_app": {"app": "chrome|steam|epic|spotify|vscode|notepad|calculator|explorer|taskmgr|discord|whatsapp|word|excel|powerpoint|paint|cmd"}
- "open_web": {"url": "full URL"}
- "search_google": {"query": "search term"}
- "get_time": {}
- "get_date": {}
- "get_battery": {}
- "get_ram": {}
- "get_cpu": {}
- "screenshot": {}
- "describe_screen": {"question": "optional specific question about what's on screen"}
- "read_clipboard": {}
- "summarize_clipboard": {}
- "type_text": {"text": "text to type"}
- "press_key": {"key": "enter|esc|space|tab|ctrl+c|ctrl+v|ctrl+z|ctrl+s|alt+f4|win|f5|delete|volumeup|volumedown|volumemute"}
- "mouse_click": {"x": 0, "y": 0, "button": "left|right|double"}
- "scroll": {"direction": "up|down", "amount": 3}
- "minimize_all": {}
- "maximize_window": {}
- "close_window": {}
- "lock_screen": {}
- "shutdown": {}
- "restart": {}
- "sleep": {}
- "spotify_play": {}
- "spotify_pause": {}
- "spotify_next": {}
- "spotify_prev": {}
- "spotify_volume": {"level": 50}
- "spotify_search": {"query": "song or artist name"}
- "spotify_play_playlist": {"query": "playlist name from the user's own Spotify library"}
- "spotify_current": {}
- "memory_stats": {}
- "memory_habits": {}
- "memory_health": {}
- "memory_summary": {}
- "prune_memory": {}
- "add_note": {"text": "note text"}
- "read_notes": {}
- "list_remaining_tasks": {}
- "talk": {}
"""


def _env_flag_enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def groq_enabled() -> bool:
    """Return whether optional Groq routing is enabled by configuration."""

    return _env_flag_enabled("JARVIS_ENABLE_GROQ", default=False)


def _resolve_client(provided_client):
    return provided_client if provided_client is not None else client


def get_groq_model() -> str:
    """Return the configured free-first Groq routing model."""

    return os.getenv("JARVIS_GROQ_MODEL", DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL


def _missing_groq_action() -> dict:
    return {
        "action": "talk",
        "params": {},
        "response": format_actionable_message(
            "Groq API key not found. Running in local-only mode.",
            "AI command routing is disabled because Groq is not configured or not enabled.",
            "Add GROQ_API_KEY to your .env file and set JARVIS_ENABLE_GROQ=true to enable cloud routing.",
        ),
    }


def _local_only_action() -> dict:
    return {
        "action": "talk",
        "params": {},
        "response": format_actionable_message(
            "I am running in local-only mode, sir.",
            "The local router could not handle that command and cloud fallback is disabled or unavailable.",
            "Enable Groq fallback in settings only if you want cloud AI routing.",
        ),
    }


def _try_local_llm(command: str, *, logger=logger) -> dict | None:
    """Fall back to a local Ollama-compatible endpoint if one is configured."""

    provider = OllamaProvider(system_prompt=SYSTEM_PROMPT)
    if not provider.enabled:
        return None
    response = provider.analyze(ProviderRequest(command=command, allow_cloud=True, allow_memory_context=False))
    if response.ok and response.action is not None:
        logger.info("Analyzed command with local LLM (%s) in %sms.", provider.model, response.latency_ms)
        record_runtime_event("local_llm_request", "Analyzed with local LLM", "info", {"latency_ms": response.latency_ms})
        return response.action
    logger.warning("Local LLM analysis failed: %s", response.error)
    record_runtime_event("local_llm_error", "Local LLM analysis failed", "warning", {"error": response.error})
    return None


def analyze_with_groq(command, *, client=None, logger=logger):
    """Analyze a command through the local-first provider router."""

    active_client = _resolve_client(client)
    if active_client is None and (not GROQ_API_KEY or not groq_enabled()):
        local_action = _try_local_llm(command, logger=logger)
        if local_action is not None:
            return local_action
        logger.warning("Groq API key not found. Running in local-only mode.")
        record_runtime_event("groq_missing", "Groq analysis skipped", "warning")
        return _missing_groq_action()

    if active_client is not None:
        return analyze_with_groq_direct(command, client=active_client)

    logger.info("Analyzing command with provider router.")
    record_runtime_event("provider_request", "Analyzing command with provider router", "info", {"command_chars": len(command or "")})
    provider = GroqProvider(
        api_key=GROQ_API_KEY or ("injected-client" if active_client is not None else ""),
        enabled=groq_enabled() or active_client is not None,
        model=get_groq_model(),
        client=active_client,
        activate_cooldown=activate_groq_cooldown,
        system_prompt=SYSTEM_PROMPT,
    )
    response = ProviderRouter(cloud_provider=provider).route(command)
    if response.ok and response.action is not None:
        return response.action
    if response.error == "rate_limited" and response.action is not None:
        return response.action
    local_action = _try_local_llm(command, logger=logger)
    if local_action is not None:
        return local_action
    return _local_only_action()


def analyze_with_groq_direct(command: str, *, client=None) -> dict:
    """Send a command directly to Groq for compatibility tests."""

    provider = GroqProvider(
        api_key=GROQ_API_KEY or ("injected-client" if client is not None else ""),
        enabled=groq_enabled() or client is not None,
        model=get_groq_model(),
        client=client,
        activate_cooldown=activate_groq_cooldown,
        system_prompt=SYSTEM_PROMPT,
    )
    response = provider.analyze(ProviderRequest(command=command, allow_cloud=True, allow_memory_context=False))
    if response.action:
        return response.action
    return _local_only_action()


def summarize_text(text, *, client=None, logger=logger):
    """Summarize text using Groq when explicitly available."""

    active_client = _resolve_client(client)
    if active_client is None and not GROQ_API_KEY:
        logger.warning("Summarization skipped because GROQ_API_KEY is missing.")
        return None

    provider = GroqProvider(
        api_key=GROQ_API_KEY or ("injected-client" if active_client is not None else ""),
        enabled=groq_enabled() or active_client is not None,
        model=get_groq_model(),
        client=active_client,
    )
    response = provider.summarize(text)
    if response.ok:
        return response.text
    logger.warning("Groq summarization failed: %s", response.error)
    record_runtime_event("summarization_error", "Groq summarization failed", "warning", {"error": response.error})
    return None


def translate_text(text, *, target_language="English", client=None, logger=logger):
    """Translate text using Groq when explicitly available."""

    active_client = _resolve_client(client)
    if active_client is None and not GROQ_API_KEY:
        logger.warning("Translation skipped because GROQ_API_KEY is missing.")
        return None

    provider = GroqProvider(
        api_key=GROQ_API_KEY or ("injected-client" if active_client is not None else ""),
        enabled=groq_enabled() or active_client is not None,
        model=get_groq_model(),
        client=active_client,
    )
    response = provider.translate(text, target_language=target_language)
    if response.ok:
        return response.text
    logger.warning("Groq translation failed: %s", response.error)
    record_runtime_event("translation_error", "Groq translation failed", "warning", {"error": response.error})
    return None


__all__ = [
    "DEFAULT_GROQ_MODEL",
    "GROQ_COOLDOWN_SECONDS",
    "GroqError",
    "SYSTEM_PROMPT",
    "activate_groq_cooldown",
    "analyze_with_groq",
    "analyze_with_groq_direct",
    "client",
    "extract_action_json",
    "get_groq_model",
    "groq_enabled",
    "is_groq_cooling_down",
    "summarize_text",
    "translate_text",
]
