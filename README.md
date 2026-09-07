# Ariadne

A Parser + GraphRAG engine for zero-day impact analysis: it ingests unstructured
cyber threat intelligence (CTI) and cross-references it against a knowledge graph
of your real infrastructure to answer, in minutes, whether a new vulnerability
reaches you, how far an attacker could get, and what the minimum safe fix is.

See [`CLAUDE.md`](./CLAUDE.md) for the full architecture, coding rules, and the
reasoning behind the Parser + GraphRAG approach.

## Structure

- `backend/` — the reasoning engine: CTI/SBOM/IaC parsers, the Neo4j-backed
  knowledge graph, the hybrid RAG reasoning engine, and the quantitative
  evaluation framework. Python 3.11+, FastAPI.
- `frontend/` — the Ariadne interface: a dark interactive graph canvas
  (React Flow) that visualizes the exposure path as a glowing thread, a
  context-sensitive impact sidebar, and a `Ctrl+K` command palette in place
  of a chat window. React + Vite + TypeScript.
- `docker-compose.yml` — local infrastructure: Neo4j, Qdrant, Ollama, and both
  services, all self-hosted so the whole thing is reproducible with one command.

## Quickstart

```bash
# 1. Infrastructure (Neo4j, Qdrant, Ollama)
docker compose up -d neo4j qdrant ollama

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in ANTHROPIC_API_KEY
python scripts/seed_topology.py   # populate the mock topology
uvicorn ariadne.api.main:app --reload

# 3. Frontend (separate shell)
cd frontend
npm install
cp .env.example .env
npm run dev
```

Then open the frontend dev server URL and press `Ctrl+K` to query the graph.

## Testing

```bash
cd backend && .venv/bin/pytest
cd frontend && npm run build   # type-checks + builds
```
