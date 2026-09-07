from enum import Enum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for models serialized to the frontend: Python stays snake_case,
    wire format is camelCase to match frontend/src/types/graph.ts."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class NodeKind(str, Enum):
    SERVICE = "service"
    LIBRARY = "library"
    ENDPOINT = "endpoint"
    DATABASE = "database"


class EdgeKind(str, Enum):
    DEPENDS_ON = "DEPENDS_ON"
    EXPOSES = "EXPOSES"
    COMMUNICATES_WITH = "COMMUNICATES_WITH"


class TopologyNode(BaseModel):
    id: str
    kind: NodeKind
    label: str
    compromised: bool = False
    internet_facing: bool = False
    metadata: dict[str, str] = {}


class TopologyEdge(CamelModel):
    id: str
    source: str
    target: str
    kind: EdgeKind


class CtiSummary(CamelModel):
    """Structured output of the Phase 1 CTI parser."""

    cve_id: str
    target_software: str
    affected_versions: str
    attack_vector: str
    source_report: str


class ExposureLevel(str, Enum):
    ISOLATED = "isolated"
    INTERNAL = "internal"
    PUBLIC_FACING = "public-facing"


class ImpactMetrics(CamelModel):
    node_id: str
    asset_recall: float
    exposure_level: ExposureLevel
    broken_dependencies: list[str] = []


class ExposurePath(CamelModel):
    """Deterministic graph traversal result -- no LLM involved. Used to light
    up Ariadne's Thread on node selection, independent of the (LLM-backed,
    API-key-gated) natural language query flow."""

    node_ids: list[str] = []
    edge_ids: list[str] = []


class Mitigation(CamelModel):
    node_id: str
    summary: str
    patch: str


class TopologyResponse(CamelModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    cti: CtiSummary | None = None


class ComponentAnalysis(CamelModel):
    """Phase 3 consolidated output: resolves a named component (e.g.
    "log4j-core") to its exact exposure path in Neo4j plus the grounded,
    LLM-generated minimum viable mitigation -- everything the frontend needs
    to render the subgraph highlight and the mitigation card from one call.
    """

    component: str
    node_ids: list[str] = []
    edge_ids: list[str] = []
    exposure_level: ExposureLevel
    broken_dependencies: list[str] = []
    mitigation: Mitigation


class QueryRequest(BaseModel):
    query: str


class QueryResult(CamelModel):
    """Phase 3 output: grounded natural-language answer plus the exact
    subgraph it was grounded in, so the frontend can render Ariadne's
    Thread instead of (or alongside) the text."""

    answer: str
    highlighted_node_ids: list[str] = []
    highlighted_edge_ids: list[str] = []
