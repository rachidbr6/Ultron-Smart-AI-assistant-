"""Local LLM provider (Ollama, LM Studio, or any OpenAI/Ollama-compatible endpoint)."""

from __future__ import annotations

import os
import time

import requests

from ultron.providers.base import ProviderRequest, ProviderResponse
from ultron.providers.groq import extract_action_json

DEFAULT_OLLAMA_MODEL = "llama3.2:1b"


def local_llm_url() -> str:
    return os.getenv("JARVIS_LOCAL_LLM_URL", "").strip().rstrip("/")


def local_llm_model() -> str:
    return os.getenv("JARVIS_LOCAL_LLM_MODEL", DEFAULT_OLLAMA_MODEL).strip() or DEFAULT_OLLAMA_MODEL


class OllamaProvider:
    """Routes commands through a local Ollama-compatible chat endpoint."""

    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None, system_prompt: str = "", timeout: float = 20.0):
        self.base_url = base_url if base_url is not None else local_llm_url()
        self.model = model or local_llm_model()
        self.system_prompt = system_prompt
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def analyze(self, request: ProviderRequest) -> ProviderResponse:
        if not self.enabled:
            return ProviderResponse(provider=self.name, status="unavailable", error="local_llm_not_configured")

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": request.command},
            ],
        }
        started = time.perf_counter()
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            return ProviderResponse(provider=self.name, status="error", error=f"request_failed: {exc}")
        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        if response.status_code != 200:
            return ProviderResponse(
                provider=self.name,
                status="error",
                error=f"http_{response.status_code}",
                latency_ms=latency_ms,
            )

        try:
            content = response.json()["message"]["content"]
            action = extract_action_json(content)
        except (KeyError, ValueError, TypeError):
            return ProviderResponse(provider=self.name, status="error", error="unparseable_response", latency_ms=latency_ms)

        return ProviderResponse(provider=self.name, status="success", action=action, latency_ms=latency_ms)


__all__ = ["DEFAULT_OLLAMA_MODEL", "OllamaProvider", "local_llm_model", "local_llm_url"]
