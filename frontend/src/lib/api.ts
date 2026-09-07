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
