// Mirrors the backend's graph & reasoning schemas (backend/src/ariadne/schemas.py).
// Keep these in sync manually until the API exposes a generated OpenAPI client.

export type NodeKind = 'service' | 'library' | 'endpoint' | 'database'

export interface TopologyNode {
  id: string
  kind: NodeKind
  label: string
  /** True once this node has been identified as reachable by an ingested CTI report. */
  compromised: boolean
  metadata?: Record<string, string>
}

export type EdgeKind = 'DEPENDS_ON' | 'EXPOSES' | 'COMMUNICATES_WITH'

export interface TopologyEdge {
  id: string
  source: string
  target: string
  kind: EdgeKind
}

export interface CtiSummary {
  cveId: string
  targetSoftware: string
  affectedVersions: string
  attackVector: string
  sourceReport: string
}

export interface ImpactMetrics {
  nodeId: string
  assetRecall: number
  exposureLevel: 'isolated' | 'internal' | 'public-facing'
  brokenDependencies: string[]
}

export interface Mitigation {
  nodeId: string
  summary: string
  patch: string
}

export interface QueryResult {
  answer: string
  highlightedNodeIds: string[]
  highlightedEdgeIds: string[]
}

/** Deterministic graph traversal only -- no LLM, no API key required. */
export interface ExposurePath {
  nodeIds: string[]
  edgeIds: string[]
}

/** Consolidated Phase 3 output: POST /api/analyze — resolves a component
 * name to its exposure path, exposure level, blast radius, and grounded
 * mitigation in a single call (replaces impact + exposure-path + mitigation). */
export interface ComponentAnalysis {
  component: string
  nodeIds: string[]
  edgeIds: string[]
  exposureLevel: 'isolated' | 'internal' | 'public-facing'
  brokenDependencies: string[]
  mitigation: Mitigation
}
