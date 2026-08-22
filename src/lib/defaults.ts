import type { AppState, SchoolCatalogEntry, SchoolEntry } from '../types'

export function catalogEntryToSchoolEntry(catalog: SchoolCatalogEntry): SchoolEntry {
  return {
    ...catalog,
    status: 'not_started',
    fromCatalogId: catalog.id,
  }
}

// A handful of well-known reach/match/safety-spanning schools to pre-populate a first-time
// visitor's list, so the table isn't empty on first load. Fully removable.
const STARTER_SCHOOL_IDS = ['stanford', 'cornell', 'boston-university', 'purdue']

/** `catalog` must already be loaded (see useReferenceData) — this only runs once that's ready. */
export function createInitialState(catalog: SchoolCatalogEntry[]): AppState {
  return {
    ownScores: { english: 700, math: 700 },
    entries: catalog.filter((s) => STARTER_SCHOOL_IDS.includes(s.id)).map(catalogEntryToSchoolEntry),
  }
}
