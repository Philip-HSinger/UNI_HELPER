// Shared style constants, reused across the Overview/Likelihood/Difficulty pages.

// The recurring flat "editorial card" wrapper. Two shapes: a padded panel for form-ish content,
// and a flush (no padding) wrapper for things that manage their own inner spacing (tables,
// empty states).
export const CARD_CLASS = 'rounded-md border border-hairline bg-surface p-4'
export const CARD_CLASS_FLUSH = 'overflow-hidden rounded-md border border-hairline bg-surface'

// Reach/Match/Safety badges — a deliberate bit of traffic-light color: green for a no-brainer,
// red for a genuine long shot, amber for the real toss-up in between. Paired with an icon (see
// ClassificationIcon in components/icons.tsx) so the signal doesn't rely on color alone.
export const CLASSIFICATION_STYLES: Record<string, string> = {
  Reach: 'border border-danger bg-danger-soft text-danger',
  Match: 'border border-caution bg-caution-soft text-caution',
  Safety: 'border border-accent bg-accent-soft text-accent',
}

// Submit/Helps vs Don't Submit/Hurts test-recommendation text. Not treated as good/bad news the
// way classification is — "Don't Submit" is neutral practical advice, not a warning — so this
// stays a two-tone accent/muted distinction rather than green/red.
export const RECOMMENDATION_STYLES: Record<string, string> = {
  Submit: 'text-accent font-semibold',
  Helps: 'text-accent font-semibold',
  "Don't Submit": 'text-ink-muted',
  Hurts: 'text-ink-muted',
}
