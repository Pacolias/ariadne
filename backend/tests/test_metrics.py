from ariadne.evaluation.metrics import (
    calculate_asset_recall,
    calculate_exposure_accuracy,
    calculate_hallucination_rate,
    calculate_path_accuracy,
)


def test_asset_recall_penalizes_missed_assets() -> None:
    assert calculate_asset_recall({"auth-api", "log4j-core"}, {"auth-api"}) == 0.5
    assert calculate_asset_recall({"auth-api", "log4j-core"}, {"auth-api", "log4j-core"}) == 1.0


def test_exposure_accuracy_counts_correct_classifications() -> None:
    universe = {"auth-api", "billing-api", "auth-db"}
    predicted = {"auth-api"}
    expected = {"auth-api"}
    assert calculate_exposure_accuracy(predicted, expected, universe) == 1.0


def test_path_accuracy_requires_exact_order() -> None:
    expected_path = ["nginx", "auth-api", "log4j-core@2.14.1"]
    assert calculate_path_accuracy(expected_path, expected_path) == 1.0
    assert calculate_path_accuracy(expected_path, ["nginx", "log4j-core@2.14.1", "auth-api"]) == 0.0
    assert calculate_path_accuracy(expected_path, ["nginx", "auth-api"]) == 0.0


def test_hallucination_rate_flags_invented_assets() -> None:
    known = {"auth-api", "log4j-core"}
    assert calculate_hallucination_rate({"auth-api", "made-up-service"}, known) == 0.5
    assert calculate_hallucination_rate({"auth-api"}, known) == 0.0
