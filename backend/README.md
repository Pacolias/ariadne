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
