import json

from ariadne.graph.client import GraphClient, compute_exposure_level
from ariadne.rag.llm_providers import LLMNotConfiguredError, LLMProvider, LLMUnavailableError
from ariadne.rag.vector_store import VectorStore
from ariadne.schemas import (
    ComponentAnalysis,
    CtiSummary,
    ExposureLevel,
    Mitigation,
    QueryResult,
    TopologyNode,
)

GROUNDING_SYSTEM_PROMPT = (
    "You are a grounded security reasoning engine. Only state facts present in "
    "the provided subgraph and CTI context. Never invent asset names, IPs, or "
    "dependencies that are not listed."
)

MITIGATION_SYSTEM_PROMPT = (
    "You are a grounded security reasoning engine. You are given a specific asset, "
    "a CVE, and its exact exposure path through a real infrastructure graph. Do not "
    "invent assets, IPs, or dependencies beyond what is listed below. "
    'Respond with ONLY a JSON object of the shape {"summary": "<one sentence>", '
    '"patch": "<the exact command, env var, or config line>"}. No markdown, no code '
    "fences, no extra commentary -- just the JSON object."
)


class ReasoningEngine:
    """Phase 3: combines vector-retrieved CTI context with a deterministic
    graph traversal, then asks the LLM to synthesize — never to decide
    reachability itself. Graph traversal is ground truth; the LLM only
    narrates it.
    """

    def __init__(
        self, graph: GraphClient, vectors: VectorStore, embedder: LLMProvider, reasoner: LLMProvider
    ) -> None:
        self._graph = graph
        self._vectors = vectors
        self._embedder = embedder
        self._reasoner = reasoner

    def answer_query(self, query: str) -> QueryResult:
        nodes, _ = self._graph.get_topology()
        target = self._resolve_target_node(query, nodes)
        if target is None:
            return QueryResult(answer="Insufficient Topology Data: no known asset matched in the query.")

        node_ids, edge_ids = self._graph.find_exposure_path(target.id)
        if not node_ids:
            return QueryResult(
                answer=f"{target.label} is not reachable from any internet-facing entry point.",
                highlighted_node_ids=[target.id],
            )

        cti_context = self._vectors.search(self._embedder.embed(query), top_k=3)
        prompt = self._build_query_prompt(query, target, node_ids, cti_context)
        answer = self._reasoner.generate(prompt, system=GROUNDING_SYSTEM_PROMPT)
        return QueryResult(answer=answer, highlighted_node_ids=node_ids, highlighted_edge_ids=edge_ids)

    def analyze(self, component: str, cti: CtiSummary | None) -> ComponentAnalysis:
        """Phase 3 entry point for a named component (e.g. "log4j-core"):
        resolves it to a graph node, traces its exposure path deterministically,
        and -- only if a CTI report has actually been ingested -- asks the LLM
        for the grounded minimum viable mitigation."""
        nodes, _ = self._graph.get_topology()
        target = resolve_component_node(nodes, component)
        if target is None:
            return ComponentAnalysis(
                component=component,
                exposure_level=ExposureLevel.ISOLATED,
                mitigation=Mitigation(
                    node_id=component,
                    summary="Insufficient Topology Data: no known asset matches this component name.",
                    patch="",
                ),
            )

        node_ids, edge_ids = self._graph.find_exposure_path(target.id)
        exposure_level = compute_exposure_level(target, node_ids)
        broken_dependencies = self._graph.find_dependents(target.id)
        mitigation = (
            self.generate_mitigation(target, node_ids, cti)
            if cti is not None
            else Mitigation(
                node_id=target.id,
                summary="No CTI context ingested yet.",
                patch="# Ingest a threat report first: POST /api/cti/ingest",
            )
        )

        return ComponentAnalysis(
            component=target.id,
            node_ids=node_ids or [target.id],
            edge_ids=edge_ids,
            exposure_level=exposure_level,
            broken_dependencies=broken_dependencies,
            mitigation=mitigation,
        )

    def generate_mitigation(self, node: TopologyNode, node_ids: list[str], cti: CtiSummary) -> Mitigation:
        """The only place an LLM proposes a fix -- always anchored to the
        exact exposure path Neo4j returned, never to the LLM's own guess at
        the topology."""
        path_str = " -> ".join(node_ids) if node_ids else node.id
        prompt = (
            f"Asset: {node.label} ({node.id})\n"
            f"CVE: {cti.cve_id}\n"
            f"Affected versions: {cti.affected_versions}\n"
            f"Attack vector: {cti.attack_vector}\n"
            f"Exposure path (ground truth, from Neo4j -- do not alter or invent): {path_str}\n\n"
            "Propose the minimum viable mitigation to block this attack vector right "
            "now, without taking the service down (a JVM/env flag, config change, or "
            "WAF rule -- not a full upgrade or restart unless strictly necessary)."
        )
        try:
            raw = self._reasoner.generate(prompt, system=MITIGATION_SYSTEM_PROMPT)
            payload = json.loads(_strip_code_fence(raw))
            return Mitigation(node_id=node.id, summary=str(payload["summary"]), patch=str(payload["patch"]))
        except LLMNotConfiguredError:
            return Mitigation(
                node_id=node.id,
                summary="Mitigation engine not configured (no GEMINI_API_KEY set).",
                patch="",
            )
        except LLMUnavailableError:
            return Mitigation(
                node_id=node.id,
                summary="Mitigation engine temporarily unavailable (the LLM call failed). Try again shortly.",
                patch="",
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return Mitigation(
                node_id=node.id,
                summary="Mitigation generation failed: model did not return structured output.",
                patch="",
            )

    @staticmethod
    def _resolve_target_node(query: str, nodes: list[TopologyNode]) -> TopologyNode | None:
        lowered = query.lower()
        for node in nodes:
            if node.label.lower() in lowered or node.id.lower() in lowered:
                return node
        return None

    @staticmethod
    def _build_query_prompt(
        query: str, target: TopologyNode, node_ids: list[str], cti_context: list[dict[str, str]]
    ) -> str:
        path_str = " -> ".join(node_ids)
        cti_str = "\n".join(f"- {c}" for c in cti_context) or "(no matching CTI context retrieved)"
        return (
            f"Query: {query}\n\n"
            f"Exposure path to {target.label} ({target.id}):\n{path_str}\n\n"
            f"Retrieved CTI context:\n{cti_str}\n\n"
            "Answer the query using only the information above."
        )


def resolve_component_node(nodes: list[TopologyNode], component: str) -> TopologyNode | None:
    """Resolves a component name/id (e.g. "log4j-core" or "auth-api") to its
    graph node: exact id/label match first, substring fallback second."""
    lowered = component.lower()
    for node in nodes:
        if node.id.lower() == lowered or node.label.lower() == lowered:
            return node
    for node in nodes:
        if lowered in node.id.lower() or lowered in node.label.lower():
            return node
    return None


def _strip_code_fence(text: str) -> str:
    """LLMs wrap JSON in ```json fences despite instructions not to; strip
    them defensively rather than failing the parse on formatting alone."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        stripped = stripped.removeprefix("json").strip()
    return stripped
