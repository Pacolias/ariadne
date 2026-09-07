"""Phase 4: the exact metrics CLAUDE.md asserts on. Kept as pure functions
over sets/values so they're trivial to unit test independently of the
engine that produces the predictions.
"""


def asset_recall(predicted_assets: set[str], expected_assets: set[str]) -> float:
    """Fraction of truly-affected assets the engine actually surfaced.
    Must be 100% per the ground-truth contract — missing an asset is a
    critical failure, not a rounding error."""
    if not expected_assets:
        return 1.0
    return len(predicted_assets & expected_assets) / len(expected_assets)


def exposure_accuracy(predicted_exposed: set[str], expected_exposed: set[str], universe: set[str]) -> float:
    """Fraction of all assets in `universe` whose isolated/exposed
    classification the engine got right."""
    if not universe:
        return 1.0
    correct = sum(1 for asset in universe if (asset in predicted_exposed) == (asset in expected_exposed))
    return correct / len(universe)


def hallucination_rate(predicted_assets: set[str], known_assets: set[str]) -> float:
    """Fraction of predicted assets that don't exist in the real topology at
    all -- i.e. the engine invented them. Must be 0%."""
    if not predicted_assets:
        return 0.0
    invented = predicted_assets - known_assets
    return len(invented) / len(predicted_assets)
