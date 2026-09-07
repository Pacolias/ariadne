from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ariadne.config import settings

COLLECTION = "cti_reports"


class VectorStore:
    """Semantic search over ingested CTI reports. This retrieves candidate
    threat context only — it never decides what is reachable in the
    customer's environment, that's GraphClient's job (see Phase 3: hybrid
    reasoning combines both, it never lets either substitute for the other).
    """

    def __init__(self, vector_size: int) -> None:
        self._client = QdrantClient(url=settings.qdrant_url)
        self._vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if not self._client.collection_exists(COLLECTION):
            self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
            )

    def upsert_report(self, report_id: str, embedding: list[float], payload: dict[str, str]) -> None:
        self._client.upsert(
            collection_name=COLLECTION,
            points=[PointStruct(id=report_id, vector=embedding, payload=payload)],
        )

    def search(self, embedding: list[float], top_k: int = 5) -> list[dict[str, str]]:
        results = self._client.query_points(
            collection_name=COLLECTION, query=embedding, limit=top_k
        ).points
        return [dict(point.payload or {}) for point in results]
