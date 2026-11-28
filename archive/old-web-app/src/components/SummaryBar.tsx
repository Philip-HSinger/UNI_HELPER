import type { EnrichedEntry } from '../types'
import { CARD_CLASS } from '../lib/uiStyles'

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className={`flex-1 ${CARD_CLASS}`}>
      <div className="text-xs font-medium text-ink-muted">{label}</div>
      <div className="mt-0.5 font-mono text-xl font-semibold tabular-nums text-ink">{value}</div>
    </div>
  )
}

export function SummaryBar({ entries }: { entries: EnrichedEntry[] }) {
  const applyingEntries = entries.filter((e) => e.status !== 'not_started')
  const reach = entries.filter((e) => e.classification === 'Reach').length
  const match = entries.filter((e) => e.classification === 'Match').length
  const safety = entries.filter((e) => e.classification === 'Safety').length
  const avgEfficiency =
    entries.length === 0
      ? 0
      : Math.round((entries.reduce((s, e) => s + e.efficiencyScore, 0) / entries.length) * 10) / 10
  // Every school on the list, not just ones marked "Applying" — the point is the total writing
  // effort ahead if you went through with all of them, not just the ones already decided.
  const totalEffort = Math.round(entries.reduce((s, e) => s + e.essayEffort, 0) * 10) / 10

  return (
    <div className="flex flex-wrap gap-3">
      <Stat label="Schools on your list" value={entries.length} />
      <Stat label="Applying / decided" value={applyingEntries.length} />
      <Stat label="Reach · Match · Safety" value={`${reach} · ${match} · ${safety}`} />
      <Stat label="Avg. efficiency score" value={avgEfficiency} />
      <Stat label="Total effort to apply" value={totalEffort} />
    </div>
  )
}
