import { useMemo, useState } from 'react'
import type { EnrichedEntry, EssayBank, SchoolEntry } from '../types'
import { SchoolRow } from './SchoolRow'

type SortKey = 'name' | 'englishPercentile' | 'mathPercentile' | 'weightedAverage' | 'essayEffort' | 'efficiencyScore'

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: 'name', label: 'School' },
  { key: 'name', label: 'Fit' }, // classification column, not independently sortable
  { key: 'englishPercentile', label: 'English %ile' },
  { key: 'mathPercentile', label: 'Math %ile' },
  { key: 'weightedAverage', label: 'Weighted score' },
  { key: 'essayEffort', label: 'Essay effort' },
  { key: 'efficiencyScore', label: 'Efficiency' },
]

export function SchoolTable({
  entries,
  banks,
  onUpdate,
  onSetSimilarity,
  onRemove,
}: {
  entries: EnrichedEntry[]
  banks: EssayBank[]
  onUpdate: (id: string, partial: Partial<SchoolEntry>) => void
  onSetSimilarity: (id: string, bankId: string, value: number) => void
  onRemove: (id: string) => void
}) {
  const [sortKey, setSortKey] = useState<SortKey>('efficiencyScore')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const sorted = useMemo(() => {
    const copy = [...entries]
    copy.sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number)
      return sortDir === 'asc' ? cmp : -cmp
    })
    return copy
  }, [entries, sortKey, sortDir])

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  if (entries.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400 dark:border-slate-700 dark:bg-slate-900">
        No schools on your list yet — add one above to see your scores.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <table className="w-full min-w-[900px] border-collapse text-left">
        <thead>
          <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:border-slate-700">
            {COLUMNS.map((col, i) => (
              <th
                key={col.label}
                className={`px-3 py-2 ${i > 1 ? 'cursor-pointer select-none hover:text-slate-600 dark:hover:text-slate-200' : ''}`}
                onClick={() => i > 1 && toggleSort(col.key)}
              >
                {col.label}
                {i > 1 && sortKey === col.key && (sortDir === 'asc' ? ' ▲' : ' ▼')}
              </th>
            ))}
            <th className="px-3 py-2">Test rec.</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2" />
          </tr>
        </thead>
        <tbody>
          {sorted.map((entry) => (
            <SchoolRow
              key={entry.id}
              entry={entry}
              banks={banks}
              expanded={expandedId === entry.id}
              onToggleExpand={() => setExpandedId((cur) => (cur === entry.id ? null : entry.id))}
              onUpdate={(partial) => onUpdate(entry.id, partial)}
              onSetSimilarity={(bankId, value) => onSetSimilarity(entry.id, bankId, value)}
              onRemove={() => onRemove(entry.id)}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
