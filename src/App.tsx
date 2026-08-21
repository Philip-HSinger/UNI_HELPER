import { useMemo } from 'react'
import { usePersistentState } from './hooks/usePersistentState'
import { CATALOG, blankSchoolEntry, catalogEntryToSchoolEntry, newId } from './lib/defaults'
import { computeSchoolScores } from './lib/scoring'
import type { EnrichedEntry, OwnScores, SchoolEntry } from './types'
import { ScoreInputPanel } from './components/ScoreInputPanel'
import { EssayBankManager } from './components/EssayBankManager'
import { SummaryBar } from './components/SummaryBar'
import { AddSchoolPanel } from './components/AddSchoolPanel'
import { SchoolTable } from './components/SchoolTable'

function App() {
  const [state, setState] = usePersistentState()

  const enrichedEntries: EnrichedEntry[] = useMemo(() => {
    const bankIds = state.essayBanks.map((b) => b.id)
    return state.entries.map((entry) => {
      const similarities = bankIds.map((id) => entry.similarities[id] ?? 0)
      const computed = computeSchoolScores(entry, state.ownScores, similarities)
      return { ...entry, ...computed }
    })
  }, [state.entries, state.essayBanks, state.ownScores])

  function setOwnScores(scores: OwnScores) {
    setState((s) => ({ ...s, ownScores: scores }))
  }

  function addBank(name: string) {
    setState((s) => ({ ...s, essayBanks: [...s.essayBanks, { id: newId(), name }] }))
  }

  function renameBank(id: string, name: string) {
    setState((s) => ({ ...s, essayBanks: s.essayBanks.map((b) => (b.id === id ? { ...b, name } : b)) }))
  }

  function removeBank(id: string) {
    setState((s) => ({
      ...s,
      essayBanks: s.essayBanks.filter((b) => b.id !== id),
      entries: s.entries.map((e) => {
        const { [id]: _removed, ...rest } = e.similarities
        return { ...e, similarities: rest }
      }),
    }))
  }

  function addFromCatalog(catalogId: string) {
    const catalogEntry = CATALOG.find((c) => c.id === catalogId)
    if (!catalogEntry) return
    setState((s) => ({ ...s, entries: [...s.entries, catalogEntryToSchoolEntry(catalogEntry)] }))
  }

  function addBlank() {
    setState((s) => ({ ...s, entries: [...s.entries, blankSchoolEntry()] }))
  }

  function updateEntry(id: string, partial: Partial<SchoolEntry>) {
    setState((s) => ({ ...s, entries: s.entries.map((e) => (e.id === id ? { ...e, ...partial } : e)) }))
  }

  function setSimilarity(id: string, bankId: string, value: number) {
    setState((s) => ({
      ...s,
      entries: s.entries.map((e) =>
        e.id === id ? { ...e, similarities: { ...e.similarities, [bankId]: value } } : e,
      ),
    }))
  }

  function removeEntry(id: string) {
    setState((s) => ({ ...s, entries: s.entries.filter((e) => e.id !== id) }))
  }

  const excludeCatalogIds = new Set(
    state.entries.map((e) => e.fromCatalogId).filter((id): id is string => id !== null),
  )

  return (
    <div className="min-h-screen bg-slate-50 pb-16 dark:bg-slate-950">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto max-w-6xl px-4 py-6">
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Application Efficiency Guide</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Enter your scores, see where you stand at each school, and find out which supplements
            give you the best score for the writing effort they demand — all saved locally in
            your browser.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <ScoreInputPanel scores={state.ownScores} onChange={setOwnScores} />
          <EssayBankManager
            banks={state.essayBanks}
            onAdd={addBank}
            onRename={renameBank}
            onRemove={removeBank}
          />
        </div>

        <SummaryBar entries={enrichedEntries} />

        <AddSchoolPanel excludeCatalogIds={excludeCatalogIds} onAddFromCatalog={addFromCatalog} onAddBlank={addBlank} />

        <SchoolTable
          entries={enrichedEntries}
          banks={state.essayBanks}
          onUpdate={updateEntry}
          onSetSimilarity={setSimilarity}
          onRemove={removeEntry}
        />

        <p className="text-center text-xs text-slate-400">
          Your data stays in this browser only — nothing is sent to a server. Clearing your
          browser data will clear your list too.
        </p>
      </main>
    </div>
  )
}

export default App
