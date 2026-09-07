import dagre from 'dagre'
import type { Node } from 'reactflow'

const NODE_WIDTH = 170
const NODE_HEIGHT = 56

/**
 * Layered left-to-right layout so the graph reads the way the exposure path
 * does: internet-facing entry points on the left, everything they can reach
 * fanning out to the right (CLAUDE.md's "Internet -> Nginx -> Spring Boot
 * API -> Vulnerable Library" example).
 */
export function layoutNodes(nodes: Node[], edges: { source: string; target: string }[]): Node[] {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'LR', nodesep: 48, ranksep: 120 })

  for (const node of nodes) {
    g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target)
  }

  dagre.layout(g)

  return nodes.map((node) => {
    const { x, y } = g.node(node.id)
    return { ...node, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } }
  })
}
