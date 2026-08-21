// Core data model for the app. `SchoolEntry` is what actually lives in a user's list
// (persisted to localStorage) — it starts as a copy of a `SchoolCatalogEntry` from
// src/data/schools.json, or a blank custom school, and is fully editable from there.

export type Importance = 'Very Important' | 'Important' | 'Considered' | 'Not Considered'

export type ApplicationStatus =
  | 'not_started'
  | 'applying'
  | 'submitted'
  | 'accepted'
  | 'rejected'
  | 'waitlisted'

export const APPLICATION_STATUSES: { value: ApplicationStatus; label: string }[] = [
  { value: 'not_started', label: 'Not started' },
  { value: 'applying', label: 'Applying' },
  { value: 'submitted', label: 'Submitted' },
  { value: 'accepted', label: 'Accepted' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'waitlisted', label: 'Waitlisted' },
]

/** The read-only reference data shipped in src/data/schools.json (the "database"). */
export interface SchoolCatalogEntry {
  id: string
  name: string
  platform: string
  testOptional: boolean
  englishP25: number
  englishP50: number
  englishP75: number
  mathP25: number
  mathP50: number
  mathP75: number
  difficulty: number
  importance: Importance
  prompts: string[]
  acceptanceRate: number | null
}

/** An essay/story bank the user has already written and wants to reuse across schools. */
export interface EssayBank {
  id: string
  name: string
}

/** A school in the user's own working list — fully editable, independent of the catalog. */
export interface SchoolEntry {
  id: string
  name: string
  platform: string
  testOptional: boolean
  englishP25: number
  englishP50: number
  englishP75: number
  mathP25: number
  mathP50: number
  mathP75: number
  difficulty: number
  importance: Importance
  prompts: string[]
  acceptanceRate: number | null
  /** bankId -> 0-100 "how much of this school's essays can this bank cover" */
  similarities: Record<string, number>
  status: ApplicationStatus
  fromCatalogId: string | null
}

export interface OwnScores {
  english: number
  math: number
}

export interface AppState {
  ownScores: OwnScores
  essayBanks: EssayBank[]
  entries: SchoolEntry[]
}

// A school entry with its live computed scores merged in — what the table/summary actually render.
export type EnrichedEntry = SchoolEntry & import('./lib/scoring').ComputedSchoolScores
