import { useState } from 'react'
import { useAppContext } from '../context/AppContext'
import { useSortedEntries } from '../hooks/useSortedEntries'
import { LikelihoodRow } from '../components/LikelihoodRow'
import type { EnrichedEntry } from '../types'

export function LikelihoodPage() {
  const { entries, ownScores, updateEntry } = useAppContext()
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const { sorted, sortKey, sortDir, toggleSort } = useSortedEntries<EnrichedEntry, keyof EnrichedEntry>(
    entries,
    'weightedAverage',
  )

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
        Your scores: <span className="font-medium text-slate-800 dark:text-slate-200">English {ownScores.english}</span>
        {', '}
        <span className="font-medium text-slate-800 dark:text-slate-200">Math {ownScores.math}</span> — edit these on
        the Overview page. Percentiles below are estimated from each school's published score band
        via bell-curve interpolation; the weighted score then adjusts for how much that school
        actually weighs standardized testing.
      </div>

      {entries.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400 dark:border-slate-700 dark:bg-slate-900">
          No schools on your list yet — add one from the Overview page.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <table className="w-full min-w-[900px] border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:border-slate-700">
                <th className="px-3 py-2">School</th>
                <th className="px-3 py-2">Fit</th>
                <th className="px-3 py-2">Eng / Math %ile</th>
                <th
                  className="cursor-pointer select-none px-3 py-2 hover:text-slate-600 dark:hover:text-slate-200"
                  onClick={() => toggleSort('weightedAverage')}
                >
                  Weighted score{sortKey === 'weightedAverage' && (sortDir === 'asc' ? ' ▲' : ' ▼')}
                </th>
                <th className="px-3 py-2">Importance</th>
                <th className="px-3 py-2">Acceptance rate</th>
                <th className="px-3 py-2">Test rec.</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((entry) => (
                <LikelihoodRow
                  key={entry.id}
                  entry={entry}
                  expanded={expandedId === entry.id}
                  onToggleExpand={() => setExpandedId((cur) => (cur === entry.id ? null : entry.id))}
                  onUpdate={(partial) => updateEntry(entry.id, partial)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
