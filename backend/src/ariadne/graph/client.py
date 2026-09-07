from neo4j import GraphDatabase

from ariadne.config import settings
from ariadne.schemas import (
    CtiSummary,
    EdgeKind,
    ExposureLevel,
    NodeKind,
    TopologyEdge,
    TopologyNode,
)

from . import queries


def _edge_id(source: str, target: str) -> str:
    return f"{source}->{target}"


def compute_exposure_level(target: TopologyNode, exposure_path_node_ids: list[str]) -> ExposureLevel:
    """Classification is derived purely from the graph traversal result --
    shared by every endpoint/engine method that needs it, so "exposed" never
    means two different things in different parts of the API."""
    if target.internet_facing:
        return ExposureLevel.PUBLIC_FACING
    if exposure_path_node_ids:
        return ExposureLevel.INTERNAL
    return ExposureLevel.ISOLATED


class GraphClient:
    """Thin wrapper around the Neo4j driver. Deterministic reads/writes only —
    per the project's coding rules, no traversal decision is ever delegated
    to an LLM; this class is the ground truth for "what is actually connected
    to what".
    """

    def __init__(self) -> None:
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def close(self) -> None:
        self._driver.close()

    def upsert_node(self, node: TopologyNode) -> None:
        with self._driver.session() as session:
            session.run(
                queries.UPSERT_NODE,
                id=node.id,
                kind=node.kind.value,
                label=node.label,
                compromised=node.compromised,
                internet_facing=node.internet_facing,
            )

    def upsert_edge(self, edge: TopologyEdge) -> None:
        query = queries.UPSERT_EDGE % edge.kind.value
        with self._driver.session() as session:
            session.run(query, source=edge.source, target=edge.target)

    def get_topology(self) -> tuple[list[TopologyNode], list[TopologyEdge]]:
        nodes: dict[str, TopologyNode] = {}
        edges: list[TopologyEdge] = []
        with self._driver.session() as session:
            result = session.run(queries.FETCH_TOPOLOGY)
            for record in result:
                n = record["n"]
                nodes.setdefault(
                    n["id"],
                    TopologyNode(
                        id=n["id"],
                        kind=NodeKind(n["kind"]),
                        label=n["label"],
                        compromised=n.get("compromised", False),
                        internet_facing=n.get("internet_facing", False),
                    ),
                )
                rel, m = record["r"], record["m"]
                if rel is not None and m is not None:
                    edges.append(
                        TopologyEdge(
                            id=_edge_id(n["id"], m["id"]),
                            source=n["id"],
                            target=m["id"],
                            kind=EdgeKind(rel.type),
                        )
                    )
        return list(nodes.values()), edges

    def find_exposure_path(self, target_id: str) -> tuple[list[str], list[str]]:
        """Returns (node_ids, edge_ids) along the shortest path from any
        internet-facing entry point to `target_id`, or empty lists if the
        target is unreachable — the API layer turns that into the
        "Insufficient Topology Data" response, never a guess.
        """
        with self._driver.session() as session:
            record = session.run(queries.FIND_EXPOSURE_PATH, target_id=target_id).single()
            if record is None:
                return [], []
            path = record["path"]
            node_ids = [node["id"] for node in path.nodes]
            edge_ids = [_edge_id(rel.start_node["id"], rel.end_node["id"]) for rel in path.relationships]
            return node_ids, edge_ids

    def find_dependents(self, target_id: str) -> list[str]:
        with self._driver.session() as session:
            return [record["id"] for record in session.run(queries.FIND_DEPENDENTS, target_id=target_id)]

    def save_latest_cti(self, cti: CtiSummary) -> None:
        with self._driver.session() as session:
            session.run(
                queries.UPSERT_LATEST_CTI,
                cve_id=cti.cve_id,
                target_software=cti.target_software,
                affected_versions=cti.affected_versions,
                attack_vector=cti.attack_vector,
                source_report=cti.source_report,
            )

    def get_latest_cti(self) -> CtiSummary | None:
        with self._driver.session() as session:
            record = session.run(queries.FETCH_LATEST_CTI).single()
            if record is None:
                return None
            c = record["c"]
            return CtiSummary(
                cve_id=c["cve_id"],
                target_software=c["target_software"],
                affected_versions=c["affected_versions"],
                attack_vector=c["attack_vector"],
                source_report=c["source_report"],
            )
