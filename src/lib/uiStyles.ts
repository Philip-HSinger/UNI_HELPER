// Shared style constants, reused across the Overview/Likelihood/Difficulty pages. Deliberately
// monochrome (ink/muted/accent only) — see src/components/StatusBadge.tsx for the same language
// applied to application status.

// The recurring flat "editorial card" wrapper. Two shapes: a padded panel for form-ish content,
// and a flush (no padding) wrapper for things that manage their own inner spacing (tables,
// empty states).
export const CARD_CLASS = 'rounded-md border border-hairline bg-surface p-4'
export const CARD_CLASS_FLUSH = 'overflow-hidden rounded-md border border-hairline bg-surface'

// Reach/Match/Safety badges. Safety is the one "good news" highlight (accent); Reach draws the
// eye in plain ink rather than a rainbow alert color; Match stays quiet.
export const CLASSIFICATION_STYLES: Record<string, string> = {
  Reach: 'border border-ink text-ink font-semibold',
  Match: 'border border-hairline text-ink-muted',
  Safety: 'border border-accent bg-accent-soft text-accent',
}

// Submit/Helps vs Don't Submit/Hurts test-recommendation text.
export const RECOMMENDATION_STYLES: Record<string, string> = {
  Submit: 'text-accent font-semibold',
  Helps: 'text-accent font-semibold',
  "Don't Submit": 'text-ink-muted',
  Hurts: 'text-ink-muted',
}
