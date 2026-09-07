from fastapi import APIRouter, Depends

from ariadne.api.deps import get_graph_client, get_reasoning_engine
from ariadne.graph.client import GraphClient, compute_exposure_level
from ariadne.rag.reasoning import ReasoningEngine
from ariadne.schemas import ExposureLevel, ExposurePath, ImpactMetrics, Mitigation, TopologyResponse

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/topology")
def get_topology(graph: GraphClient = Depends(get_graph_client)) -> TopologyResponse:
    nodes, edges = graph.get_topology()
    return TopologyResponse(nodes=nodes, edges=edges, cti=graph.get_latest_cti())


@router.get("/nodes/{node_id}/exposure-path")
def get_exposure_path(node_id: str, graph: GraphClient = Depends(get_graph_client)) -> ExposurePath:
    """Deterministic traversal only -- no LLM, no API key required. This is
    what lights up Ariadne's Thread when a node is selected on the canvas."""
    node_ids, edge_ids = graph.find_exposure_path(node_id)
    return ExposurePath(node_ids=node_ids, edge_ids=edge_ids)


@router.get("/nodes/{node_id}/impact")
def get_impact(node_id: str, graph: GraphClient = Depends(get_graph_client)) -> ImpactMetrics:
    node_ids, _ = graph.find_exposure_path(node_id)
    dependents = graph.find_dependents(node_id)

    nodes, _ = graph.get_topology()
    target = next((n for n in nodes if n.id == node_id), None)
    exposure_level = compute_exposure_level(target, node_ids) if target else ExposureLevel.ISOLATED

    return ImpactMetrics(
        node_id=node_id,
        asset_recall=1.0 if node_ids else 0.0,
        exposure_level=exposure_level,
        broken_dependencies=dependents,
    )


@router.get("/nodes/{node_id}/mitigation")
def get_mitigation(
    node_id: str,
    graph: GraphClient = Depends(get_graph_client),
    engine: ReasoningEngine = Depends(get_reasoning_engine),
) -> Mitigation:
    """Thin wrapper around ReasoningEngine.generate_mitigation, kept as its
    own endpoint for the frontend's per-node parallel fetch (impact +
    exposure-path + mitigation). See POST /api/analyze for the consolidated
    single-call version."""
    cti = graph.get_latest_cti()
    if cti is None:
        return Mitigation(
            node_id=node_id,
            summary="No CTI context ingested yet.",
            patch="# Ingest a threat report first: POST /api/cti/ingest",
        )

    nodes, _ = graph.get_topology()
    target = next((n for n in nodes if n.id == node_id), None)
    if target is None:
        return Mitigation(node_id=node_id, summary="Unknown asset.", patch="")

    node_ids, _ = graph.find_exposure_path(node_id)
    return engine.generate_mitigation(target, node_ids, cti)
