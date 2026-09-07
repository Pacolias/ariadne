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

pytest                                # tests
ruff check src tests scripts          # lint
mypy src                              # type-check (strict)
```

Requires Neo4j and Qdrant reachable (see the root `docker-compose.yml`), and
`ANTHROPIC_API_KEY` set for the Phase 3 reasoning endpoints (`/api/query`,
`/api/graph/nodes/{id}/mitigation`).
