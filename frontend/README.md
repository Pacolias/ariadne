# Ariadne — Frontend

The visual interface described in the root [`CLAUDE.md`](../CLAUDE.md#frontend-the-ariadne-interface):
a dark, interactive graph canvas instead of a chat window.

- `src/components/LabyrinthCanvas.tsx` — the main React Flow canvas.
- `src/components/ImpactPanel.tsx` — the context-sensitive sidebar.
- `src/components/CommandPalette.tsx` — the `Ctrl+K` natural-language query modal.
- `src/store/useAriadneStore.ts` — shared canvas/selection state (zustand).
- `src/lib/api.ts` — the backend client; see `backend/src/ariadne/api/routes/` for the matching endpoints.

## Commands

```bash
npm install
cp .env.example .env   # point VITE_API_URL at the backend
npm run dev             # dev server
npm run build            # type-check (tsc -b) + production build
npm run lint             # oxlint
```
