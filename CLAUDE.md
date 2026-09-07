# CLAUDE.md: Zero-Day Impact & Remediation Engine

## Project Vision
You are an expert AI Engineer coding an enterprise-grade cybersecurity reasoning engine. The goal is to build a Parser + GraphRAG pipeline that ingests unstructured Cyber Threat Intelligence (CTI) and internal SBOM/Infrastructure data to automatically determine the exact attack path of a zero-day vulnerability and propose a minimum safe remediation.

**Crucial:** This is NOT a basic Q&A chatbot. This is a deterministic, mathematically evaluated reasoning engine. Zero hallucinations are tolerated in asset identification.

## Architecture & Tech Stack
- **Languages:** Python 3.11+
- **Parsing:** `LlamaParse` / `unstructured` (for CTI reports), custom JSON/YAML parsers for SBOMs (CycloneDX) and IaC (Terraform/Docker Compose).
- **Graph Storage:** `NetworkX` (for prototyping in-memory) or `Neo4j` (for persistence).
- **Vector Storage:** `Qdrant` or `Pinecone` (for semantic search of CTI context).
- **Orchestration:** `LangChain` or `LlamaIndex` (Property Graph Index).
- **Evaluation:** `Ragas`, `DeepEval`, or custom `pytest` fixtures for ground-truth validation.

## Data Topology (Mock Environment)
Assume we are protecting a modern microservices architecture:
- Backend APIs (Spring Boot, Java, JWT authentication).
- Frontend clients (React, Vite, TypeScript).
- Databases (MySQL).
- Containerization (Docker, Docker Compose deployment configurations).

## Execution Phases

### Phase 1: The Semantic Parsers (Data Ingestion)
1. Write a parser module that takes a Mandiant/CrowdStrike threat report (PDF/Markdown) and extracts a structured schema: `CVE_ID`, `Target_Software`, `Affected_Versions`, `Attack_Vector` (e.g., HTTP header injection).
2. Write an internal parser that reads `pom.xml`, `package.json`, and `docker-compose.yml` files to extract dependencies, service ports, and internal network visibility.

### Phase 2: The Knowledge Graph (Topology Mapping)
1. Map the parsed internal data into a directed graph. 
2. Nodes: `Service` (e.g., Auth-API), `Library` (e.g., log4j-core), `Endpoint` (e.g., port 443).
3. Edges: `DEPENDS_ON`, `EXPOSES`, `COMMUNICATES_WITH`.
4. Ensure the graph can answer reachability queries: "Is Library X reachable from the public internet?"

### Phase 3: The Hybrid RAG Engine (Reasoning)
1. Given a new CTI alert, retrieve the affected software from the vector store.
2. Query the Knowledge Graph to find all internal assets containing that software.
3. Traverse the graph to determine the **Exposure Path** (e.g., Internet -> Nginx -> Spring Boot API -> Vulnerable Library).
4. Inject this specific subgraph and the original CTI context into the LLM prompt.
5. Force the LLM to output a JSON/Markdown response with: `Affected_Assets`, `Exploitability_Confidence`, and `Proposed_Mitigation` (e.g., specific WAF rule or environment variable toggle).

### Phase 4: Quantitative Evaluation (The Ground Truth)
1. Create a `data/ground_truth.json` file containing 10 historical vulnerabilities applied to our mock architecture.
2. Build an automated test suite that runs the engine against these 10 scenarios.
3. Calculate and assert strictly on the following metrics:
   - **Asset Recall:** Must be 100% (missing a vulnerable asset is a critical failure).
   - **Exposure Accuracy:** Must correctly identify isolated vs. exposed services >90%.
   - **Hallucination Rate:** Must be 0% for IP addresses and service names.

## Repository Layout
This is a two-part repository: `backend/` (this document's primary focus — the Parser+GraphRAG engine) and `frontend/` (the Ariadne-themed visual interface, described below). Treat them as independently deployable services connected by a REST/WebSocket API — the frontend never talks to Neo4j/Qdrant directly.

## Frontend: The Ariadne Interface
The frontend is themed around the myth of Ariadne's thread through the Labyrinth. **This is a deliberate design choice, not decoration** — it maps directly onto the product's core mechanic (tracing an exposure path through a network graph), so preserve the metaphor rather than defaulting to a generic dashboard or chatbot UI.

- **Stack:** React + Vite + TypeScript. Graph rendering via `React Flow` (or equivalent) on a dark, full-bleed canvas.
- **The Labyrinth Canvas (main view):** An interactive dark canvas rendering the live network topology (services, libraries, endpoints as nodes; dependencies/network paths as edges). Occupies the majority of the screen.
- **Ariadne's Thread (the core visual payoff):** When a threat report is ingested, do NOT surface this as a chat message first. The affected node pulses red, and a glowing thread animates along the exact traversed path from the public entry point (internet) to the vulnerable microservice — this IS the attack path / blast radius output of Phase 3, rendered visually instead of as text.
- **Impact Panel (dynamic sidebar):** Reacts to canvas selection state rather than holding a chat history.
  - Nothing selected → global state: parsed CTI facts (CVE, attack tactics, report source).
  - Red node selected → quantitative evaluation metrics for that node (Asset Recall, exposure level, broken dependencies).
  - Mitigation card: the LLM-generated fix (firewall rule / patch), copyable, with a simulated "Apply Patch" action.
- **Command Palette (the "chat," evolved):** No visible persistent chatbot. Natural-language queries go through a `Ctrl+K` Spotlight/Raycast-style modal. Responses are NOT primarily textual — the query result manifests as canvas state changes (filtering, highlighting, grouping nodes), with text as secondary confirmation.

## Infrastructure
- **Local-first via Docker Compose.** Neo4j and Qdrant run as self-hosted containers defined in a root `docker-compose.yml` — no managed cloud services required. This keeps the project fully reproducible for anyone cloning the repo (important for portfolio review).
- Backend exposes its API (FastAPI) as its own service in the same compose file; frontend consumes it over HTTP/WebSocket.

## LLM Strategy (concrete instantiation of "LLM Independence" below)
- **Ollama (local models):** bulk/cheap extraction work — CTI entity extraction, SBOM/IaC parsing assistance. Zero marginal cost, runs offline.
- **Anthropic Claude API:** the Phase 3 reasoning step only — synthesizing the retrieved CTI context + exposure subgraph into the final grounded output (`Affected_Assets`, `Exploitability_Confidence`, `Proposed_Mitigation`). This is where hallucination tolerance is zero, so the stronger model is reserved for it.

## Data Strategy
- **CTI reports:** real, publicly available threat intel (Mandiant, CrowdStrike, NVD advisories, etc.) — parsed for genuine, citable extraction quality.
- **Internal topology / SBOMs / ground truth:** synthetic — a mock microservices environment (per Data Topology below) built specifically so the 50-100 ground-truth vulnerability scenarios have a known-correct answer to evaluate against.

## Coding Rules & Constraints
- **Type Hinting:** Strictly enforce Python type hints (`typing` module) across all functions.
- **Modularity:** Separate extraction logic from LLM generation logic. The graph traversal must be deterministic code, not delegated to the LLM.
- **LLM Independence:** Use generic interfaces. The system should easily swap between Anthropic Claude 3.5 Sonnet (for reasoning) and local models (e.g., via Ollama) for basic parsing.
- **Error Handling:** If the graph cannot resolve an attack path, the system must explicitly return "Insufficient Topology Data", never guess.
