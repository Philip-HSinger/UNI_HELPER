import { useEffect, useRef, useState, type Dispatch, type SetStateAction } from 'react'
import type { AppState } from '../types'
import { loadState, saveState } from '../lib/storage'

/**
 * Loads AppState from localStorage on mount, or falls back to `defaultState` (which should be
 * catalog-independent — the catalog loads asynchronously from Supabase, so it can't be baked into
 * a starter list synchronously at mount time; see AppContext for the one-time starter-school
 * seeding that runs once the catalog is ready). Persists every change back to localStorage.
 *
 * The third return value, `wasFreshOnLoad`, is true only if there was genuinely no saved state at
 * mount — as opposed to a returning visitor who happens to have an empty entries list — so callers
 * can tell "seed starter schools" apart from "respect that they cleared their list."
 */
export function usePersistentState(
  defaultState: AppState,
): [AppState, Dispatch<SetStateAction<AppState>>, boolean] {
  const initialRef = useRef<{ state: AppState; wasFresh: boolean } | null>(null)
  if (initialRef.current === null) {
    const loaded = loadState()
    initialRef.current = { state: loaded ?? defaultState, wasFresh: loaded === null }
  }

  const [state, setState] = useState<AppState>(initialRef.current.state)
  const isFirstRender = useRef(true)

  useEffect(() => {
    // Avoid an unnecessary write-back of the exact data we just loaded on mount.
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    saveState(state)
  }, [state])

  return [state, setState, initialRef.current.wasFresh]
}
