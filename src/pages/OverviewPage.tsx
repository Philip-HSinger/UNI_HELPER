import { useAppContext } from '../context/AppContext'
import { useSortedEntries } from '../hooks/useSortedEntries'
import { ScoreInputPanel } from '../components/ScoreInputPanel'
import { ApplyingSchoolsPanel } from '../components/ApplyingSchoolsPanel'
import { SummaryBar } from '../components/SummaryBar'
import { AddSchoolPanel } from '../components/AddSchoolPanel'
import { StatusBadge } from '../components/StatusBadge'
import { CARD_CLASS_FLUSH, CLASSIFICATION_STYLES } from '../lib/uiStyles'
import type { EnrichedEntry } from '../types'

export function OverviewPage() {
  const { catalog, ownScores, setOwnScores, entries, excludeCatalogIds, addFromCatalog, setStatus, removeEntry } =
    useAppContext()

  const { sorted, sortKey, sortDir, toggleSort } = useSortedEntries<EnrichedEntry, keyof EnrichedEntry>(
    entries,
    'efficiencyScore',
  )

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <ScoreInputPanel scores={ownScores} onChange={setOwnScores} />
        <ApplyingSchoolsPanel entries={entries} />
      </div>

      <SummaryBar entries={entries} />

      <AddSchoolPanel catalog={catalog} excludeCatalogIds={excludeCatalogIds} onAddFromCatalog={addFromCatalog} />

      {entries.length === 0 ? (
        <div className={`${CARD_CLASS_FLUSH} border-dashed p-10 text-center text-sm text-ink-muted`}>
          No schools on your list yet — add one above.
        </div>
      ) : (
        <div className={CARD_CLASS_FLUSH}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] border-collapse text-left">
              <thead>
                <tr className="border-b border-hairline text-xs font-semibold uppercase tracking-wide text-ink-muted">
                  <th className="px-3 py-2">School</th>
                  <th className="px-3 py-2">Fit</th>
                  <th
                    className="cursor-pointer select-none px-3 py-2 hover:text-ink"
                    onClick={() => toggleSort('efficiencyScore')}
                  >
                    Efficiency{sortKey === 'efficiencyScore' && (sortDir === 'asc' ? ' ▲' : ' ▼')}
                  </th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {sorted.map((entry) => (
                  <tr key={entry.id} className="border-b border-hairline last:border-0 hover:bg-accent-soft">
                    <td className="px-3 py-3 font-medium text-ink">{entry.name}</td>
                    <td className="px-3 py-3">
                      <span
                        className={`rounded-sm px-2 py-0.5 text-xs font-medium tracking-wide ${CLASSIFICATION_STYLES[entry.classification]}`}
                      >
                        {entry.classification}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <span className="inline-flex items-center justify-center rounded-md border border-accent px-2 py-0.5 font-mono text-sm font-semibold tabular-nums text-accent">
                        {entry.efficiencyScore}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <StatusBadge status={entry.status} onChange={(status) => setStatus(entry.id, status)} />
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => removeEntry(entry.id)}
                        className="rounded-md px-2 py-1 text-xs text-ink-muted hover:bg-accent-soft hover:text-ink"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
