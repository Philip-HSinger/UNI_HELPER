import { describe, expect, it } from 'vitest'
import {
  average,
  classify,
  compositeBand,
  computeSchoolScores,
  efficiencyScore,
  essayEffort,
  estimatePromptReuse,
  estimateSchoolReuse,
  lookupSimilarity,
  pairKey,
  percentile,
  testRecommendation,
  weightedAverage,
  type SimilarityMatrix,
} from './scoring'

// Fixtures below are read directly from the original guide.xlsx "APPLICATION GUIDE" sheet,
// computed with the user's own SAT English 730 / Math 800, to confirm this port reproduces
// the workbook's actual numbers (not just formulas that look plausible).
const OWN_SCORES = { english: 730, math: 800 }

describe('percentile', () => {
  it('matches the workbook for Purdue (English)', () => {
    expect(percentile(OWN_SCORES.english, 600, 660, 720)).toBeCloseTo(78.4, 1)
  })
  it('matches the workbook for Purdue (Math)', () => {
    expect(percentile(OWN_SCORES.math, 600, 690, 760)).toBeCloseTo(82.3, 1)
  })
  it('matches the workbook for Georgia Tech (English)', () => {
    expect(percentile(OWN_SCORES.english, 680, 720, 750)).toBeCloseTo(57.6, 1)
  })
  it('matches the workbook for Georgia Tech (Math)', () => {
    expect(percentile(OWN_SCORES.math, 690, 760, 790)).toBeCloseTo(70.5, 1)
  })
  it('matches the workbook for Tufts (English)', () => {
    expect(percentile(OWN_SCORES.english, 720, 740, 770)).toBeCloseTo(39.4, 1)
  })
  it('matches the workbook for Tufts (Math)', () => {
    expect(percentile(OWN_SCORES.math, 750, 770, 790)).toBeCloseTo(84.4, 1)
  })
  it('clamps to [1, 99]', () => {
    expect(percentile(200, 700, 750, 780)).toBe(1)
    expect(percentile(1600, 700, 750, 780)).toBe(99)
  })
})

describe('average', () => {
  it('matches the workbook for Purdue', () => {
    expect(average(78.4, 82.3)).toBeCloseTo(80.4, 1)
  })
})

describe('weightedAverage', () => {
  it('leaves the average untouched when importance is "Important" (modifier 1x)', () => {
    expect(weightedAverage(80.4, 'Important')).toBeCloseTo(80.4, 1)
  })
  it('pulls toward the extreme for "Very Important" (1.2x)', () => {
    // workbook Northeastern-style case: avg 68 -> weighted 71.6
    expect(weightedAverage(68, 'Very Important')).toBeCloseTo(71.6, 1)
  })
  it('dampens toward 50 for "Considered" (0.8x) — matches Georgia Tech', () => {
    expect(weightedAverage(64.1, 'Considered')).toBeCloseTo(61.3, 1)
  })
  it('matches the workbook for Tufts', () => {
    expect(weightedAverage(61.9, 'Considered')).toBeCloseTo(59.5, 1)
  })
  it('pins the weighted average at exactly 50 for "Not Considered", regardless of the raw average', () => {
    expect(weightedAverage(95, 'Not Considered')).toBe(50)
    expect(weightedAverage(5, 'Not Considered')).toBe(50)
  })
})

describe('essayEffort', () => {
  it('matches the workbook for Purdue (difficulty 30, 50% reuse)', () => {
    expect(essayEffort(30, 50)).toBeCloseTo(15, 1)
  })
  it('matches the workbook for Georgia Tech (difficulty 25, 50% reuse)', () => {
    expect(essayEffort(25, 50)).toBeCloseTo(12.5, 1)
  })
  it('matches the workbook for Tufts (difficulty 20, 35% reuse)', () => {
    expect(essayEffort(20, 35)).toBeCloseTo(13, 1)
  })
  it('floors at 1 instead of hitting zero for a fully-reused school', () => {
    expect(essayEffort(50, 100)).toBe(1)
  })
  it('treats zero reuse as the full difficulty', () => {
    expect(essayEffort(40, 0)).toBe(40)
  })
})

describe('pairKey / lookupSimilarity', () => {
  it('is order-independent', () => {
    const matrix: SimilarityMatrix = new Map([[pairKey('a', 'b'), 75]])
    expect(lookupSimilarity(matrix, 'a', 'b')).toBe(75)
    expect(lookupSimilarity(matrix, 'b', 'a')).toBe(75)
  })
  it('is 0 for an unscored pair', () => {
    expect(lookupSimilarity(new Map(), 'a', 'b')).toBe(0)
  })
  it('is 0 comparing a prompt to itself', () => {
    expect(lookupSimilarity(new Map(), 'a', 'a')).toBe(0)
  })
})

