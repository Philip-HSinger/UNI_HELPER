import { useMemo, useState } from 'react'
import type { EnrichedEntry, SchoolEntry } from '../types'
import type { Theme } from '../lib/themes'
import { SchoolRow } from './SchoolRow'

type SortKey =
  | 'name'
  | 'englishPercentile'
  | 'mathPercentile'
  | 'weightedAverage'
  | 'estimatedReuse'
  | 'essayEffort'
  | 'efficiencyScore'

const COLUMNS: { key: SortKey; label: string; sortable: boolean }[] = [
  { key: 'name', label: 'School', sortable: false },
  { key: 'name', label: 'Committed', sortable: false },
  { key: 'name', label: 'Fit', sortable: false },
  { key: 'englishPercentile', label: 'English %ile', sortable: true },
  { key: 'mathPercentile', label: 'Math %ile', sortable: true },
  { key: 'weightedAverage', label: 'Weighted score', sortable: true },
  { key: 'estimatedReuse', label: 'Reuse', sortable: true },
  { key: 'essayEffort', label: 'Essay effort', sortable: true },
  { key: 'efficiencyScore', label: 'Efficiency', sortable: true },
]

export function SchoolTable({
  entries,
  onUpdate,
  onToggleCommitted,
  onAddPrompt,
  onUpdatePromptText,
  onTogglePromptTheme,
  onRemovePrompt,
  onRemove,
}: {
  entries: EnrichedEntry[]
  onUpdate: (id: string, partial: Partial<SchoolEntry>) => void
  onToggleCommitted: (id: string) => void
  onAddPrompt: (id: string, text: string) => void
  onUpdatePromptText: (id: string, index: number, text: string) => void
  onTogglePromptTheme: (id: string, index: number, theme: Theme) => void
  onRemovePrompt: (id: string, index: number) => void
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
      <table className="w-full min-w-[1000px] border-collapse text-left">
        <thead>
          <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:border-slate-700">
            {COLUMNS.map((col) => (
              <th
                key={col.label}
                className={`px-3 py-2 ${col.sortable ? 'cursor-pointer select-none hover:text-slate-600 dark:hover:text-slate-200' : ''}`}
                onClick={() => col.sortable && toggleSort(col.key)}
              >
                {col.label}
                {col.sortable && sortKey === col.key && (sortDir === 'asc' ? ' ▲' : ' ▼')}
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
              expanded={expandedId === entry.id}
              onToggleExpand={() => setExpandedId((cur) => (cur === entry.id ? null : entry.id))}
              onUpdate={(partial) => onUpdate(entry.id, partial)}
              onToggleCommitted={() => onToggleCommitted(entry.id)}
              onAddPrompt={(text) => onAddPrompt(entry.id, text)}
              onUpdatePromptText={(index, text) => onUpdatePromptText(entry.id, index, text)}
              onTogglePromptTheme={(index, theme) => onTogglePromptTheme(entry.id, index, theme)}
              onRemovePrompt={(index) => onRemovePrompt(entry.id, index)}
              onRemove={() => onRemove(entry.id)}
            />
          ))}
        </tbody>
      </table>
    </div>
  )
}
