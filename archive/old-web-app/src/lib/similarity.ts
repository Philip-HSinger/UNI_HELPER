import { supabase } from './supabaseClient'
import { pairKey, type SimilarityMatrix } from './scoring'

interface RawSimilarityRow {
  prompt_a_id: string
  prompt_b_id: string
  score: number
}

/** Pure shaping function, unit tested against hand-built fixtures — no network involved. */
export function shapeSimilarityRows(rows: RawSimilarityRow[]): SimilarityMatrix {
  const matrix: SimilarityMatrix = new Map()
  for (const row of rows) {
    matrix.set(pairKey(row.prompt_a_id, row.prompt_b_id), row.score)
  }
  return matrix
}

/** Fetches every scored pair from prompt_similarity into the pair-key map estimatePromptReuse expects. */
export async function fetchSimilarityMatrix(): Promise<SimilarityMatrix> {
  const { data, error } = await supabase.from('prompt_similarity').select('prompt_a_id, prompt_b_id, score')

  if (error) throw error
  return shapeSimilarityRows((data ?? []) as RawSimilarityRow[])
}
