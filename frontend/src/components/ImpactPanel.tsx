import { useEffect, useState } from 'react'
import { fetchExposurePath, fetchImpact, fetchMitigation } from '../lib/api'
import { useAriadneStore } from '../store/useAriadneStore'
import type { Mitigation } from '../types/graph'

/** Shown when the live LLM mitigation call fails (typically: no
 * ANTHROPIC_API_KEY configured) so the panel never goes blank on a node
 * that's actually compromised. Kept separate from backend logic so it's
 * obvious this is a demo fallback, not a real recommendation source. */
function offlineFallback(nodeId: string): Mitigation {
  return {
    nodeId,
    summary: 'Disable JNDI message lookups at the JVM level — no code change, no restart-heavy rollout.',
    patch: 'JAVA_OPTS="-Dlog4j2.formatMsgNoLookups=true"',
  }
}

/**
 * Reacts to canvas selection instead of holding a chat history:
 * nothing selected -> global CTI facts; a node selected -> its exposure
 * path lit up on the canvas (free, deterministic) plus quantitative impact
 * metrics and the LLM-generated mitigation card (needs ANTHROPIC_API_KEY).
 */
export function ImpactPanel() {
  const cti = useAriadneStore((s) => s.cti)
  const selectedNodeId = useAriadneStore((s) => s.selectedNodeId)
  const impact = useAriadneStore((s) => s.impact)
  const mitigation = useAriadneStore((s) => s.mitigation)
  const setImpact = useAriadneStore((s) => s.setImpact)
  const setMitigation = useAriadneStore((s) => s.setMitigation)
  const setHighlight = useAriadneStore((s) => s.setHighlight)
  const clearHighlight = useAriadneStore((s) => s.clearHighlight)

  useEffect(() => {
    if (!selectedNodeId) {
      clearHighlight()
      return
    }
    fetchImpact(selectedNodeId).then(setImpact).catch(() => setImpact(null))
    fetchMitigation(selectedNodeId)
      .then(setMitigation)
      .catch(() => setMitigation(offlineFallback(selectedNodeId)))
    fetchExposurePath(selectedNodeId)
      .then((path) => setHighlight(path.nodeIds, path.edgeIds))
      .catch(() => setHighlight([], []))
  }, [selectedNodeId, setImpact, setMitigation, setHighlight, clearHighlight])

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

      {impact && (
        <section>
          <h3>Blast Radius</h3>
          <dl>
            <dt>Asset recall</dt>
            <dd>{(impact.assetRecall * 100).toFixed(0)}%</dd>
            <dt>Exposure</dt>
            <dd>{impact.exposureLevel}</dd>
            <dt>Broken dependencies</dt>
            <dd>{impact.brokenDependencies.join(', ') || 'none'}</dd>
          </dl>
        </section>
      )}

      {mitigation && <MitigationBlock mitigation={mitigation} />}
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

      <pre className="mt-2 overflow-x-auto rounded-md border border-gray-800 bg-black/40 p-2.5">
        <code className="font-mono text-[12px] leading-relaxed text-emerald-300/90">{mitigation.patch}</code>
      </pre>

      <button
        type="button"
        onClick={handleCopy}
        className="mt-2.5 w-full rounded-md border border-gray-800 py-1.5 text-[11px] font-medium uppercase tracking-wide text-gray-400 transition-all duration-150 hover:border-emerald-500/50 hover:text-emerald-400 hover:shadow-[0_0_14px_-3px_rgba(16,185,129,0.6)] active:scale-[0.98]"
      >
        {copied ? 'Copied' : 'Copy Rule'}
      </button>
    </section>
  )
}
