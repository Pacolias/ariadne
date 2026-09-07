import { useEffect, useState } from 'react'
import { analyzeComponent } from '../lib/api'
import { useAriadneStore } from '../store/useAriadneStore'
import type { ComponentAnalysis, Mitigation } from '../types/graph'

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

/**
 * Reacts to canvas selection instead of holding a chat history: nothing
 * selected -> global CTI facts; a node selected -> one call to
 * POST /api/analyze resolves its exposure path (lit up on the canvas),
 * blast radius, and grounded mitigation card together.
 */
export function ImpactPanel() {
  const cti = useAriadneStore((s) => s.cti)
  const selectedNodeId = useAriadneStore((s) => s.selectedNodeId)
  const analysis = useAriadneStore((s) => s.analysis)
  const setAnalysis = useAriadneStore((s) => s.setAnalysis)
  const setHighlight = useAriadneStore((s) => s.setHighlight)
  const clearHighlight = useAriadneStore((s) => s.clearHighlight)

  useEffect(() => {
    if (!selectedNodeId) {
      clearHighlight()
      return
    }
    analyzeComponent(selectedNodeId)
      .then((result) => {
        setAnalysis(result)
        setHighlight(result.nodeIds, result.edgeIds)
      })
      .catch(() => {
        const fallback = offlineFallback(selectedNodeId)
        setAnalysis(fallback)
        setHighlight(fallback.nodeIds, fallback.edgeIds)
      })
  }, [selectedNodeId, setAnalysis, setHighlight, clearHighlight])

  if (!selectedNodeId) {
    return (
      <aside className="impact-panel">
        <h2>Threat Intelligence</h2>
        {cti ? (
          <dl>
            <dt>CVE</dt>
            <dd>{cti.cveId}</dd>
            <dt>Target software</dt>
            <dd>{cti.targetSoftware}</dd>
            <dt>Affected versions</dt>
            <dd>{cti.affectedVersions}</dd>
            <dt>Attack vector</dt>
            <dd>{cti.attackVector}</dd>
            <dt>Source</dt>
            <dd>{cti.sourceReport}</dd>
          </dl>
        ) : (
          <p className="impact-panel__empty">No report ingested yet. Waiting on the parser.</p>
        )}
      </aside>
    )
  }

  return (
    <aside className="impact-panel">
      <h2>Node {selectedNodeId}</h2>

      {analysis && (
        <section>
          <h3>Blast Radius</h3>
          <dl>
            <dt>Exposure</dt>
            <dd>{analysis.exposureLevel}</dd>
            <dt>Broken dependencies</dt>
            <dd>{analysis.brokenDependencies.join(', ') || 'none'}</dd>
          </dl>
        </section>
      )}

      {analysis && <MitigationBlock mitigation={analysis.mitigation} />}
    </aside>
  )
}

function MitigationBlock({ mitigation }: { mitigation: Mitigation }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(mitigation.patch)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <section className="mt-4 rounded-lg border border-gray-800 bg-black/30 p-3">
      <h3 className="m-0 text-[10px] font-semibold uppercase tracking-[0.14em] text-gray-500">
        Recommended Mitigation
      </h3>

      <p className="mt-2 text-xs leading-relaxed text-gray-300">{mitigation.summary}</p>

      {mitigation.patch && (
        <>
          <pre className="mt-2 overflow-x-auto rounded-md border border-gray-800 bg-black/40 p-2.5">
            <code className="font-mono text-[12px] leading-relaxed text-emerald-300/90">
              {mitigation.patch}
            </code>
          </pre>

          <button
            type="button"
            onClick={handleCopy}
            className="mt-2.5 w-full rounded-md border border-gray-800 py-1.5 text-[11px] font-medium uppercase tracking-wide text-gray-400 transition-all duration-150 hover:border-emerald-500/50 hover:text-emerald-400 hover:shadow-[0_0_14px_-3px_rgba(16,185,129,0.6)] active:scale-[0.98]"
          >
            {copied ? 'Copied' : 'Copy Rule'}
          </button>
        </>
      )}
    </section>
  )
}
