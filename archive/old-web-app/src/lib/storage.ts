// All user data (own scores, essay banks, the working school list) lives only in the
// browser's localStorage — there is no server in v1. See README.md for the plan to add
// accounts/sync when this moves to a paid tier.
import type { AppState } from '../types'

const STORAGE_KEY = 'uni-helper:state:v1'

export function loadState(): AppState | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw) as AppState
  } catch {
    // Corrupt data, private-browsing mode, or storage disabled — fall back to defaults.
    return null
  }
}

export function saveState(state: AppState): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // Storage full or unavailable — silently no-op rather than crash the app.
  }
}
