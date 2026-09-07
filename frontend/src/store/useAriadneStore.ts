import { create } from 'zustand'
import type { CtiSummary, ImpactMetrics, Mitigation, TopologyEdge, TopologyNode } from '../types/graph'

interface AriadneState {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  cti: CtiSummary | null
  selectedNodeId: string | null
  impact: ImpactMetrics | null
  mitigation: Mitigation | null
  commandPaletteOpen: boolean

  /** Ariadne's Thread: which nodes/edges to light up right now. Kept
   * separate from `nodes`/`edges` so highlighting a path never clobbers the
   * backend-sourced `compromised` truth on unrelated nodes. */
  highlightedNodeIds: Set<string>
  highlightedEdgeIds: Set<string>

  setTopology: (nodes: TopologyNode[], edges: TopologyEdge[], cti: CtiSummary | null) => void
  selectNode: (nodeId: string | null) => void
  setImpact: (impact: ImpactMetrics | null) => void
  setMitigation: (mitigation: Mitigation | null) => void
  setHighlight: (nodeIds: string[], edgeIds: string[]) => void
  clearHighlight: () => void
  setCommandPaletteOpen: (open: boolean) => void
}

export const useAriadneStore = create<AriadneState>((set) => ({
  nodes: [],
  edges: [],
  cti: null,
  selectedNodeId: null,
  impact: null,
  mitigation: null,
  commandPaletteOpen: false,
  highlightedNodeIds: new Set(),
  highlightedEdgeIds: new Set(),

  setTopology: (nodes, edges, cti) => set({ nodes, edges, cti }),

  selectNode: (nodeId) => set({ selectedNodeId: nodeId, impact: null, mitigation: null }),

  setImpact: (impact) => set({ impact }),

  setMitigation: (mitigation) => set({ mitigation }),

  setHighlight: (nodeIds, edgeIds) =>
    set({ highlightedNodeIds: new Set(nodeIds), highlightedEdgeIds: new Set(edgeIds) }),

  clearHighlight: () => set({ highlightedNodeIds: new Set(), highlightedEdgeIds: new Set() }),

  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
}))
