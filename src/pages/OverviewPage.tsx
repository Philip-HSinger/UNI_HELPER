import { useAppContext } from '../context/AppContext'
import { useSortedEntries } from '../hooks/useSortedEntries'
import { ScoreInputPanel } from '../components/ScoreInputPanel'
import { CommittedSchoolsPanel } from '../components/CommittedSchoolsPanel'
import { SummaryBar } from '../components/SummaryBar'
import { AddSchoolPanel } from '../components/AddSchoolPanel'
import { StatusBadge } from '../components/StatusBadge'
import { CLASSIFICATION_STYLES } from '../lib/uiStyles'
import type { EnrichedEntry } from '../types'

export function OverviewPage() {
  const {
    catalog,
    ownScores,
    setOwnScores,
    entries,
    excludeCatalogIds,
    addFromCatalog,
    addBlank,
    toggleCommitted,
    updateEntry,
    removeEntry,
  } = useAppContext()

  const { sorted, sortKey, sortDir, toggleSort } = useSortedEntries<EnrichedEntry, keyof EnrichedEntry>(
    entries,
    'efficiencyScore',
  )

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <ScoreInputPanel scores={ownScores} onChange={setOwnScores} />
        <CommittedSchoolsPanel entries={entries} />
      </div>

      <SummaryBar entries={entries} />

      <AddSchoolPanel
        catalog={catalog}
        excludeCatalogIds={excludeCatalogIds}
        onAddFromCatalog={addFromCatalog}
        onAddBlank={addBlank}
      />

      {entries.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-400 dark:border-slate-700 dark:bg-slate-900">
          No schools on your list yet — add one above.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <table className="w-full min-w-[700px] border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:border-slate-700">
                <th className="px-3 py-2">School</th>
                <th className="px-3 py-2">Fit</th>
                <th
                  className="cursor-pointer select-none px-3 py-2 hover:text-slate-600 dark:hover:text-slate-200"
                  onClick={() => toggleSort('efficiencyScore')}
                >
                  Efficiency{sortKey === 'efficiencyScore' && (sortDir === 'asc' ? ' ▲' : ' ▼')}
                </th>
                <th className="px-3 py-2">Committed</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {sorted.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
                >
                  <td className="px-3 py-3 font-medium text-slate-900 dark:text-slate-100">{entry.name}</td>
                  <td className="px-3 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${CLASSIFICATION_STYLES[entry.classification]}`}
                    >
                      {entry.classification}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-sm font-semibold tabular-nums text-indigo-600 dark:text-indigo-400">
                    {entry.efficiencyScore}
                  </td>
                  <td className="px-3 py-3">
                    <button
                      type="button"
                      onClick={() => toggleCommitted(entry.id)}
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        entry.committed
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-400 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700'
                      }`}
                    >
                      {entry.committed ? '★ Committed' : '☆ Committed?'}
                    </button>
                  </td>
                  <td className="px-3 py-3">
                    <StatusBadge status={entry.status} onChange={(status) => updateEntry(entry.id, { status })} />
                  </td>
                  <td className="px-3 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => removeEntry(entry.id)}
                      className="rounded-lg px-2 py-1 text-xs text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
