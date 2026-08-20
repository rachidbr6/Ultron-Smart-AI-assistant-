"""Wake-word configuration and matching without microphone dependencies."""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from difflib import SequenceMatcher

_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}


def parse_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return default


def normalize_voice_phrase(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", " ", text.lower())
    return " ".join(normalized.split())


def fuzzy_wake_word_score(text: str, wake_word: str) -> float:
    """Return the best character-similarity ratio between any token (or the
    whole phrase) in text and wake_word.

    Small offline speech models often substitute an unusual wake word (e.g.
    a name not in their compact vocabulary) with the closest real word they
    know. This score is deliberately loose - it is meant to decide whether a
    result is worth a slower, more accurate confirmation pass, not to be the
    final accept/reject decision on its own (see analyze_wake_word).
    """

    normalized_text = normalize_voice_phrase(text)
    normalized_word = normalize_voice_phrase(wake_word)
    if not normalized_text or not normalized_word:
        return 0.0
    tokens = normalized_text.split()
    candidates = [*tokens, "".join(tokens)]
    return max(SequenceMatcher(None, candidate, normalized_word).ratio() for candidate in candidates)


@dataclass(frozen=True)
class WakeWordConfig:
    wake_word: str = "jarvis"
    enabled: bool = True
    voice_enabled: bool = True
    cooldown_seconds: float = 1.0
    aliases: tuple[str, ...] = ()


def build_wake_word_config(env: Mapping[str, str] | None = None) -> dict[str, object]:
    source = os.environ if env is None else env
    wake_word = normalize_voice_phrase(source.get("JARVIS_WAKE_WORD", "jarvis")) or "jarvis"
    voice_enabled = parse_bool(source.get("JARVIS_VOICE_ENABLED"), True)
    enabled = parse_bool(source.get("JARVIS_WAKE_WORD_ENABLED"), True) and voice_enabled
    try:
        cooldown_seconds = max(0.0, float(source.get("JARVIS_WAKE_WORD_COOLDOWN_SECONDS", "1.0")))
    except (TypeError, ValueError):
        cooldown_seconds = 1.0
    raw_aliases = source.get("JARVIS_WAKE_WORD_ALIASES", "")
    aliases = tuple(
        dict.fromkeys(  # dedupe while preserving order
            normalized
            for part in raw_aliases.split(",")
            if (normalized := normalize_voice_phrase(part))
        )
    )
    return {
        "wake_word": wake_word,
        "enabled": enabled,
        "voice_enabled": voice_enabled,
        "cooldown_seconds": cooldown_seconds,
        "aliases": aliases,
    }


def _config_value(config: WakeWordConfig | Mapping[str, object] | None, key: str, default: object) -> object:
    if config is None:
        return default
    if isinstance(config, WakeWordConfig):
        return getattr(config, key)
    return config.get(key, default)


def wake_word_detected(
    text: str,
    *,
    wake_word: str | None = None,
    config: WakeWordConfig | Mapping[str, object] | None = None,
    now: float | None = None,
    last_detected_at: float | None = None,
) -> bool:
    result = analyze_wake_word(text, wake_word=wake_word, config=config, now=now, last_detected_at=last_detected_at)
    return bool(result["detected"])


def _phrase_present(tokens: list[str], phrase_tokens: list[str]) -> bool:
    """Return True if phrase_tokens appears as a contiguous run inside tokens."""

    if not phrase_tokens or len(tokens) < len(phrase_tokens):
        return False
    return any(
        tokens[index : index + len(phrase_tokens)] == phrase_tokens
        for index in range(len(tokens) - len(phrase_tokens) + 1)
    )


def analyze_wake_word(
    text: str,
    *,
    wake_word: str | None = None,
    config: WakeWordConfig | Mapping[str, object] | None = None,
    now: float | None = None,
    last_detected_at: float | None = None,
) -> dict[str, object]:
    configured_word = normalize_voice_phrase(wake_word or str(_config_value(config, "wake_word", "jarvis"))) or "jarvis"
    enabled = bool(_config_value(config, "enabled", True))
    cooldown_seconds = float(_config_value(config, "cooldown_seconds", 0.0))
    aliases = tuple(_config_value(config, "aliases", ()) or ())
    normalized_text = normalize_voice_phrase(text)
    cooldown_active = False
    if not enabled:
        return {
            "detected": False,
            "enabled": False,
            "wake_word": configured_word,
            "normalized": normalized_text,
            "reason": "wake word disabled",
            "cooldown_active": False,
        }
    if last_detected_at is not None and now is not None and now - last_detected_at < cooldown_seconds:
        cooldown_active = True
    tokens = normalized_text.split()
    detected = False
    matched_phrase = None
    if not cooldown_active:
        for phrase in (configured_word, *aliases):
            if _phrase_present(tokens, phrase.split()):
                detected = True
                matched_phrase = phrase
                break
    return {
        "detected": detected,
        "enabled": enabled,
        "wake_word": configured_word,
        "matched_phrase": matched_phrase,
        "normalized": normalized_text,
        "reason": "detected" if detected else ("cooldown active" if cooldown_active else "not detected"),
        "cooldown_active": cooldown_active,
    }


class WakeWordDetector:
    def __init__(
        self,
        wake_word: str = "jarvis",
        *,
        enabled: bool = True,
        cooldown_seconds: float = 1.0,
        aliases: tuple[str, ...] = (),
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.config = WakeWordConfig(
            wake_word=normalize_voice_phrase(wake_word) or "jarvis",
            enabled=enabled,
            cooldown_seconds=max(0.0, cooldown_seconds),
            aliases=tuple(dict.fromkeys(normalize_voice_phrase(alias) for alias in aliases if normalize_voice_phrase(alias))),
        )
        self.clock = clock or time.monotonic
        self.last_detected_at: float | None = None

    def detect(self, text: str) -> dict[str, object]:
        now = self.clock()
        result = analyze_wake_word(text, config=self.config, now=now, last_detected_at=self.last_detected_at)
        if result["detected"]:
            self.last_detected_at = now
        return result
