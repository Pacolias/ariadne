import axios from 'axios'
import type { ComponentAnalysis, CtiSummary, QueryResult, TopologyEdge, TopologyNode } from '../types/graph'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
})

export interface TopologyResponse {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  cti: CtiSummary | null
}

export async function fetchTopology(): Promise<TopologyResponse> {
  const { data } = await client.get<TopologyResponse>('/api/graph/topology')
  return data
}

/** Consolidated Phase 3 call: exposure path + exposure level + blast radius
 * + grounded mitigation, resolved server-side in one round trip. */
export async function analyzeComponent(component: string): Promise<ComponentAnalysis> {
  const { data } = await client.post<ComponentAnalysis>('/api/analyze', { component })
  return data
}

export async function runQuery(query: string): Promise<QueryResult> {
  const { data } = await client.post<QueryResult>('/api/query', { query })
  return data
}

/** Phase 1: parses raw CTI text (a pasted blog post, advisory, PDF dump)
 * into a structured CVE/software/attack-vector summary, and flags the
 * matching graph node as compromised. */
export async function ingestCti(text: string, sourceReport: string): Promise<CtiSummary> {
  // Note: /api/cti/ingest's request body is plain BaseModel (snake_case),
  // unlike the CamelModel responses used everywhere else in this API.
  const { data } = await client.post<CtiSummary>('/api/cti/ingest', {
    text,
    source_report: sourceReport,
  })
  return data
}
