import type { EnrichedEntry } from '../types'

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="text-xs font-medium text-slate-400">{label}</div>
      <div className="mt-0.5 text-xl font-semibold text-slate-900 dark:text-slate-100">{value}</div>
    </div>
  )
}

export function SummaryBar({ entries }: { entries: EnrichedEntry[] }) {
  const applying = entries.filter((e) => e.status !== 'not_started').length
  const reach = entries.filter((e) => e.classification === 'Reach').length
  const match = entries.filter((e) => e.classification === 'Match').length
  const safety = entries.filter((e) => e.classification === 'Safety').length
  const avgEfficiency =
    entries.length === 0
      ? 0
      : Math.round((entries.reduce((s, e) => s + e.efficiencyScore, 0) / entries.length) * 10) / 10

  return (
    <div className="flex flex-wrap gap-3">
      <Stat label="Schools on your list" value={entries.length} />
      <Stat label="Applying / decided" value={applying} />
      <Stat label="Reach · Match · Safety" value={`${reach} · ${match} · ${safety}`} />
      <Stat label="Avg. efficiency score" value={avgEfficiency} />
    </div>
  )
}
