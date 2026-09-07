# Contributing to Ariadne

This is a portfolio project demonstrating a deterministic, rigorously evaluated
Parser + GraphRAG pipeline (see [`CLAUDE.md`](./CLAUDE.md) for the full
architecture and vision). The bar here isn't just "it compiles" — it's "I
traced this against the real graph and it's still true." The conventions
below exist to keep that bar consistent as the project grows.

## Before you touch code

**Read `CLAUDE.md` first.** It documents decisions that aren't obvious from
the code alone: why Neo4j over NetworkX, why the graph traversal must stay
deterministic and the LLM only narrates it, why CTI ingestion is CVE-centric,
why the frontend is themed around Ariadne's thread instead of a generic
dashboard. If a change seems to contradict something there, that's a signal
to reconcile it explicitly (see below), not to route around it silently.

**Reuse before you rebuild.** This project has accumulated real, working
modules: `backend/src/ariadne/{parsers,graph,rag,evaluation,api}/`,
`scripts/seed_topology.py`, the frontend's `store/useAriadneStore.ts` as the
single source of truth for canvas/sidebar state. Before adding a new file or
endpoint, check whether an existing one already does most of the job. A
prompt or spec that describes something in different words than the current
code (different file names, a different endpoint path, a different graph
backend) is not automatically a request to rebuild it from scratch — it's
often the same requirement seen from a different angle. When a request
genuinely conflicts with an established architectural decision (e.g. "use
NetworkX in memory" vs. the project's Neo4j+Docker Compose setup), say so
explicitly and reconcile before writing code, rather than quietly
maintaining two parallel implementations.

## Core invariants (don't break these)

- **Graph traversal is ground truth; the LLM only narrates it.** Exposure
  paths, asset lists, and hallucination checks must always be computable
  from Neo4j alone, with zero LLM involvement. Anything the LLM generates
  (a mitigation, a natural-language answer) must be grounded in a subgraph
  the graph client already produced — never used to guess connectivity.
- **An LLM failure must never take down a deterministic response.** If the
  reasoning provider is unconfigured, rate-limited, or returns garbage, the
  affected field degrades to an explicit, honest message (see
  `LLMNotConfiguredError` / `LLMUnavailableError` in
  `rag/llm_providers.py`) — the exposure path and blast radius in the same
  response must still come back correct. This has broken twice already
  (missing key, then a transient 503) and both were real bugs, not
  hypotheticals.
- **LLM Independence.** New reasoning/embedding logic goes through the
  `LLMProvider` protocol, not a provider SDK called directly from
  `reasoning.py` or route handlers.
- **No fabricated ground truth.** Don't invent a CVE for something that
  isn't one (see the `MISCONFIG-AUTH-DB-EXPOSED` eval scenario for how to
  model a real misconfiguration without a fake CVE ID instead).

## Verifying a change

"It compiles" and "the tests I imagined would pass" are not verification.
Before considering a change done:

- **Backend:** `make test` (fast, no infra) and, when you touched graph
  queries, the reasoning engine, or an endpoint, `make test-integration`
  against the actually-running Neo4j (`docker compose up -d neo4j qdrant`,
  then `python scripts/seed_topology.py`). Then `make lint` and `make
  typecheck` (mypy runs `--strict`; keep it that way). If you're touching
  `/api/analyze`, `/api/query`, or ingestion, hit the live endpoint with
  `curl` or a throwaway local `uvicorn` process — this project has caught
  real bugs (a Cypher query with no deterministic tie-break, an LLM call
  that 500'd the whole response, an outdated model name) only by actually
  calling the running service, never by reading the code.
- **Frontend:** `npm run build` (type-checks via `tsc -b` then bundles) and
  `npm run lint`.
- **Both:** if the fix came from something you observed live (a stale
  Docker image, an env var mismatch, a Cypher edge case), reproduce it
  first, then verify the fix against the same live setup — don't declare
  it fixed from reading the diff alone.

## Commit messages

Look at `git log` before writing one — the existing history is the style
guide. Concretely:

- **Subject line:** imperative mood ("Add", "Fix", "Persist", "Consolidate"
  — not "Added"/"Fixes"), capitalized, no trailing period, ~50-70 chars,
  describing the change at the level someone skimming `git log --oneline`
  needs.
- **Body: prose paragraphs, not bullet lists.** Each paragraph covers one
  logical piece of the change. Explain *why*, not just what — a diff
  already shows what changed.
- **Call out bugs found while building or testing, explicitly**, e.g. "Fixed
  a real bug found while running this against live data: ...". Don't bury
  a real fix inside a generic "misc changes" line.
- **State what you verified**, e.g. "Verified live: ingested a report,
  killed the process, started a fresh one that never saw the ingest, and it
  still returned the CTI correctly." A claim with no verification behind it
  doesn't belong in the message.
- **Note explicitly what was *not* affected** when it's non-obvious, e.g.
  "Ollama continues to handle embeddings — unaffected by this change."
- **No attribution / co-author trailers** in this repo (project-level
  choice — `.claude/settings.json` disables them locally; don't add them
  by hand either).
- One commit per coherent change; don't bundle an unrelated drive-by fix
  into a feature commit without calling it out in the body.

## Frontend conventions

- New UI: Tailwind utility classes, dark palette only
  (`gray-800`/`900`/`950`, `emerald-*` for the one accent, `gold`/`thread`
  for the exposure-path highlight). No saturated colors.
- Canvas/graph-specific styling (React Flow node/edge classes, keyframe
  animations) stays in `index.css` as plain CSS — Tailwind isn't a good fit
  for React Flow's DOM structure or custom keyframes. Everything else
  (sidebar, command palette, any new panel) should be Tailwind, not a new
  custom CSS block.
- All server state lives in `store/useAriadneStore.ts`. If a fetch needs to
  update both the canvas highlight and the sidebar, that belongs in one
  store action (see `analyzeNode`), not duplicated across components —
  this project already had a bug where two components independently
  re-fetched the same (LLM-backed, non-free) endpoint.
