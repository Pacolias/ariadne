"""Phase 4: the exact metrics CLAUDE.md asserts on. Kept as pure functions
over sets/lists so they're trivial to unit test independently of the
engine that produces the predictions.
"""


def calculate_asset_recall(expected: set[str], retrieved: set[str]) -> float:
    """Fraction of truly-affected assets the engine actually surfaced.
    Must be 100% per the ground-truth contract — missing an asset is a
    critical failure, not a rounding error."""
    if not expected:
        return 1.0
    return len(retrieved & expected) / len(expected)


def calculate_exposure_accuracy(predicted_exposed: set[str], expected_exposed: set[str], universe: set[str]) -> float:
    """Fraction of all assets in `universe` whose isolated/exposed
    classification the engine got right."""
    if not universe:
        return 1.0
    correct = sum(1 for asset in universe if (asset in predicted_exposed) == (asset in expected_exposed))
    return correct / len(universe)


def calculate_path_accuracy(expected_path: list[str], retrieved_path: list[str]) -> float:
    """Strict, node-for-node, in-order comparison of the exposure path Neo4j
    returned against the ground-truth path. No partial credit: a reordered
    or partial path does not describe the same attack path, so it is wrong,
    not "mostly right"."""
    return 1.0 if retrieved_path == expected_path else 0.0


def calculate_hallucination_rate(retrieved_assets: set[str], valid_graph_nodes: set[str]) -> float:
    """Fraction of retrieved assets that don't exist in the real topology at
    all -- i.e. the engine invented them. Must be 0%."""
    if not retrieved_assets:
        return 0.0
    invented = retrieved_assets - valid_graph_nodes
    return len(invented) / len(retrieved_assets)
