from functools import lru_cache

from ariadne.config import settings
from ariadne.graph.client import GraphClient
from ariadne.rag.llm_providers import AnthropicProvider, OllamaProvider
from ariadne.rag.reasoning import ReasoningEngine
from ariadne.rag.vector_store import VectorStore
from ariadne.schemas import CtiSummary


class LatestCtiStore:
    """Holds the most recently ingested CTI report in-process. A real
    deployment would persist this in Neo4j/Qdrant alongside the report
    itself; in-memory is enough for a single-instance demo."""

    def __init__(self) -> None:
        self._cti: CtiSummary | None = None

    def set(self, cti: CtiSummary) -> None:
        self._cti = cti

    def get(self) -> CtiSummary | None:
        return self._cti


@lru_cache
def get_cti_store() -> LatestCtiStore:
    return LatestCtiStore()


@lru_cache
def get_graph_client() -> GraphClient:
    return GraphClient()


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore(vector_size=settings.embedding_size)


@lru_cache
def get_embedder() -> OllamaProvider:
    return OllamaProvider()


@lru_cache
def get_reasoner() -> AnthropicProvider:
    return AnthropicProvider()


@lru_cache
def get_reasoning_engine() -> ReasoningEngine:
    return ReasoningEngine(
        graph=get_graph_client(),
        vectors=get_vector_store(),
        embedder=get_embedder(),
        reasoner=get_reasoner(),
    )
