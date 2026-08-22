import schoolCatalog from '../data/schools.json'
import type { AppState, SchoolCatalogEntry, SchoolEntry } from '../types'

export const CATALOG: SchoolCatalogEntry[] = schoolCatalog as SchoolCatalogEntry[]

export function newId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID()
  return `id-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export function catalogEntryToSchoolEntry(catalog: SchoolCatalogEntry): SchoolEntry {
  return {
    ...catalog,
    committed: false,
    status: 'not_started',
    fromCatalogId: catalog.id,
  }
}

export function blankSchoolEntry(): SchoolEntry {
  return {
    id: newId(),
    name: 'New school',
    platform: 'Common app',
    testOptional: false,
    englishP25: 650,
    englishP50: 700,
    englishP75: 750,
    mathP25: 650,
    mathP50: 700,
    mathP75: 750,
    difficulty: 50,
    importance: 'Considered',
    prompts: [],
    acceptanceRate: null,
    committed: false,
    status: 'not_started',
    fromCatalogId: null,
  }
}

// A handful of well-known reach/match/safety-spanning schools to pre-populate a first-time
// visitor's list, so the table isn't empty on first load. Fully removable/editable.
const STARTER_SCHOOL_IDS = ['stanford', 'cornell', 'boston-university', 'purdue']

export function createInitialState(): AppState {
  return {
    ownScores: { english: 700, math: 700 },
    entries: CATALOG.filter((s) => STARTER_SCHOOL_IDS.includes(s.id)).map(catalogEntryToSchoolEntry),
  }
}
