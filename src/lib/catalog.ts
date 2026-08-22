import { supabase } from './supabaseClient'
import type { Importance, Prompt, SchoolCatalogEntry } from '../types'

// Shapes matching the Postgres column names in supabase/schema.sql (snake_case) — kept private to
// this module; everything else in the app only ever sees the camelCase SchoolCatalogEntry shape.
interface RawPromptRow {
  id: string
  text: string
  word_limit: number | null
}

interface RawSchoolRow {
  id: string
  name: string
  platform: string
  test_optional: boolean
  english_p25: number
  english_p50: number
  english_p75: number
  math_p25: number
  math_p50: number
  math_p75: number
  difficulty: number
  importance: string
  acceptance_rate: number | null
  us_news_rank: number | null
  prompts: RawPromptRow[] | null
}

/** Pure shaping function, unit tested against hand-built fixtures — no network involved. */
export function shapeCatalogRows(rows: RawSchoolRow[]): SchoolCatalogEntry[] {
  return rows.map((row) => {
    const prompts: Prompt[] = (row.prompts ?? []).map((p) => ({
      id: p.id,
      text: p.text,
      wordLimit: p.word_limit,
    }))

    return {
      id: row.id,
      name: row.name,
      platform: row.platform,
      testOptional: row.test_optional,
      englishP25: row.english_p25,
      englishP50: row.english_p50,
      englishP75: row.english_p75,
      mathP25: row.math_p25,
      mathP50: row.math_p50,
      mathP75: row.math_p75,
      difficulty: row.difficulty,
      importance: row.importance as Importance,
      acceptanceRate: row.acceptance_rate,
      usNewsRank: row.us_news_rank,
      prompts,
    }
  })
}

/** Fetches the whole school catalog (schools + their prompts) in one round trip. */
export async function fetchCatalog(): Promise<SchoolCatalogEntry[]> {
  const { data, error } = await supabase
    .from('schools')
    .select('*, prompts(*)')
    .order('sort_order', { foreignTable: 'prompts' })

  if (error) throw error
  return shapeCatalogRows((data ?? []) as unknown as RawSchoolRow[])
}
