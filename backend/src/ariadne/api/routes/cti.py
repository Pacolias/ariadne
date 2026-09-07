from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ariadne.api.deps import get_graph_client
from ariadne.graph.client import GraphClient
from ariadne.parsers.cti_parser import parse_cti_report
from ariadne.schemas import CtiSummary

router = APIRouter(prefix="/api/cti", tags=["cti"])


class IngestRequest(BaseModel):
    text: str
    source_report: str


@router.post("/ingest")
def ingest_cti(body: IngestRequest, graph: GraphClient = Depends(get_graph_client)) -> CtiSummary:
    cti = parse_cti_report(body.text, source_report=body.source_report)
    graph.save_latest_cti(cti)

    # Best-effort: flag any node whose label matches the reported target
    # software as compromised, so the canvas can render Ariadne's Thread
    # without a human manually tagging the affected asset.
    nodes, _ = graph.get_topology()
    for node in nodes:
        if node.label.lower() in cti.target_software.lower():
            node.compromised = True
            graph.upsert_node(node)

    return cti
