from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ariadne.api.deps import LatestCtiStore, get_cti_store, get_reasoning_engine
from ariadne.rag.reasoning import ReasoningEngine
from ariadne.schemas import ComponentAnalysis

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    component: str


@router.post("/analyze")
def analyze(
    body: AnalyzeRequest,
    engine: ReasoningEngine = Depends(get_reasoning_engine),
    cti_store: LatestCtiStore = Depends(get_cti_store),
) -> ComponentAnalysis:
    """Consolidated Phase 3 entry point: given a component name (e.g.
    "log4j-core"), returns its exact exposure path (deterministic, from
    Neo4j) plus the grounded mitigation card -- everything the frontend
    sidebar needs from one call."""
    return engine.analyze(body.component, cti_store.get())
