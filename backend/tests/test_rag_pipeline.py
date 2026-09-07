"""Phase 4 end-to-end evaluation: drives the real FastAPI app (in-process,
via TestClient) against a live Neo4j to verify the GraphRAG pipeline's
topological accuracy against a curated ground truth (tests/eval_data.json).

Requires: Neo4j reachable (root docker-compose.yml) with the mock topology
seeded (`python scripts/seed_topology.py`). The three graph-derived metrics
below never depend on the LLM -- graph traversal is ground truth, per the
project's coding rules -- so they run and assert unconditionally. Only the
mitigation-keyword check needs a live LLM call, and is skipped (not failed)
when no GEMINI_API_KEY is configured or the scenario has no CTI to ground
a mitigation in (e.g. a pure infrastructure misconfiguration).
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from conftest import record_scenario_result
from fastapi.testclient import TestClient

from ariadne.api.main import app
from ariadne.evaluation.metrics import (
    calculate_asset_recall,
    calculate_hallucination_rate,
    calculate_path_accuracy,
)

EVAL_DATA = Path(__file__).resolve().parent / "eval_data.json"


@dataclass
class EvalScenario:
    id: str
    cti_alert: str | None
    expected_assets: list[str]
    expected_exposure_path: list[str]
    expected_mitigation_keywords: list[str]


def load_eval_scenarios() -> list[EvalScenario]:
    raw = json.loads(EVAL_DATA.read_text())
    return [EvalScenario(**scenario) for scenario in raw]


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def valid_graph_nodes(client: TestClient) -> set[str]:
    """The real inventory: anything the engine reports that isn't in here is
    an invented asset, full stop."""
    response = client.get("/api/graph/topology")
    assert response.status_code == 200, response.text
    return {node["id"] for node in response.json()["nodes"]}


@pytest.mark.integration
@pytest.mark.parametrize("scenario", load_eval_scenarios(), ids=lambda s: s.id)
def test_rag_pipeline_topological_accuracy(
    scenario: EvalScenario, client: TestClient, valid_graph_nodes: set[str]
) -> None:
    if scenario.cti_alert:
        ingest = client.post(
            "/api/cti/ingest", json={"text": scenario.cti_alert, "source_report": scenario.id}
        )
        assert ingest.status_code == 200, ingest.text

    target_component = scenario.expected_exposure_path[-1]
    response = client.post("/api/analyze", json={"component": target_component})
    assert response.status_code == 200, response.text
    result = response.json()

    retrieved_path: list[str] = result["nodeIds"]
    retrieved_assets = set(retrieved_path)
    expected_assets = set(scenario.expected_assets)

    recall = calculate_asset_recall(expected_assets, retrieved_assets)
    path_accuracy = calculate_path_accuracy(scenario.expected_exposure_path, retrieved_path)
    hallucination = calculate_hallucination_rate(retrieved_assets, valid_graph_nodes)

    record_scenario_result(
        id=scenario.id, asset_recall=recall, path_accuracy=path_accuracy, hallucination_rate=hallucination
    )

    assert recall == 1.0, f"{scenario.id}: missed expected assets {expected_assets - retrieved_assets}"
    assert path_accuracy == 1.0, (
        f"{scenario.id}: path mismatch -- expected {scenario.expected_exposure_path}, got {retrieved_path}"
    )
    assert hallucination == 0.0, f"{scenario.id}: engine reported assets not present in the real graph"

    if not scenario.cti_alert:
        pytest.skip(f"{scenario.id}: infrastructure misconfiguration, no CTI-grounded mitigation to check")

    mitigation = result["mitigation"]
    if "not configured" in mitigation["summary"].lower():
        pytest.skip(f"{scenario.id}: GEMINI_API_KEY not set, skipping mitigation keyword check")

    mitigation_text = f"{mitigation['summary']} {mitigation['patch']}".lower()
    for keyword in scenario.expected_mitigation_keywords:
        assert keyword.lower() in mitigation_text, f"{scenario.id}: mitigation missing keyword '{keyword}'"
