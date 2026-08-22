// Fixed vocabulary used to tag supplemental essay prompts. Reuse is estimated by overlap
// between a candidate school's prompt themes and the themes covered by prompts you've already
// committed to writing (see estimateSchoolReuse in scoring.ts) — this is what stands in for a
// literal prompt-by-prompt similarity matrix, but generalizes to any school/prompt without
// needing every pair hand-scored.
export type Theme =
  | 'why_major'
  | 'why_school'
  | 'community_identity'
  | 'intellectual_curiosity'
  | 'extracurricular_activity'
  | 'challenge_adversity'
  | 'values_joy'
  | 'future_contribution'
  | 'creative_open'

export const THEME_OPTIONS: { value: Theme; label: string; hint: string }[] = [
  { value: 'why_major', label: 'Why this major', hint: '"Why do you want to study X"' },
  { value: 'why_school', label: 'Why this school', hint: '"Why us specifically"' },
  { value: 'community_identity', label: 'Identity / community', hint: 'background, identity, diversity, belonging' },
  { value: 'intellectual_curiosity', label: 'Intellectual curiosity', hint: 'ideas, learning, books/media you love' },
  { value: 'extracurricular_activity', label: 'Extracurricular / activity', hint: 'elaborate on an EC, job, or responsibility' },
  { value: 'challenge_adversity', label: 'Challenge / adversity', hint: 'overcoming something, disagreement, failure' },
  { value: 'values_joy', label: 'Values / joy / quirky', hint: 'what brings you joy, short-answer quick-hits' },
  { value: 'future_contribution', label: 'Future / contribution', hint: 'how you\'ll use it, what you\'ll contribute' },
  { value: 'creative_open', label: 'Creative / open-ended', hint: '"teach a class", "write a song", roommate notes' },
]
