"""Generic LLM interface so the reasoning engine can swap providers per the
project's "LLM Independence" rule: Ollama for bulk/cheap extraction,
Anthropic Claude for the zero-hallucination-tolerance reasoning step.
"""

from typing import Protocol

import httpx
from anthropic import Anthropic

from ariadne.config import settings


class LLMProvider(Protocol):
    def generate(self, prompt: str, *, system: str | None = None) -> str: ...

    def embed(self, text: str) -> list[float]: ...


class AnthropicProvider:
    """Used for Phase 3 grounded reasoning — the only place where
    exploitability confidence and remediation text get generated.

    The API key is validated lazily, on first `generate()` call, not in
    `__init__`. This provider is constructed via FastAPI's `Depends` on
    every request to a route that might need it -- if the key were checked
    eagerly, a request that never actually reaches the LLM (e.g. "no CTI
    ingested yet") would still 500 for a key it never needed.
    """

    def __init__(self) -> None:
        self._client: Anthropic | None = None

    def _get_client(self) -> Anthropic:
        if self._client is None:
            if not settings.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY is not set")
            self._client = Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    def generate(self, prompt: str, *, system: str | None = None) -> str:
        response = self._get_client().messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Anthropic does not serve embeddings; use OllamaProvider.embed")


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
