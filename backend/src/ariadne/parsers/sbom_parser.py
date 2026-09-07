"""Phase 1: reads a CycloneDX SBOM and produces Library nodes plus
DEPENDS_ON edges from the owning service."""

import json
from pathlib import Path

from ariadne.schemas import EdgeKind, NodeKind, TopologyEdge, TopologyNode


def parse_cyclonedx_sbom(path: Path, *, service_id: str) -> tuple[list[TopologyNode], list[TopologyEdge]]:
    bom = json.loads(path.read_text())

    nodes: list[TopologyNode] = []
    edges: list[TopologyEdge] = []
    for component in bom.get("components", []):
        library_id = f"{component['name']}@{component.get('version', 'unknown')}"
        nodes.append(TopologyNode(id=library_id, kind=NodeKind.LIBRARY, label=component["name"]))
        edges.append(
            TopologyEdge(
                id=f"{service_id}->{library_id}",
                source=service_id,
                target=library_id,
                kind=EdgeKind.DEPENDS_ON,
            )
        )
    return nodes, edges
