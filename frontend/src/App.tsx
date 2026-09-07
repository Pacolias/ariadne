import { useEffect } from 'react'
import { CommandPalette } from './components/CommandPalette'
import { ImpactPanel } from './components/ImpactPanel'
import { LabyrinthCanvas } from './components/LabyrinthCanvas'
import { fetchTopology } from './lib/api'
import { useAriadneStore } from './store/useAriadneStore'

function App() {
  const setTopology = useAriadneStore((s) => s.setTopology)

  useEffect(() => {
    fetchTopology()
      .then((t) => setTopology(t.nodes, t.edges, t.cti))
      .catch(() => setTopology([], [], null))
  }, [setTopology])

  return (
    <div className="app-shell">
      <LabyrinthCanvas />
      <ImpactPanel />
      <CommandPalette />
      <div className="pointer-events-none fixed bottom-4 left-4 font-mono text-xs text-gray-600">
        Ctrl+K to query or ingest a report
      </div>
    </div>
  )
}

export default App
