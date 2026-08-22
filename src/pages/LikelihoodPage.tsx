import { useAppContext } from '../context/AppContext'
import { useSortedEntries } from '../hooks/useSortedEntries'
import { LikelihoodRow } from '../components/LikelihoodRow'
import { CARD_CLASS, CARD_CLASS_FLUSH } from '../lib/uiStyles'
import type { EnrichedEntry } from '../types'

export function LikelihoodPage() {
  const { entries, ownScores } = useAppContext()
  const { sorted, sortKey, sortDir, toggleSort } = useSortedEntries<EnrichedEntry, keyof EnrichedEntry>(
    entries,
    'weightedAverage',
  )

  return (
    <div className="space-y-4">
      <div className={`${CARD_CLASS} text-sm text-ink-muted`}>
        Your scores:{' '}
        <span className="font-mono font-medium tabular-nums text-ink">English {ownScores.english}</span>
        {', '}
        <span className="font-mono font-medium tabular-nums text-ink">Math {ownScores.math}</span> — edit these on
        the Overview page. Percentiles below are estimated from each school's published score band
        via bell-curve interpolation; the weighted score then adjusts for how much that school
        actually weighs standardized testing.
      </div>

      {entries.length === 0 ? (
        <div className={`${CARD_CLASS_FLUSH} border-dashed p-10 text-center text-sm text-ink-muted`}>
          No schools on your list yet — add one from the Overview page.
        </div>
      ) : (
        <div className={CARD_CLASS_FLUSH}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] border-collapse text-left">
              <thead>
                <tr className="border-b border-hairline text-xs font-semibold uppercase tracking-wide text-ink-muted">
                  <th className="px-3 py-2">School</th>
                  <th className="px-3 py-2">Fit</th>
                  <th className="px-3 py-2">Eng / Math %ile</th>
                  <th
                    className="cursor-pointer select-none px-3 py-2 hover:text-ink"
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
                  <LikelihoodRow key={entry.id} entry={entry} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
