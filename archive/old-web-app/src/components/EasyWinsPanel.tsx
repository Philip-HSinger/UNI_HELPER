import type { EnrichedEntry } from '../types'
import { CARD_CLASS } from '../lib/uiStyles'

const MAX_SHOWN = 3

/** A quiet nudge toward low-effort schools already on your list that you haven't started yet —
 * not a catalog-wide recommendation engine, just a re-sort of what's already there. */
export function EasyWinsPanel({ entries }: { entries: EnrichedEntry[] }) {
  const candidates = entries
    .filter((e) => e.status === 'not_started')
    .slice()
    .sort((a, b) => a.essayEffort - b.essayEffort)
    .slice(0, MAX_SHOWN)

  if (candidates.length === 0) return null

  return (
    <div className={CARD_CLASS}>
      <h2 className="mb-1 text-sm font-semibold text-ink">Easiest to apply to</h2>
      <p className="mb-3 text-xs text-ink-muted">
        Lowest essay-writing effort among schools on your list you haven't started yet.
      </p>
      <ul className="space-y-1">
        {candidates.map((e) => (
          <li key={e.id} className="flex items-center justify-between text-sm">
            <span className="font-medium text-ink">{e.name}</span>
            <span className="font-mono text-xs tabular-nums text-accent">effort {e.essayEffort}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
