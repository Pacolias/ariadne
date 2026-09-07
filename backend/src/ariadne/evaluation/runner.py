"""Phase 4: runs the engine against data/ground_truth.json and aggregates
the metrics from evaluation/metrics.py. The caller supplies `predict` so
this module stays decoupled from how the engine is wired (Neo4j/Qdrant
clients, which LLM provider, etc.) -- see tests/test_evaluation.py for the
wiring example.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ariadne.evaluation.metrics import asset_recall, exposure_accuracy, hallucination_rate


@dataclass
class GroundTruthScenario:
    cve_id: str
    expected_assets: list[str]
    expected_exposed: list[str]
    known_assets: list[str]


class EnginePrediction(Protocol):
    predicted_assets: list[str]
    predicted_exposed: list[str]


@dataclass
class EvaluationReport:
    scenario_count: int
    mean_asset_recall: float
    mean_exposure_accuracy: float
    mean_hallucination_rate: float


def load_ground_truth(path: Path) -> list[GroundTruthScenario]:
    raw = json.loads(path.read_text())
    return [GroundTruthScenario(**scenario) for scenario in raw]


def evaluate(
    scenarios: list[GroundTruthScenario],
    predict: Callable[[GroundTruthScenario], EnginePrediction],
) -> EvaluationReport:
    recalls: list[float] = []
    accuracies: list[float] = []
    hallucinations: list[float] = []

    for scenario in scenarios:
        prediction = predict(scenario)
        predicted_assets = set(prediction.predicted_assets)
        expected_assets = set(scenario.expected_assets)
        known_assets = set(scenario.known_assets)

        recalls.append(asset_recall(predicted_assets, expected_assets))
        accuracies.append(
            exposure_accuracy(set(prediction.predicted_exposed), set(scenario.expected_exposed), known_assets)
        )
        hallucinations.append(hallucination_rate(predicted_assets, known_assets))

    n = len(scenarios)
    return EvaluationReport(
        scenario_count=n,
        mean_asset_recall=sum(recalls) / n,
        mean_exposure_accuracy=sum(accuracies) / n,
        mean_hallucination_rate=sum(hallucinations) / n,
    )
