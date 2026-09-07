# Ariadne — Backend

The Parser + GraphRAG reasoning engine described in the root [`CLAUDE.md`](../CLAUDE.md).

```
src/ariadne/
  parsers/     Phase 1 — CTI report, SBOM (CycloneDX), and IaC (docker-compose) parsers
  graph/       Phase 2 — Neo4j client and Cypher queries (the deterministic ground truth)
  rag/         Phase 3 — vector retrieval (Qdrant) + LLM providers + the hybrid reasoning engine
  evaluation/  Phase 4 — Asset Recall / Exposure Accuracy / Hallucination Rate metrics + runner
  api/         FastAPI app wiring the above into REST endpoints for the frontend
```

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

python scripts/seed_topology.py     # populate Neo4j with data/mock_topology/
uvicorn ariadne.api.main:app --reload

pytest -m "not integration"           # fast unit tests, no infra needed
pytest -m integration                 # Phase 4 eval: hits the real API + Neo4j, prints a summary table
ruff check src tests scripts          # lint
mypy src                              # type-check (strict)
```

Requires Neo4j and Qdrant reachable (see the root `docker-compose.yml`), and
`ANTHROPIC_API_KEY` set for the Phase 3 reasoning endpoints (`/api/query`,
`/api/graph/nodes/{id}/mitigation`).

## Phase 4 evaluation (`pytest -m integration`)

`tests/test_rag_pipeline.py` runs `tests/eval_data.json`'s ground-truth
scenarios end to end against the live FastAPI app (in-process `TestClient`)
and a real Neo4j -- run `python scripts/seed_topology.py` first so the
scenarios' expected assets actually exist in the graph. It prints a summary
table (asset recall / path accuracy / hallucination rate per scenario) via
a `pytest_terminal_summary` hook in `tests/conftest.py`.

The three graph-derived metrics are asserted unconditionally (`== 1.0` /
`== 0.0`) — they never depend on the LLM, since graph traversal is ground
truth. Only the mitigation-keyword check needs a live `ANTHROPIC_API_KEY`;
it's `pytest.skip`'d, not failed, when the key isn't set or a scenario has
no CTI to ground a mitigation in (e.g. a pure infrastructure
misconfiguration). In CI, with the key configured as a secret, that skip
condition never triggers and the keyword assertions become blocking too.

### Latest test results

Run 2026-09-07, local, against the mock topology seeded via
`scripts/seed_topology.py`, without `ANTHROPIC_API_KEY` set (hence the 3
skips — see above):

```
tests/test_evaluation.py::test_load_ground_truth_parses_scenarios PASSED
tests/test_evaluation.py::test_evaluate_against_a_perfect_prediction PASSED
tests/test_metrics.py::test_asset_recall_penalizes_missed_assets PASSED
tests/test_metrics.py::test_exposure_accuracy_counts_correct_classifications PASSED
tests/test_metrics.py::test_path_accuracy_requires_exact_order PASSED
tests/test_metrics.py::test_hallucination_rate_flags_invented_assets PASSED
tests/test_parsers.py::test_parse_cti_report_extracts_log4shell_fields PASSED
tests/test_parsers.py::test_parse_docker_compose_flags_published_ports_as_internet_facing PASSED
tests/test_parsers.py::test_parse_cyclonedx_sbom_links_components_to_owning_service PASSED
tests/test_rag_pipeline.py::test_rag_pipeline_topological_accuracy[CVE-2021-44228] SKIPPED
tests/test_rag_pipeline.py::test_rag_pipeline_topological_accuracy[CVE-2022-22965] SKIPPED
tests/test_rag_pipeline.py::test_rag_pipeline_topological_accuracy[MISCONFIG-AUTH-DB-EXPOSED] SKIPPED

================ Ariadne Phase 4 -- GraphRAG Evaluation Summary ================
Scenario                      Asset Recall   Path Accuracy   Hallucination
--------------------------------------------------------------------------
CVE-2021-44228                        100%            100%              0%
CVE-2022-22965                        100%            100%              0%
MISCONFIG-AUTH-DB-EXPOSED             100%            100%              0%
--------------------------------------------------------------------------
CI gate: this suite must exit non-zero if any percentage above is not 100/100/0.

9 passed, 3 skipped in 2.26s
```

`ruff check src tests scripts` and `mypy src` (strict) both pass clean.
