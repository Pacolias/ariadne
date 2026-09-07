import { create } from 'zustand'
import type { ComponentAnalysis, CtiSummary, TopologyEdge, TopologyNode } from '../types/graph'

interface AriadneState {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  cti: CtiSummary | null
  selectedNodeId: string | null
  analysis: ComponentAnalysis | null
  commandPaletteOpen: boolean

  /** Ariadne's Thread: which nodes/edges to light up right now. Kept
   * separate from `nodes`/`edges` so highlighting a path never clobbers the
   * backend-sourced `compromised` truth on unrelated nodes. */
  highlightedNodeIds: Set<string>
  highlightedEdgeIds: Set<string>

  setTopology: (nodes: TopologyNode[], edges: TopologyEdge[], cti: CtiSummary | null) => void
  selectNode: (nodeId: string | null) => void
  setAnalysis: (analysis: ComponentAnalysis | null) => void
  setHighlight: (nodeIds: string[], edgeIds: string[]) => void
  clearHighlight: () => void
  setCommandPaletteOpen: (open: boolean) => void
}

export const useAriadneStore = create<AriadneState>((set) => ({
  nodes: [],
  edges: [],
  cti: null,
  selectedNodeId: null,
  analysis: null,
  commandPaletteOpen: false,
  highlightedNodeIds: new Set(),
  highlightedEdgeIds: new Set(),

  setTopology: (nodes, edges, cti) => set({ nodes, edges, cti }),

  selectNode: (nodeId) => set({ selectedNodeId: nodeId, analysis: null }),

  setAnalysis: (analysis) => set({ analysis }),

  setHighlight: (nodeIds, edgeIds) =>
    set({ highlightedNodeIds: new Set(nodeIds), highlightedEdgeIds: new Set(edgeIds) }),

  clearHighlight: () => set({ highlightedNodeIds: new Set(), highlightedEdgeIds: new Set() }),

  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
}))
