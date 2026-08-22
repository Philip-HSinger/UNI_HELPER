import { createContext, useContext, useEffect, useMemo, useRef, type ReactNode } from 'react'
import { usePersistentState } from '../hooks/usePersistentState'
import { useReferenceData } from '../hooks/useReferenceData'
import { catalogEntryToSchoolEntry, createInitialState } from '../lib/defaults'
import { computeSchoolScores, estimateSchoolReuse } from '../lib/scoring'
import type { ApplicationStatus, EnrichedEntry, OwnScores, SchoolCatalogEntry } from '../types'

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
  setStatus: (id: string, status: ApplicationStatus) => void
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
    // Schools with any status past "not started" are treated as essays you're actually writing —
    // that's what every other school's reuse gets estimated against (see estimateSchoolReuse).
    const applyingPromptIds = state.entries
      .filter((e) => e.status !== 'not_started')
      .flatMap((e) => e.prompts.map((p) => p.id))
    return state.entries.map((entry) => {
      const promptIds = entry.prompts.map((p) => p.id)
      const reusePercent = estimateSchoolReuse(promptIds, applyingPromptIds, matrix)
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

  function setStatus(id: string, status: ApplicationStatus) {
    setState((s) => ({ ...s, entries: s.entries.map((e) => (e.id === id ? { ...e, status } : e)) }))
  }

  function removeEntry(id: string) {
    setState((s) => ({ ...s, entries: s.entries.filter((e) => e.id !== id) }))
  }

  const excludeCatalogIds = new Set(state.entries.map((e) => e.fromCatalogId))

  const value: AppContextValue = {
    catalog,
    referenceLoading,
    referenceError,
    ownScores: state.ownScores,
    setOwnScores,
    entries: enrichedEntries,
    excludeCatalogIds,
    addFromCatalog,
    setStatus,
    removeEntry,
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useAppContext(): AppContextValue {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useAppContext must be used within an AppProvider')
  return ctx
}
