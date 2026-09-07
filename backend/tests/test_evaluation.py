from dataclasses import dataclass
from pathlib import Path

from ariadne.evaluation.runner import GroundTruthScenario, evaluate, load_ground_truth

GROUND_TRUTH = Path(__file__).resolve().parent.parent / "data" / "ground_truth.json"


@dataclass
class FakePrediction:
    predicted_assets: list[str]
    predicted_exposed: list[str]


def test_load_ground_truth_parses_scenarios() -> None:
    scenarios = load_ground_truth(GROUND_TRUTH)
    assert scenarios[0].cve_id == "CVE-2021-44228"


def test_evaluate_against_a_perfect_prediction() -> None:
    """Wiring example: replace `predict` with a call into ReasoningEngine
    once Phase 1-3 are live end to end."""

    def predict(scenario: GroundTruthScenario) -> FakePrediction:
        return FakePrediction(
            predicted_assets=scenario.expected_assets,
            predicted_exposed=scenario.expected_exposed,
        )

    report = evaluate(load_ground_truth(GROUND_TRUTH), predict)

    assert report.mean_asset_recall == 1.0
    assert report.mean_hallucination_rate == 0.0
