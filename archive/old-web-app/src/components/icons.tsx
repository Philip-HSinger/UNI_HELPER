// Small hand-drawn inline SVG icons — no icon library dependency. Each inherits its color from
// `currentColor`, so it always matches the text color it sits next to in both light and dark.
import type { Classification, TestRecommendation } from '../lib/scoring'

type IconProps = { className?: string }

const BASE = 'h-3.5 w-3.5 shrink-0'

export function CheckCircleIcon({ className = '' }: IconProps) {
  return (
    <svg viewBox="0 0 16 16" fill="none" className={`${BASE} ${className}`} aria-hidden="true">
      <circle cx="8" cy="8" r="6.25" stroke="currentColor" strokeWidth="1.3" />
      <path d="M5.1 8.3 7 10.2l3.9-4.3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function MinusCircleIcon({ className = '' }: IconProps) {
  return (
    <svg viewBox="0 0 16 16" fill="none" className={`${BASE} ${className}`} aria-hidden="true">
      <circle cx="8" cy="8" r="6.25" stroke="currentColor" strokeWidth="1.3" />
      <path d="M5.2 8h5.6" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  )
}

export function AlertTriangleIcon({ className = '' }: IconProps) {
  return (
    <svg viewBox="0 0 16 16" fill="none" className={`${BASE} ${className}`} aria-hidden="true">
      <path d="M8 2.1 14.4 13.3H1.6L8 2.1Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
      <path d="M8 6.5v3" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <circle cx="8" cy="11.1" r="0.8" fill="currentColor" />
    </svg>
  )
}

/** Safety = a no-brainer (check), Match = a real toss-up (dash), Reach = a genuine long shot (alert). */
export function ClassificationIcon({ classification, className }: { classification: Classification; className?: string }) {
  if (classification === 'Safety') return <CheckCircleIcon className={className} />
  if (classification === 'Match') return <MinusCircleIcon className={className} />
  return <AlertTriangleIcon className={className} />
}

/** Submit/Helps = your scores help (check), Don't Submit/Hurts = they don't (dash — neutral, not an alarm). */
export function RecommendationIcon({ recommendation, className }: { recommendation: TestRecommendation; className?: string }) {
  if (recommendation === 'Submit' || recommendation === 'Helps') return <CheckCircleIcon className={className} />
  return <MinusCircleIcon className={className} />
}
