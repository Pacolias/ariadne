import { create } from 'zustand'
import { analyzeComponent, ingestCti } from '../lib/api'
import type { ComponentAnalysis, CtiSummary, TopologyEdge, TopologyNode } from '../types/graph'

export type IngestPhase = 'idle' | 'parsing' | 'traversing'

/** Shown when /api/analyze itself is unreachable (network error, backend
 * down) so the panel never goes blank on a node that's actually
 * compromised. Kept separate from backend logic so it's obvious this is a
 * demo fallback, not a real recommendation source. */
function offlineFallback(nodeId: string): ComponentAnalysis {
  return {
    component: nodeId,
    nodeIds: [nodeId],
    edgeIds: [],
    exposureLevel: 'isolated',
    brokenDependencies: [],
    mitigation: {
      nodeId,
      summary: 'Disable JNDI message lookups at the JVM level — no code change, no restart-heavy rollout.',
      patch: 'JAVA_OPTS="-Dlog4j2.formatMsgNoLookups=true"',
    },
  }
}

interface AriadneState {
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  cti: CtiSummary | null
  selectedNodeId: string | null
  analysis: ComponentAnalysis | null
  commandPaletteOpen: boolean

  /** Two-phase status for the CTI paste-and-analyze flow: 'parsing' while
   * /api/cti/ingest runs, 'traversing' while the follow-up /api/analyze
   * (Neo4j + Gemini) runs. Also drives the canvas pulse effect. */
  ingestPhase: IngestPhase

  /** Ariadne's Thread: which nodes/edges to light up right now. Kept
   * separate from `nodes`/`edges` so highlighting a path never clobbers the
   * backend-sourced `compromised` truth on unrelated nodes. */
  highlightedNodeIds: Set<string>
  highlightedEdgeIds: Set<string>

  setTopology: (nodes: TopologyNode[], edges: TopologyEdge[], cti: CtiSummary | null) => void
  clearSelection: () => void
  /** Click-to-inspect: resolves a node's exposure path + mitigation
   * (POST /api/analyze) and lights up the thread. */
  analyzeNode: (nodeId: string) => Promise<void>
  /** The Command Palette's paste-a-report flow: parses the text
   * (POST /api/cti/ingest), then feeds the resulting target software
   * straight into analyzeNode -- one user action, two chained calls. */
  ingestAndAnalyze: (text: string) => Promise<void>
  /** Used by the Command Palette's free-text query (POST /api/query), which
   * highlights a path without going through node selection/analysis. */
  highlightPath: (nodeIds: string[], edgeIds: string[]) => void
  clearHighlight: () => void
  setCommandPaletteOpen: (open: boolean) => void
}

export const useAriadneStore = create<AriadneState>((set, get) => ({
  nodes: [],
  edges: [],
  cti: null,
  selectedNodeId: null,
  analysis: null,
  commandPaletteOpen: false,
  ingestPhase: 'idle',
  highlightedNodeIds: new Set(),
  highlightedEdgeIds: new Set(),

  setTopology: (nodes, edges, cti) => set({ nodes, edges, cti }),

  clearSelection: () =>
    set({
      selectedNodeId: null,
      analysis: null,
      highlightedNodeIds: new Set(),
      highlightedEdgeIds: new Set(),
    }),

  analyzeNode: async (nodeId) => {
    set({ selectedNodeId: nodeId, analysis: null })
    try {
      const result = await analyzeComponent(nodeId)
      set({
        analysis: result,
        highlightedNodeIds: new Set(result.nodeIds),
        highlightedEdgeIds: new Set(result.edgeIds),
      })
    } catch {
      const fallback = offlineFallback(nodeId)
      set({
        analysis: fallback,
        highlightedNodeIds: new Set(fallback.nodeIds),
        highlightedEdgeIds: new Set(fallback.edgeIds),
      })
    }
  },

  ingestAndAnalyze: async (text) => {
    set({ ingestPhase: 'parsing' })
    try {
      const cti = await ingestCti(text, 'pasted-report')
      set({ cti, ingestPhase: 'traversing' })
      await get().analyzeNode(cti.targetSoftware)
    } finally {
      set({ ingestPhase: 'idle' })
    }
  },

  highlightPath: (nodeIds, edgeIds) =>
    set({ highlightedNodeIds: new Set(nodeIds), highlightedEdgeIds: new Set(edgeIds) }),

  clearHighlight: () => set({ highlightedNodeIds: new Set(), highlightedEdgeIds: new Set() }),

  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
}))
