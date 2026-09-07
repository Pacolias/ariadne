import { useEffect, useRef, useState } from 'react'
import { runQuery } from '../lib/api'
import { useAriadneStore } from '../store/useAriadneStore'

/**
 * The chat, evolved: a Ctrl+K modal instead of a persistent chat window.
 * A submitted query answers primarily through canvas state (highlighted
 * exposure path), with text as secondary confirmation.
 */
export function CommandPalette() {
  const open = useAriadneStore((s) => s.commandPaletteOpen)
  const setOpen = useAriadneStore((s) => s.setCommandPaletteOpen)
  const setHighlight = useAriadneStore((s) => s.setHighlight)
  const clearHighlight = useAriadneStore((s) => s.clearHighlight)

  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    setPending(true)
    clearHighlight()
    try {
      const result = await runQuery(query)
      setAnswer(result.answer)
      setHighlight(result.highlightedNodeIds, result.highlightedEdgeIds)
    } catch {
      setAnswer('Insufficient Topology Data')
    } finally {
      setPending(false)
    }
  }

  if (!open) return null

  return (
    <div className="command-palette-overlay" onClick={() => setOpen(false)}>
      <div className="command-palette" onClick={(e) => e.stopPropagation()}>
        <form onSubmit={handleSubmit}>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about an attack path, e.g. 'is auth-api reachable from the internet?'"
            autoComplete="off"
          />
        </form>
        {pending && <p className="command-palette__status">Tracing the thread…</p>}
        {answer && !pending && <p className="command-palette__answer">{answer}</p>}
      </div>
    </div>
  )
}
