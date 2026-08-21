// Pure scoring functions ported from the original guide.xlsx "APPLICATION GUIDE" sheet.
// Every function here is deterministic and side-effect free so it can be unit tested directly
// against the workbook's own computed values (see scoring.test.ts).
import type { Importance } from '../types'

export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value))
}

function round1(value: number): number {
  return Math.round(value * 10) / 10
}

// Abramowitz & Stegun 7.1.26 approximation of the error function (max error ~1.5e-7).
// Excel's NORM.DIST has no native JS equivalent, so this is what lets us reproduce it.
function erf(x: number): number {
  const sign = x < 0 ? -1 : 1
  const ax = Math.abs(x)
  const a1 = 0.254829592
  const a2 = -0.284496736
  const a3 = 1.421413741
  const a4 = -1.453152027
  const a5 = 1.061405429
  const p = 0.3275911

  const t = 1 / (1 + p * ax)
  const y = 1 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-ax * ax)
  return sign * y
}

/** Cumulative distribution function of a normal(mean, sd) at x — mirrors Excel's NORM.DIST(x, mean, sd, TRUE). */
export function normCdf(x: number, mean: number, sd: number): number {
  if (sd <= 0) return x >= mean ? 1 : 0
  return 0.5 * (1 + erf((x - mean) / (sd * Math.SQRT2)))
}

/**
 * Estimate what percentile a test score falls at for a given school, from its published
 * 25th/50th/75th percentile band. The band is treated as samples of a normal distribution
 * (sd derived from the interquartile range via the standard 1.348 constant), same as the sheet's
 * `NORM.DIST($AB$3, C2, (D2-B2)/1.348, TRUE)` formula. Clamped to [1, 99] since no real
 * distribution is truly 0 or 100.
 */
export function percentile(userScore: number, p25: number, p50: number, p75: number): number {
  const sd = (p75 - p25) / 1.348
  if (sd <= 0) return userScore >= p50 ? 99 : 1
  return round1(clamp(normCdf(userScore, p50, sd) * 100, 1, 99))
}

export function average(a: number, b: number): number {
  return round1((a + b) / 2)
}

function importanceModifier(importance: Importance): number {
  switch (importance) {
    case 'Very Important':
      return 1.2
    case 'Important':
      return 1
    case 'Considered':
      return 0.8
    default:
      return 1
  }
}

/**
 * Pulls the raw average score toward the extremes when a school weighs standardized testing
 * heavily, and pulls it toward 50 (neutral) when it barely matters — same shape as the sheet's
 * `50 + (S-50) * modifier` formula, clamped to a valid 0-100 range.
 */
export function weightedAverage(avg: number, importance: Importance): number {
  return round1(clamp(50 + (avg - 50) * importanceModifier(importance), 0, 100))
}

/**
 * How much genuine new writing a school's supplement will cost, after discounting for
 * material the applicant can reuse from essay banks they've already written. `similarities`
 * are 0-100 reuse percentages against each bank; effort is floored at 1 so a "fully reused"
 * school (100% similarity) still produces a large-but-finite efficiency score instead of Infinity.
 */
export function essayEffort(difficulty: number, similarities: number[]): number {
  const avgSimilarity = similarities.length === 0 ? 0 : similarities.reduce((s, v) => s + v, 0) / similarities.length
  const effort = difficulty * (1 - avgSimilarity / 100)
  return Math.max(1, effort)
}

/** Score achievable per unit of essay effort — the "best bang for your writing time" ranking metric. */
export function efficiencyScore(weightedAvg: number, effort: number): number {
  return round1((weightedAvg / effort) * 100)
}

export type TestRecommendation = 'Submit' | "Don't Submit" | 'Helps' | 'Hurts'

/**
 * Faithful port of the sheet's `IF(testOptional, IF(mathPct>50,"Submit","Don't Submit"),
 * IF(AVERAGE(englishPct,mathPct)>50,"Helps","Hurts"))`. Note it deliberately keys the
 * test-optional branch off the math percentile alone (not the combined average) — that's what
 * the original workbook did, presumably because the author leaned on their math score as the
 * deciding factor. Kept as-is for fidelity; a future version could make this configurable.
 */
export function testRecommendation(
  testOptional: boolean,
  mathPct: number,
  englishPct: number,
): TestRecommendation {
  if (testOptional) {
    return mathPct > 50 ? 'Submit' : "Don't Submit"
  }
  return average(englishPct, mathPct) > 50 ? 'Helps' : 'Hurts'
}

export type Classification = 'Reach' | 'Match' | 'Safety'

// Editable thresholds for the Reach/Match/Safety heuristic.
export const CLASSIFICATION_THRESHOLDS = {
  /** Below this acceptance rate, treat as a Reach regardless of fit score (elite-school floor). */
  reachAcceptanceRate: 0.15,
  /** Weighted-average score at/above which a school counts as a Safety. */
  safetyScore: 70,
  /** Weighted-average score at/above which a school counts as a Match (below = Reach). */
  matchScore: 45,
}

/** Combines the student's fit score with the school's acceptance rate (when known) into a simple Reach/Match/Safety label. */
export function classify(weightedAvg: number, acceptanceRate: number | null): Classification {
  if (acceptanceRate !== null && acceptanceRate < CLASSIFICATION_THRESHOLDS.reachAcceptanceRate) {
    return 'Reach'
  }
  if (weightedAvg >= CLASSIFICATION_THRESHOLDS.safetyScore) return 'Safety'
  if (weightedAvg >= CLASSIFICATION_THRESHOLDS.matchScore) return 'Match'
  return 'Reach'
}

export interface ComputedSchoolScores {
  englishPercentile: number
  mathPercentile: number
  average: number
  weightedAverage: number
  essayEffort: number
  efficiencyScore: number
  testRecommendation: TestRecommendation
  classification: Classification
}

/** Runs every formula above for one school entry, given the user's own test scores. */
export function computeSchoolScores(
  school: {
    englishP25: number
    englishP50: number
    englishP75: number
    mathP25: number
    mathP50: number
    mathP75: number
    difficulty: number
    importance: Importance
    testOptional: boolean
    acceptanceRate: number | null
  },
  ownScores: { english: number; math: number },
  bankSimilarities: number[],
): ComputedSchoolScores {
  const englishPercentile = percentile(ownScores.english, school.englishP25, school.englishP50, school.englishP75)
  const mathPercentile = percentile(ownScores.math, school.mathP25, school.mathP50, school.mathP75)
  const avg = average(englishPercentile, mathPercentile)
  const wAvg = weightedAverage(avg, school.importance)
  const effort = essayEffort(school.difficulty, bankSimilarities)
  const efficiency = efficiencyScore(wAvg, effort)
  const recommendation = testRecommendation(school.testOptional, mathPercentile, englishPercentile)
  const classification = classify(wAvg, school.acceptanceRate)

  return {
    englishPercentile,
    mathPercentile,
    average: avg,
    weightedAverage: wAvg,
    essayEffort: round1(effort),
    efficiencyScore: efficiency,
    testRecommendation: recommendation,
    classification,
  }
}
