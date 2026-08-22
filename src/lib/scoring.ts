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
    case 'Not Considered':
      // A school that doesn't consider testing at all shouldn't have your score move its
      // weighted average off 50 in either direction - modifier 0, not 1 (that was a bug: it
      // used to fall through to the same weight as "Important").
      return 0
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
 * How much genuine new writing a school's supplement will cost, after discounting for the
 * estimated reuse (0-100, from estimateSchoolReuse below) against essays for schools you're
 * already applying to. Effort is floored at 1 so a "fully reused" school still produces a
 * large-but-finite efficiency score instead of Infinity.
 */
export function essayEffort(difficulty: number, reusePercent: number): number {
  const effort = difficulty * (1 - reusePercent / 100)
  return Math.max(1, effort)
}

/**
 * The prompt-to-prompt reuse matrix: a map from an order-independent pair key to a 0-100
 * similarity score, built from the `prompt_similarity` table (see lib/similarity.ts). Only pairs
 * someone has actually scored appear here — an unscored pair simply looks up as 0 (no reuse
 * credit assumed), never an error.
 */
export type SimilarityMatrix = Map<string, number>

/** Order-independent key so a pair scored as (a, b) is found whether looked up as (a, b) or (b, a). */
export function pairKey(promptIdA: string, promptIdB: string): string {
  return promptIdA < promptIdB ? `${promptIdA}|${promptIdB}` : `${promptIdB}|${promptIdA}`
}

/** 0 if the pair hasn't been scored (or is the same prompt compared to itself). */
export function lookupSimilarity(matrix: SimilarityMatrix, promptIdA: string, promptIdB: string): number {
  if (promptIdA === promptIdB) return 0
  return matrix.get(pairKey(promptIdA, promptIdB)) ?? 0
}

/**
 * Estimated 0-100 reuse for one prompt: the best (highest-scoring) match against any prompt from
 * schools you're already applying to. "Best match" rather than an average, since what matters is
 * whether *some* essay you're already writing covers this prompt well, not diluting that by
 * unrelated prompts from the same schools.
 */
export function estimatePromptReuse(promptId: string, applyingPromptIds: string[], matrix: SimilarityMatrix): number {
  if (applyingPromptIds.length === 0) return 0
  let best = 0
  for (const applyingId of applyingPromptIds) {
    const score = lookupSimilarity(matrix, promptId, applyingId)
    if (score > best) best = score
  }
  return round1(best)
}

/** A school's overall estimated reuse: the average across its own prompts. No prompts -> 0 (no credit). */
export function estimateSchoolReuse(promptIds: string[], applyingPromptIds: string[], matrix: SimilarityMatrix): number {
  if (promptIds.length === 0) return 0
  const total = promptIds.reduce((sum, id) => sum + estimatePromptReuse(id, applyingPromptIds, matrix), 0)
  return round1(total / promptIds.length)
}

/**
 * The composite (English + Math) 25th/50th/75th SAT band, for display only. This is an
 * *approximation* — it sums the two section bands rather than reflecting a school's real
 * published composite distribution (which CDS reports separately and tends to be a bit tighter,
 * since section scores correlate) — good enough for a reference figure, not precise enough to
 * feed back into the percentile math, which keeps using the real section-level bands.
 */
export function compositeBand(school: {
  englishP25: number
  englishP50: number
  englishP75: number
  mathP25: number
  mathP50: number
  mathP75: number
}): { p25: number; p50: number; p75: number } {
  return {
    p25: school.englishP25 + school.mathP25,
    p50: school.englishP50 + school.mathP50,
    p75: school.englishP75 + school.mathP75,
  }
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
  estimatedReuse: number
  essayEffort: number
  efficiencyScore: number
  testRecommendation: TestRecommendation
  classification: Classification
}

/** Runs every formula above for one school entry, given the user's own test scores and its
 * already-estimated reuse percent (see estimateSchoolReuse, computed once per render from
 * whichever schools the user's `status` marks as already being applied to). */
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
  reusePercent: number,
): ComputedSchoolScores {
  const englishPercentile = percentile(ownScores.english, school.englishP25, school.englishP50, school.englishP75)
  const mathPercentile = percentile(ownScores.math, school.mathP25, school.mathP50, school.mathP75)
  const avg = average(englishPercentile, mathPercentile)
  const wAvg = weightedAverage(avg, school.importance)
  const effort = essayEffort(school.difficulty, reusePercent)
  const efficiency = efficiencyScore(wAvg, effort)
  const recommendation = testRecommendation(school.testOptional, mathPercentile, englishPercentile)
  const classification = classify(wAvg, school.acceptanceRate)

  return {
    englishPercentile,
    mathPercentile,
    average: avg,
    weightedAverage: wAvg,
    estimatedReuse: reusePercent,
    essayEffort: round1(effort),
    efficiencyScore: efficiency,
    testRecommendation: recommendation,
    classification,
  }
}