describe('estimatePromptReuse', () => {
  it('is 0 with no prompts from schools being applied to', () => {
    expect(estimatePromptReuse('mit-1', [], new Map())).toBe(0)
  })
  it('is 0 when no pair involving this prompt has been scored', () => {
    expect(estimatePromptReuse('mit-1', ['princeton-1'], new Map())).toBe(0)
  })
  it('takes the best match across the schools the applicant is applying to', () => {
    const matrix: SimilarityMatrix = new Map([
      [pairKey('mit-1', 'princeton-1'), 40],
      [pairKey('mit-1', 'stanford-1'), 75],
    ])
    expect(estimatePromptReuse('mit-1', ['princeton-1', 'stanford-1'], matrix)).toBe(75)
  })
  it('a strong-but-partial match reduces reuse, never to 100 unless actually scored that high', () => {
    const matrix: SimilarityMatrix = new Map([[pairKey('mit-intellectual-curiosity', 'princeton-what-excites-you'), 75]])
    expect(estimatePromptReuse('mit-intellectual-curiosity', ['princeton-what-excites-you'], matrix)).toBe(75)
  })
})

describe('estimateSchoolReuse', () => {
  it("averages reuse across all of a school's prompts (unscored ones count as 0)", () => {
    const matrix: SimilarityMatrix = new Map([[pairKey('p1', 'c1'), 80]])
    expect(estimateSchoolReuse(['p1', 'p2'], ['c1'], matrix)).toBeCloseTo(40, 1)
  })
  it('is 0 for a school with no prompts', () => {
    expect(estimateSchoolReuse([], ['c1'], new Map())).toBe(0)
  })
  it('a partial match reduces essay effort but never all the way to zero ("not zero less")', () => {
    const matrix: SimilarityMatrix = new Map([[pairKey('p1', 'c1'), 75]])
    const reuse = estimateSchoolReuse(['p1'], ['c1'], matrix)
    expect(essayEffort(50, reuse)).toBeCloseTo(12.5, 1)
    expect(essayEffort(50, reuse)).toBeGreaterThan(0)
  })
})

describe('compositeBand', () => {
  it('sums the English and Math bands per percentile (an approximation, not a real published composite)', () => {
    const band = compositeBand({
      englishP25: 600,
      englishP50: 660,
      englishP75: 720,
      mathP25: 600,
      mathP50: 690,
      mathP75: 760,
    })
    expect(band).toEqual({ p25: 1200, p50: 1350, p75: 1480 })
  })
})

describe('efficiencyScore', () => {
  it('matches the workbook for Georgia Tech (weighted avg 61.3, effort 12.5)', () => {
    expect(efficiencyScore(61.3, 12.5)).toBeCloseTo(490.4, 1)
  })
  it('matches the workbook for Tufts (weighted avg 59.5, effort 13)', () => {
    expect(efficiencyScore(59.5, 13)).toBeCloseTo(457.7, 1)
  })
})

describe('testRecommendation', () => {
  it('keys the test-optional branch off the math percentile — matches Tufts (Submit)', () => {
    expect(testRecommendation(true, 84.4, 39.4)).toBe('Submit')
  })
  it("recommends against submitting when test-optional and math percentile is under 50", () => {
    expect(testRecommendation(true, 45, 90)).toBe("Don't Submit")
  })
  it('uses the combined average when testing is required — matches Purdue (Helps)', () => {
    expect(testRecommendation(false, 82.3, 78.4)).toBe('Helps')
  })
  it('reports Hurts when required and the combined average is under 50', () => {
    expect(testRecommendation(false, 30, 40)).toBe('Hurts')
  })
})

describe('classify', () => {
  it('treats sub-15% acceptance-rate schools as a Reach regardless of fit score', () => {
    expect(classify(95, 0.05)).toBe('Reach')
  })
  it('calls a high weighted average with an unknown acceptance rate a Safety', () => {
    expect(classify(80, null)).toBe('Safety')
  })
  it('calls a mid-range weighted average a Match', () => {
    expect(classify(55, null)).toBe('Match')
  })
  it('calls a low weighted average a Reach', () => {
    expect(classify(30, null)).toBe('Reach')
  })
})

describe('computeSchoolScores (end-to-end)', () => {
  it('reproduces the full Georgia Tech row from the workbook', () => {
    const result = computeSchoolScores(
      {
        englishP25: 680,
        englishP50: 720,
        englishP75: 750,
        mathP25: 690,
        mathP50: 760,
        mathP75: 790,
        difficulty: 25,
        importance: 'Considered',
        testOptional: false,
        acceptanceRate: null,
      },
      OWN_SCORES,
      50, // reuse percent, matching the workbook's avg(10, 90) similarity for this row
    )

    expect(result.englishPercentile).toBeCloseTo(57.6, 1)
    expect(result.mathPercentile).toBeCloseTo(70.5, 1)
    expect(result.average).toBeCloseTo(64.1, 1)
    expect(result.weightedAverage).toBeCloseTo(61.3, 1)
    expect(result.estimatedReuse).toBe(50)
    expect(result.essayEffort).toBeCloseTo(12.5, 1)
    expect(result.efficiencyScore).toBeCloseTo(490.4, 1)
    expect(result.testRecommendation).toBe('Helps')
    expect(result.classification).toBe('Match')
  })
})
