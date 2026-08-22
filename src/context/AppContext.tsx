import { createContext, useContext, useEffect, useMemo, useRef, type ReactNode } from 'react'
import { usePersistentState } from '../hooks/usePersistentState'
import { useReferenceData } from '../hooks/useReferenceData'
import { newId, blankSchoolEntry, catalogEntryToSchoolEntry, createInitialState } from '../lib/defaults'
import { computeSchoolScores, estimateSchoolReuse } from '../lib/scoring'
import type { EnrichedEntry, OwnScores, SchoolCatalogEntry, SchoolEntry } from '../types'

const EMPTY_STATE = { ownScores: { english: 700, math: 700 }, entries: [] }

interface AppContextValue {
  catalog: SchoolCatalogEntry[]
  referenceLoading: boolean
  referenceError: string | null
  ownScores: OwnScores
  setOwnScores: (scores: OwnScores) => void
  entries: EnrichedEntry[]
  excludeCatalogIds: Set<string>
  addFromCatalog: (catalogId: string) => void
  addBlank: () => void
  updateEntry: (id: string, partial: Partial<SchoolEntry>) => void
  toggleCommitted: (id: string) => void
  addPrompt: (id: string, text: string) => void
  updatePromptText: (id: string, index: number, text: string) => void
  updatePromptWordLimit: (id: string, index: number, wordLimit: number | null) => void
  removePrompt: (id: string, index: number) => void
  removeEntry: (id: string) => void
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const { catalog, matrix, loading: referenceLoading, error: referenceError } = useReferenceData()
  const [state, setState, wasFreshOnLoad] = usePersistentState(EMPTY_STATE)
  const seededRef = useRef(false)

  // A genuinely new visitor (no saved localStorage state at all) gets a starter list once the
  // catalog has actually loaded — can't seed synchronously at mount since the catalog is fetched.
  useEffect(() => {
    if (wasFreshOnLoad && !referenceLoading && catalog.length > 0 && !seededRef.current) {
      seededRef.current = true
      setState((s) => ({ ...s, entries: createInitialState(catalog).entries }))
    }
  }, [wasFreshOnLoad, referenceLoading, catalog, setState])

  const enrichedEntries: EnrichedEntry[] = useMemo(() => {
    const committedPromptIds = state.entries.filter((e) => e.committed).flatMap((e) => e.prompts.map((p) => p.id))
    return state.entries.map((entry) => {
      const promptIds = entry.prompts.map((p) => p.id)
      const reusePercent = estimateSchoolReuse(promptIds, committedPromptIds, matrix)
      const computed = computeSchoolScores(entry, state.ownScores, reusePercent)
      return { ...entry, ...computed }
    })
  }, [state.entries, state.ownScores, matrix])

  function setOwnScores(scores: OwnScores) {
    setState((s) => ({ ...s, ownScores: scores }))
  }

  function addFromCatalog(catalogId: string) {
    const catalogEntry = catalog.find((c) => c.id === catalogId)
    if (!catalogEntry) return
    setState((s) => ({ ...s, entries: [...s.entries, catalogEntryToSchoolEntry(catalogEntry)] }))
  }

  function addBlank() {
    setState((s) => ({ ...s, entries: [...s.entries, blankSchoolEntry()] }))
  }

  function updateEntry(id: string, partial: Partial<SchoolEntry>) {
    setState((s) => ({ ...s, entries: s.entries.map((e) => (e.id === id ? { ...e, ...partial } : e)) }))
  }

  function toggleCommitted(id: string) {
    setState((s) => ({
      ...s,
      entries: s.entries.map((e) => (e.id === id ? { ...e, committed: !e.committed } : e)),
    }))
  }

  function addPrompt(id: string, text: string) {
    setState((s) => ({
      ...s,
      entries: s.entries.map((e) =>
        e.id === id ? { ...e, prompts: [...e.prompts, { id: newId(), text, wordLimit: null }] } : e,
      ),
    }))
  }

  function updatePromptText(id: string, index: number, text: string) {
    setState((s) => ({
      ...s,
      entries: s.entries.map((e) =>
        e.id === id ? { ...e, prompts: e.prompts.map((p, i) => (i === index ? { ...p, text } : p)) } : e,
      ),
    }))
  }

  function updatePromptWordLimit(id: string, index: number, wordLimit: number | null) {
    setState((s) => ({
      ...s,
      entries: s.entries.map((e) =>
        e.id === id ? { ...e, prompts: e.prompts.map((p, i) => (i === index ? { ...p, wordLimit } : p)) } : e,
      ),
    }))
  }

  function removePrompt(id: string, index: number) {
    setState((s) => ({
      ...s,
      entries: s.entries.map((e) => (e.id === id ? { ...e, prompts: e.prompts.filter((_, i) => i !== index) } : e)),
    }))
  }

  function removeEntry(id: string) {
    setState((s) => ({ ...s, entries: s.entries.filter((e) => e.id !== id) }))
  }

  const excludeCatalogIds = new Set(
    state.entries.map((e) => e.fromCatalogId).filter((id): id is string => id !== null),
  )

  const value: AppContextValue = {
    catalog,
    referenceLoading,
    referenceError,
    ownScores: state.ownScores,
    setOwnScores,
    entries: enrichedEntries,
    excludeCatalogIds,
    addFromCatalog,
    addBlank,
    updateEntry,
    toggleCommitted,
    addPrompt,
    updatePromptText,
    updatePromptWordLimit,
    removePrompt,
    removeEntry,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useAppContext must be used within an AppProvider')
  return ctx
}
