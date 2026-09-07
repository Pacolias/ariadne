from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ariadne.api.deps import get_graph_client, get_reasoning_engine
from ariadne.graph.client import GraphClient
from ariadne.rag.reasoning import ReasoningEngine
from ariadne.schemas import ComponentAnalysis

router = APIRouter(prefix="/api", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    component: str


@router.post("/analyze")
def analyze(
    body: AnalyzeRequest,
    engine: ReasoningEngine = Depends(get_reasoning_engine),
    graph: GraphClient = Depends(get_graph_client),
) -> ComponentAnalysis:
    """Consolidated Phase 3 entry point: given a component name (e.g.
    "log4j-core"), returns its exact exposure path (deterministic, from
    Neo4j) plus the grounded mitigation card -- everything the frontend
    sidebar needs from one call."""
    return engine.analyze(body.component, graph.get_latest_cti())
