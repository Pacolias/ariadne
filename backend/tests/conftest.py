"""Session-wide pytest hooks. `record_scenario_result` / `_scenario_results`
back the Phase 4 evaluation summary table printed by `pytest_terminal_summary`
-- see tests/test_rag_pipeline.py, which is the only thing that calls it.
"""

from typing import TypedDict

import pytest


class ScenarioResult(TypedDict):
    id: str
    asset_recall: float
    path_accuracy: float
    hallucination_rate: float


_scenario_results: list[ScenarioResult] = []


def record_scenario_result(
    *, id: str, asset_recall: float, path_accuracy: float, hallucination_rate: float
) -> None:
    _scenario_results.append(
        {
            "id": id,
            "asset_recall": asset_recall,
            "path_accuracy": path_accuracy,
            "hallucination_rate": hallucination_rate,
        }
    )


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, exitstatus: int, config: pytest.Config
) -> None:
    if not _scenario_results:
        return

    terminalreporter.section("Ariadne Phase 4 -- GraphRAG Evaluation Summary")
    header = f"{'Scenario':<28}{'Asset Recall':>14}{'Path Accuracy':>16}{'Hallucination':>16}"
    terminalreporter.write_line(header)
    terminalreporter.write_line("-" * len(header))
    for r in _scenario_results:
        terminalreporter.write_line(
            f"{r['id']:<28}"
            f"{r['asset_recall'] * 100:>13.0f}%"
            f"{r['path_accuracy'] * 100:>15.0f}%"
            f"{r['hallucination_rate'] * 100:>15.0f}%"
        )
    terminalreporter.write_line("-" * len(header))
    terminalreporter.write_line("CI gate: this suite must exit non-zero if any percentage above is not 100/100/0.")
