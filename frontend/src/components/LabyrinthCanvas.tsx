import { useMemo } from 'react'
import ReactFlow, { Background, BackgroundVariant, MarkerType, type Edge, type Node } from 'reactflow'
import 'reactflow/dist/style.css'
import { layoutNodes } from '../lib/layout'
import { useAriadneStore } from '../store/useAriadneStore'
import { ServiceNode } from './nodes/ServiceNode'

const nodeTypes = { service: ServiceNode }

/**
 * The main view: a dark, interactive canvas rendering the live topology in
 * a left-to-right layered layout (internet-facing entry points on the
 * left). When a node is selected, its exposure path lights up gold --
 * "Ariadne's Thread" -- as the attack-path output rendered instead of
 * described.
 */
export function LabyrinthCanvas() {
  const nodes = useAriadneStore((s) => s.nodes)
  const edges = useAriadneStore((s) => s.edges)
  const selectedNodeId = useAriadneStore((s) => s.selectedNodeId)
  const highlightedNodeIds = useAriadneStore((s) => s.highlightedNodeIds)
  const highlightedEdgeIds = useAriadneStore((s) => s.highlightedEdgeIds)
  const selectNode = useAriadneStore((s) => s.selectNode)

  const flowNodes: Node[] = useMemo(() => {
    const positioned = layoutNodes(
      nodes.map((n) => ({
        id: n.id,
        type: 'service',
        position: { x: 0, y: 0 },
        data: { label: n.label, kind: n.kind, compromised: n.compromised },
      })),
      edges,
    )
    return positioned.map((n) => ({
      ...n,
      selected: n.id === selectedNodeId,
      className: highlightedNodeIds.has(n.id) ? 'is-on-thread' : undefined,
    }))
  }, [nodes, edges, selectedNodeId, highlightedNodeIds])

  const flowEdges: Edge[] = useMemo(
    () =>
      edges.map((e) => {
        const onThread = highlightedEdgeIds.has(e.id)
        return {
          id: e.id,
          source: e.source,
          target: e.target,
          animated: onThread,
          className: onThread ? 'edge--thread' : `edge--${e.kind.toLowerCase()}`,
          markerEnd: { type: MarkerType.ArrowClosed, color: onThread ? '#d4af37' : '#4b4e5c' },
        }
      }),
    [edges, highlightedEdgeIds],
  )

  return (
    <div className="labyrinth-canvas">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => selectNode(node.id)}
        onPaneClick={() => selectNode(null)}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#2a2d3a" />
      </ReactFlow>
    </div>
  )
}
