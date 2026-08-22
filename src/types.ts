// Core data model for the app. `SchoolEntry` is what actually lives in a user's list
// (persisted to localStorage) — it starts as a copy of a `SchoolCatalogEntry` fetched from
// Supabase (see lib/catalog.ts). All catalog-sourced fields (percentiles, importance, acceptance
// rate, difficulty, prompts) are read-only in the app by design — they're admin-curated data,
// edited only in Supabase (see supabase/schema.sql and src/data/README.md).

export type Importance = 'Very Important' | 'Important' | 'Considered' | 'Not Considered'

/** One supplemental prompt. `id` is a stable key referenced by rows in the prompt_similarity
 * table (see lib/similarity.ts) so reuse can be estimated against the schools you're applying to
 * (see estimateSchoolReuse in lib/scoring.ts). */
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

/** A school on the user's own list. Deliberately holds only what's actually yours to set — every
 * catalog-sourced field (name, percentiles, prompts, etc.) is looked up live from `catalog` by
 * `fromCatalogId` each render (see AppContext's `enrichedEntries`), never copied/frozen at add
 * time. That way an admin edit in Supabase (a typo fix, a new percentile band, a reworded prompt)
 * shows up immediately for schools already on someone's list, not just newly-added ones. */
export interface SchoolEntry {
  id: string
  status: ApplicationStatus
  fromCatalogId: string
}

export interface OwnScores {
  english: number
  math: number
}

export interface AppState {
  ownScores: OwnScores
  entries: SchoolEntry[]
}

/** Per-prompt reuse detail, one per entry in `SchoolCatalogEntry.prompts` (same order), so the
 * Difficulty page can show *why* a specific essay question has reuse credit, not just the
 * school-wide average — see AppContext's `enrichedEntries` for how this gets built. */
export interface PromptReuseInfo {
  promptId: string
  percent: number
  matchedWith: { schoolName: string; promptText: string } | null
}

// What the table/summary actually render: the live catalog fields for `fromCatalogId` (never a
// stale copy), the user's own `status`, and the computed scores derived from both.
export type EnrichedEntry = SchoolCatalogEntry &
  Pick<SchoolEntry, 'status' | 'fromCatalogId'> &
  import('./lib/scoring').ComputedSchoolScores & { promptReuse: PromptReuseInfo[] }
