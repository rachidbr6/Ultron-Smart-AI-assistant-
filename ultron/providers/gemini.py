"""Gemini vision provider - describes images (e.g. screenshots) on request."""

from __future__ import annotations

import base64
import os
import time

import requests

from ultron.providers.base import ProviderResponse

DEFAULT_GEMINI_VISION_MODEL = "gemini-2.0-flash"
_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_DEFAULT_PROMPT = (
    "Describe what is visible in this screenshot in two or three concise spoken "
    "sentences, as if briefing someone who cannot see their own screen. Mention "
    "the active application/window and anything notable on it. Be direct, no "
    "preamble."
)


def gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def gemini_vision_model() -> str:
    return os.getenv("GEMINI_VISION_MODEL", DEFAULT_GEMINI_VISION_MODEL).strip() or DEFAULT_GEMINI_VISION_MODEL


class GeminiProvider:
    """Thin REST client for Gemini's vision-capable generateContent endpoint."""

    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: float = 12.0):
        self.api_key = api_key if api_key is not None else gemini_api_key()
        self.model = model or gemini_vision_model()
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def describe_image(self, image_bytes: bytes, question: str = "") -> ProviderResponse:
        """Send an image (PNG/JPEG bytes) to Gemini and return a spoken description."""

        if not self.enabled:
            return ProviderResponse(provider=self.name, status="error", error="missing_api_key")

        prompt = question.strip() if question and question.strip() else _DEFAULT_PROMPT
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(image_bytes).decode("ascii")}},
                    ]
                }
            ]
        }
        url = f"{_API_BASE}/{self.model}:generateContent"
        started = time.perf_counter()
        try:
            response = requests.post(
                url,
                params={"key": self.api_key},
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            return ProviderResponse(provider=self.name, status="error", error=f"request_failed: {exc}")

        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        if response.status_code != 200:
            return ProviderResponse(
                provider=self.name,
                status="error",
                error=f"http_{response.status_code}: {response.text[:200]}",
                latency_ms=latency_ms,
            )

        try:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, ValueError, TypeError):
            return ProviderResponse(provider=self.name, status="error", error="unparseable_response", latency_ms=latency_ms)

        if not text:
            return ProviderResponse(provider=self.name, status="error", error="empty_response", latency_ms=latency_ms)

        return ProviderResponse(provider=self.name, status="success", text=text, latency_ms=latency_ms)


__all__ = ["DEFAULT_GEMINI_VISION_MODEL", "GeminiProvider", "gemini_api_key", "gemini_vision_model"]
