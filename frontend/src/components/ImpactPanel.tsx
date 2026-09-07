import { useState } from 'react'
import { useAriadneStore } from '../store/useAriadneStore'
import type { Mitigation } from '../types/graph'

/**
 * Reacts to canvas/palette state instead of holding a chat history. All
 * fetching lives in the store (analyzeNode / ingestAndAnalyze) -- this
 * component is purely presentational so it never triggers a duplicate
 * Gemini call on top of whatever action (click, paste) populated it.
 */
export function ImpactPanel() {
  const cti = useAriadneStore((s) => s.cti)
  const selectedNodeId = useAriadneStore((s) => s.selectedNodeId)
  const analysis = useAriadneStore((s) => s.analysis)

  return (
    <aside className="flex h-full flex-col overflow-y-auto border-l border-gray-800 bg-gray-950 p-5 text-gray-300">
      <h2 className="m-0 text-[13px] font-semibold uppercase tracking-[0.08em] text-gray-100">
        {selectedNodeId ? `Node ${selectedNodeId}` : 'Threat Intelligence'}
      </h2>

      {cti ? (
        <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
          <dt className="text-gray-500">CVE</dt>
          <dd className="m-0 text-gray-100">{cti.cveId}</dd>
          <dt className="text-gray-500">Target software</dt>
          <dd className="m-0 text-gray-100">{cti.targetSoftware}</dd>
          <dt className="text-gray-500">Affected versions</dt>
          <dd className="m-0 text-gray-100">{cti.affectedVersions}</dd>
          <dt className="text-gray-500">Attack vector</dt>
          <dd className="m-0 text-gray-100">{cti.attackVector}</dd>
          <dt className="text-gray-500">Source</dt>
          <dd className="m-0 text-gray-100">{cti.sourceReport}</dd>
        </dl>
      ) : (
        <p className="mt-4 text-xs italic text-gray-500">
          No report ingested yet. Press Ctrl+K to paste a threat advisory.
        </p>
      )}

      {analysis && <MitigationBlock mitigation={analysis.mitigation} />}

      {analysis && (
        <section className="mt-4">
          <h3 className="m-0 text-[10px] font-semibold uppercase tracking-[0.14em] text-gray-500">
            Blast Radius
          </h3>
          <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
            <dt className="text-gray-500">Exposure</dt>
            <dd className="m-0 text-gray-100">{analysis.exposureLevel}</dd>
            <dt className="text-gray-500">Broken dependencies</dt>
            <dd className="m-0 text-gray-100">{analysis.brokenDependencies.join(', ') || 'none'}</dd>
          </dl>
        </section>
      )}
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
    <section className="mt-4 rounded-lg border border-gray-800 bg-gray-900 p-3">
      <h3 className="m-0 text-[10px] font-semibold uppercase tracking-[0.14em] text-gray-500">
        Recommended Mitigation
      </h3>

      <p className="mt-2 text-xs leading-relaxed text-gray-300">{mitigation.summary}</p>

      {mitigation.patch && (
        <>
          <pre className="mt-2 overflow-x-auto rounded-md border border-gray-800 bg-gray-950 p-2.5">
            <code className="font-mono text-[12px] leading-relaxed text-emerald-400">
              {mitigation.patch}
            </code>
          </pre>

          <button
            type="button"
            onClick={handleCopy}
            className="mt-2.5 w-full rounded-md border border-gray-800 py-1.5 text-[11px] font-medium uppercase tracking-wide text-gray-400 transition-all duration-150 hover:border-emerald-500/50 hover:text-emerald-400 hover:shadow-[0_0_14px_-3px_rgba(16,185,129,0.6)] active:scale-[0.98]"
          >
            {copied ? 'Copied' : 'Copy to clipboard'}
          </button>
        </>
      )}
    </section>
  )
}
