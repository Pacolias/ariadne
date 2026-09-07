import { useEffect, useRef, useState } from 'react'
import { runQuery } from '../lib/api'
import { useAriadneStore, type IngestPhase } from '../store/useAriadneStore'

const PHASE_LABEL: Record<Exclude<IngestPhase, 'idle'>, string> = {
  parsing: 'Parsing threat intelligence…',
  traversing: 'Traversing graph topology…',
}

/**
 * The chat, evolved: a Ctrl+K modal instead of a persistent chat window.
 * Two modes stacked in one panel: a quick natural-language query on top
 * (answers through canvas highlighting), and a paste-a-full-report flow
 * below it that drives the real ingest -> analyze pipeline (Neo4j + Gemini).
 */
export function CommandPalette() {
  const open = useAriadneStore((s) => s.commandPaletteOpen)
  const setOpen = useAriadneStore((s) => s.setCommandPaletteOpen)
  const highlightPath = useAriadneStore((s) => s.highlightPath)
  const clearHighlight = useAriadneStore((s) => s.clearHighlight)
  const ingestPhase = useAriadneStore((s) => s.ingestPhase)
  const ingestAndAnalyze = useAriadneStore((s) => s.ingestAndAnalyze)

  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [queryPending, setQueryPending] = useState(false)
  const [reportText, setReportText] = useState('')
  const [ingestError, setIngestError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const isIngesting = ingestPhase !== 'idle'

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(!open)
      }
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, setOpen])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  async function handleQuerySubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim() || isIngesting) return
    setQueryPending(true)
    clearHighlight()
    try {
      const result = await runQuery(query)
      setAnswer(result.answer)
      highlightPath(result.highlightedNodeIds, result.highlightedEdgeIds)
    } catch {
      setAnswer('Insufficient Topology Data')
    } finally {
      setQueryPending(false)
    }
  }

  async function handleIngest() {
    if (!reportText.trim() || isIngesting) return
    setIngestError(null)
    try {
      await ingestAndAnalyze(reportText)
      setReportText('')
      setOpen(false)
    } catch {
      setIngestError('Could not reach the analysis engine. Check the backend and try again.')
    }
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[1000] flex items-start justify-center bg-black/60 pt-[12vh]"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-[min(600px,92vw)] rounded-xl border border-gray-800 bg-gray-950 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <form onSubmit={handleQuerySubmit} className="border-b border-gray-800">
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isIngesting}
            placeholder="Ask about an attack path, e.g. 'is auth-api reachable from the internet?'"
            autoComplete="off"
            className="w-full bg-transparent px-4 py-3 text-sm text-gray-100 placeholder-gray-600 outline-none disabled:opacity-50"
          />
        </form>
        {queryPending && <p className="px-4 pt-2 text-xs text-gray-500">Tracing the thread…</p>}
        {answer && !queryPending && <p className="px-4 pt-2 text-xs text-gray-300">{answer}</p>}

        <div className="p-4">
          <label
            htmlFor="cti-paste"
            className="block text-[10px] font-semibold uppercase tracking-[0.14em] text-gray-500"
          >
            Paste threat intel
          </label>
          <textarea
            id="cti-paste"
            rows={6}
            value={reportText}
            onChange={(e) => setReportText(e.target.value)}
            disabled={isIngesting}
            placeholder="Paste the raw text of a vulnerability report, advisory, or blog post…"
            className="mt-2 w-full resize-none rounded-md border border-gray-800 bg-gray-900 p-2.5 font-mono text-xs leading-relaxed text-gray-200 placeholder-gray-600 outline-none focus:border-emerald-500/50 disabled:opacity-50"
          />

          <button
            type="button"
            onClick={handleIngest}
            disabled={isIngesting || !reportText.trim()}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-md border border-emerald-600/40 bg-emerald-500/10 py-2 text-xs font-semibold uppercase tracking-wide text-emerald-400 transition-all duration-150 hover:border-emerald-500 hover:bg-emerald-500/20 hover:shadow-[0_0_16px_-3px_rgba(16,185,129,0.6)] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:shadow-none"
          >
            {isIngesting && (
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-emerald-400/30 border-t-emerald-400" />
            )}
            {isIngesting ? PHASE_LABEL[ingestPhase as Exclude<IngestPhase, 'idle'>] : 'Ingest & Analyze Threat'}
          </button>

          {ingestError && <p className="mt-2 text-xs text-red-400">{ingestError}</p>}
        </div>
      </div>
    </div>
  )
}
