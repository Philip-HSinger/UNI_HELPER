import { useState } from 'react'
import { useAppContext } from '../context/AppContext'
import { useSortedEntries } from '../hooks/useSortedEntries'
import { DifficultyRow } from '../components/DifficultyRow'
import type { EnrichedEntry } from '../types'

export function DifficultyPage() {
  const { entries } = useAppContext()
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const { sorted, sortKey, sortDir, toggleSort } = useSortedEntries<EnrichedEntry, keyof EnrichedEntry>(
    entries,
    'essayEffort',
    'asc',
  )

  return (
    <div className="space-y-4">
      {entries.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400 dark:border-slate-700 dark:bg-slate-900">
          No schools on your list yet — add one from the Overview page.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <table className="w-full min-w-[800px] border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:border-slate-700">
                <th className="px-3 py-2">School</th>
                <th className="px-3 py-2"># essays</th>
                <th className="px-3 py-2">Total word count</th>
                <th
                  className="cursor-pointer select-none px-3 py-2 hover:text-slate-600 dark:hover:text-slate-200"
                  onClick={() => toggleSort('difficulty')}
                >
                  Difficulty{sortKey === 'difficulty' && (sortDir === 'asc' ? ' ▲' : ' ▼')}
                </th>
                <th className="px-3 py-2">Reuse</th>
                <th
                  className="cursor-pointer select-none px-3 py-2 hover:text-slate-600 dark:hover:text-slate-200"
                  onClick={() => toggleSort('essayEffort')}
                >
                  Effort{sortKey === 'essayEffort' && (sortDir === 'asc' ? ' ▲' : ' ▼')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((entry) => (
                <DifficultyRow
                  key={entry.id}
                  entry={entry}
                  expanded={expandedId === entry.id}
                  onToggleExpand={() => setExpandedId((cur) => (cur === entry.id ? null : entry.id))}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
