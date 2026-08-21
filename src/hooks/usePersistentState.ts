import { useEffect, useRef, useState } from 'react'
import type { AppState } from '../types'
import { loadState, saveState } from '../lib/storage'
import { createInitialState } from '../lib/defaults'

/** Loads AppState from localStorage on mount (or seeds a fresh default), and persists every change. */
export function usePersistentState(): [AppState, React.Dispatch<React.SetStateAction<AppState>>] {
  const [state, setState] = useState<AppState>(() => loadState() ?? createInitialState())
  const isFirstRender = useRef(true)

  useEffect(() => {
    // Avoid an unnecessary write-back of the exact data we just loaded on mount.
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    saveState(state)
  }, [state])

  return [state, setState]
}
