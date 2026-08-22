import { describe, expect, it } from 'vitest'
import { shapeCatalogRows } from './catalog'

describe('shapeCatalogRows', () => {
  it('converts snake_case Supabase rows into the camelCase SchoolCatalogEntry shape', () => {
    const [school] = shapeCatalogRows([
      {
        id: 'purdue',
        name: 'Purdue',
        platform: 'Common app',
        test_optional: false,
        english_p25: 600,
        english_p50: 660,
        english_p75: 720,
        math_p25: 600,
        math_p50: 690,
        math_p75: 760,
        difficulty: 30,
        importance: 'Important',
        acceptance_rate: null,
        prompts: [{ id: 'purdue--why-major', text: 'Why this major?', word_limit: 250 }],
      },
    ])

    expect(school.id).toBe('purdue')
    expect(school.englishP25).toBe(600)
    expect(school.mathP75).toBe(760)
    expect(school.importance).toBe('Important')
    expect(school.prompts).toEqual([{ id: 'purdue--why-major', text: 'Why this major?', wordLimit: 250 }])
  })

  it('handles a school with no prompts', () => {
    const [school] = shapeCatalogRows([
      {
        id: 'x',
        name: 'X',
        platform: 'Common app',
        test_optional: true,
        english_p25: 1,
        english_p50: 2,
        english_p75: 3,
        math_p25: 1,
        math_p50: 2,
        math_p75: 3,
        difficulty: 10,
        importance: 'Considered',
        acceptance_rate: 0.5,
        prompts: null,
      },
    ])
    expect(school.prompts).toEqual([])
  })
})
