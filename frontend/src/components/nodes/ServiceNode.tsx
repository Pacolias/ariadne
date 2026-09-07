import { Handle, Position, type NodeProps } from 'reactflow'
import type { TopologyNode } from '../../types/graph'

type ServiceNodeData = Pick<TopologyNode, 'label' | 'kind' | 'compromised'>

export function ServiceNode({ data }: NodeProps<ServiceNodeData>) {
  return (
    <div className={`service-node service-node--${data.kind} ${data.compromised ? 'is-compromised' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <span className="service-node__kind">{data.kind}</span>
      <span className="service-node__label">{data.label}</span>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}
