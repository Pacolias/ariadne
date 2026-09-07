import axios from 'axios'
import type {
  CtiSummary,
  ExposurePath,
  ImpactMetrics,
  Mitigation,
  QueryResult,
  TopologyEdge,
  TopologyNode,
} from '../types/graph'

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

export async function fetchImpact(nodeId: string): Promise<ImpactMetrics> {
  const { data } = await client.get<ImpactMetrics>(`/api/graph/nodes/${nodeId}/impact`)
  return data
}

export async function fetchExposurePath(nodeId: string): Promise<ExposurePath> {
  const { data } = await client.get<ExposurePath>(`/api/graph/nodes/${nodeId}/exposure-path`)
  return data
}

export async function fetchMitigation(nodeId: string): Promise<Mitigation> {
  const { data } = await client.get<Mitigation>(`/api/graph/nodes/${nodeId}/mitigation`)
  return data
}

export async function runQuery(query: string): Promise<QueryResult> {
  const { data } = await client.post<QueryResult>('/api/query', { query })
  return data
}
