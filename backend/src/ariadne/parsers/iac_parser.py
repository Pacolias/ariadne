"""Phase 1: reads a docker-compose.yml and produces Service nodes,
their published-port Endpoints, and the COMMUNICATES_WITH edges implied
by depends_on. A service with a published port is flagged internet_facing
-- that flag is what graph.queries.FIND_EXPOSURE_PATH treats as an entry
point when tracing an attack path.
"""

from pathlib import Path

import yaml

from ariadne.schemas import EdgeKind, NodeKind, TopologyEdge, TopologyNode


def parse_docker_compose(path: Path) -> tuple[list[TopologyNode], list[TopologyEdge]]:
    compose = yaml.safe_load(path.read_text())

    nodes: list[TopologyNode] = []
    edges: list[TopologyEdge] = []

    for service_name, spec in (compose.get("services") or {}).items():
        published_ports = _published_ports(spec.get("ports") or [])
        nodes.append(
            TopologyNode(
                id=service_name,
                kind=NodeKind.SERVICE,
                label=service_name,
                internet_facing=bool(published_ports),
            )
        )

        for host_port in published_ports:
            endpoint_id = f"{service_name}:{host_port}"
            nodes.append(TopologyNode(id=endpoint_id, kind=NodeKind.ENDPOINT, label=f"port {host_port}"))
            edges.append(
                TopologyEdge(
                    id=f"{service_name}->{endpoint_id}",
                    source=service_name,
                    target=endpoint_id,
                    kind=EdgeKind.EXPOSES,
                )
            )

        for dependency in spec.get("depends_on") or []:
            edges.append(
                TopologyEdge(
                    id=f"{service_name}->{dependency}",
                    source=service_name,
                    target=dependency,
                    kind=EdgeKind.COMMUNICATES_WITH,
                )
            )

    return nodes, edges


def _published_ports(ports: list[str | int | dict[str, object]]) -> list[str]:
    """Docker Compose lets ports be "8080:80", 8080, or a long-form mapping.
    We only care about the host-side port (what's reachable from outside)."""
    published: list[str] = []
    for entry in ports:
        if isinstance(entry, dict):
            published.append(str(entry.get("published", entry.get("target"))))
        else:
            published.append(str(entry).split(":")[0])
    return published
