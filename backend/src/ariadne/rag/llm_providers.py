"""Generic LLM interface so the reasoning engine can swap providers per the
project's "LLM Independence" rule: Ollama for bulk/cheap extraction,
Gemini for the zero-hallucination-tolerance reasoning step.
"""

from typing import Protocol

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from ariadne.config import settings


class LLMProvider(Protocol):
    def generate(self, prompt: str, *, system: str | None = None) -> str: ...

    def embed(self, text: str) -> list[float]: ...


class LLMNotConfiguredError(RuntimeError):
    """Raised when a provider is asked to generate/embed without its
    required configuration (e.g. no API key). Distinct from RuntimeError so
    callers can catch this specific, expected condition without also
    swallowing unrelated bugs."""


class LLMUnavailableError(RuntimeError):
    """Raised when a *configured* provider's call itself fails -- rate
    limit, transient outage, empty/malformed response. Distinct from
    LLMNotConfiguredError: "had a key, the call just failed right now" is a
    different, retryable condition, not a setup problem."""


class GeminiProvider:
    """Used for Phase 3 grounded reasoning — the only place where
    exploitability confidence and remediation text get generated.

    The API key is validated lazily, on first `generate()` call, not in
    `__init__`. This provider is constructed via FastAPI's `Depends` on
    every request to a route that might need it -- if the key were checked
    eagerly, a request that never actually reaches the LLM (e.g. "no CTI
    ingested yet") would still 500 for a key it never needed.
    """

    def __init__(self) -> None:
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not settings.gemini_api_key:
                raise LLMNotConfiguredError("GEMINI_API_KEY is not set")
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        config = types.GenerateContentConfig(system_instruction=system) if system else None
        try:
            response = self._get_client().models.generate_content(
                model=settings.gemini_model, contents=prompt, config=config
            )
        except genai_errors.APIError as exc:
            raise LLMUnavailableError(str(exc)) from exc
        if not response.text:
            raise LLMUnavailableError("Gemini returned an empty response")
        return response.text

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("GeminiProvider does not serve embeddings here; use OllamaProvider.embed")


class OllamaProvider:
    """Used for Phase 1 bulk extraction and for embeddings — local, free,
    good enough for structured extraction from CTI text and SBOM/IaC hints.
    """

    def __init__(self) -> None:
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_model

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        payload = {"model": self._model, "prompt": prompt, "system": system or "", "stream": False}
        response = httpx.post(f"{self._base_url}/api/generate", json=payload, timeout=60.0)
        response.raise_for_status()
        text: str = response.json()["response"]
        return text

    def embed(self, text: str) -> list[float]:
        payload = {"model": settings.ollama_embedding_model, "prompt": text}
        response = httpx.post(f"{self._base_url}/api/embeddings", json=payload, timeout=60.0)
        response.raise_for_status()
        embedding: list[float] = response.json()["embedding"]
        return embedding
