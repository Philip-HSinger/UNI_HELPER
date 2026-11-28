import { describe, expect, it } from 'vitest'
import { shapeSimilarityRows } from './similarity'
import { lookupSimilarity } from './scoring'

describe('shapeSimilarityRows', () => {
  it('builds a matrix queryable in either direction', () => {
    const matrix = shapeSimilarityRows([{ prompt_a_id: 'mit-1', prompt_b_id: 'princeton-1', score: 75 }])
    expect(lookupSimilarity(matrix, 'mit-1', 'princeton-1')).toBe(75)
    expect(lookupSimilarity(matrix, 'princeton-1', 'mit-1')).toBe(75)
  })

  it('handles multiple rows independently', () => {
    const matrix = shapeSimilarityRows([
      { prompt_a_id: 'a', prompt_b_id: 'b', score: 10 },
      { prompt_a_id: 'a', prompt_b_id: 'c', score: 90 },
    ])
    expect(lookupSimilarity(matrix, 'a', 'b')).toBe(10)
    expect(lookupSimilarity(matrix, 'a', 'c')).toBe(90)
    expect(lookupSimilarity(matrix, 'b', 'c')).toBe(0)
  })
})
