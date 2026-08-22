// Core data model for the app. `SchoolEntry` is what actually lives in a user's list
// (persisted to localStorage) — it starts as a copy of a `SchoolCatalogEntry` fetched from
// Supabase (see lib/catalog.ts), or a blank custom school, and is fully editable from there.

export type Importance = 'Very Important' | 'Important' | 'Considered' | 'Not Considered'

/** One supplemental prompt. `id` is a stable key referenced by rows in the prompt_similarity
 * table (see lib/similarity.ts) so reuse can be estimated against your committed schools'
 * prompts (see estimateSchoolReuse in lib/scoring.ts). */
export interface Prompt {
  id: string
  text: string
  wordLimit: number | null
}

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

/** The read-only reference data fetched from Supabase (see lib/catalog.ts) — the "database". */
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
  prompts: Prompt[]
  acceptanceRate: number | null
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
  prompts: Prompt[]
  acceptanceRate: number | null
  /** You're 100% going here regardless of outcome — its prompts seed the reuse estimate for
   * every other school on the list (see estimateSchoolReuse in lib/scoring.ts). */
  committed: boolean
  status: ApplicationStatus
  fromCatalogId: string | null
}

export interface OwnScores {
  english: number
  math: number
}

export interface AppState {
  ownScores: OwnScores
  entries: SchoolEntry[]
}

// A school entry with its live computed scores merged in — what the table/summary actually render.
export type EnrichedEntry = SchoolEntry & import('./lib/scoring').ComputedSchoolScores
