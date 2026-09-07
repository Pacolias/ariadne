"""Populates Neo4j with the mock protected environment described in
data/mock_topology/, so the frontend has something to render before a real
CTI report has been ingested.

Usage (from backend/, with Neo4j reachable -- e.g. `docker compose up neo4j -d`
at the repo root, and `pip install -e .` done here first):

    python scripts/seed_topology.py
"""

from pathlib import Path

from ariadne.graph.client import GraphClient
from ariadne.parsers.iac_parser import parse_docker_compose
from ariadne.parsers.sbom_parser import parse_cyclonedx_sbom

MOCK_TOPOLOGY_DIR = Path(__file__).resolve().parent.parent / "data" / "mock_topology"


def main() -> None:
    nodes, edges = parse_docker_compose(MOCK_TOPOLOGY_DIR / "docker-compose.yml")

    sbom_nodes, sbom_edges = parse_cyclonedx_sbom(
        MOCK_TOPOLOGY_DIR / "auth-api-sbom.json", service_id="auth-api"
    )
    nodes += sbom_nodes
    edges += sbom_edges

    graph = GraphClient()
    try:
        for node in nodes:
            graph.upsert_node(node)
        for edge in edges:
            graph.upsert_edge(edge)
    finally:
        graph.close()

    print(f"Seeded {len(nodes)} nodes and {len(edges)} edges.")


if __name__ == "__main__":
    main()
