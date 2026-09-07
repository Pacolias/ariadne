from ariadne.evaluation.metrics import asset_recall, exposure_accuracy, hallucination_rate


def test_asset_recall_penalizes_missed_assets() -> None:
    assert asset_recall({"auth-api"}, {"auth-api", "log4j-core"}) == 0.5
    assert asset_recall({"auth-api", "log4j-core"}, {"auth-api", "log4j-core"}) == 1.0


def test_exposure_accuracy_counts_correct_classifications() -> None:
    universe = {"auth-api", "billing-api", "auth-db"}
    predicted = {"auth-api"}
    expected = {"auth-api"}
    assert exposure_accuracy(predicted, expected, universe) == 1.0


def test_hallucination_rate_flags_invented_assets() -> None:
    known = {"auth-api", "log4j-core"}
    assert hallucination_rate({"auth-api", "made-up-service"}, known) == 0.5
    assert hallucination_rate({"auth-api"}, known) == 0.0
