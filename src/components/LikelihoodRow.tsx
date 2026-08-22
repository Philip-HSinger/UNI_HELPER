import type { EnrichedEntry } from '../types'
import { compositeBand } from '../lib/scoring'
import { CLASSIFICATION_STYLES, RECOMMENDATION_STYLES } from '../lib/uiStyles'

export function LikelihoodRow({ entry }: { entry: EnrichedEntry }) {
  const composite = compositeBand(entry)

  return (
    <tr className="border-b border-slate-100 last:border-0 dark:border-slate-800">
      <td className="px-3 py-3">
        <div className="font-medium text-slate-900 dark:text-slate-100">{entry.name}</div>
        <div className="text-xs text-slate-400">
          Composite (approx.) {composite.p25}/{composite.p50}/{composite.p75}
        </div>
      </td>
      <td className="px-3 py-3">
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${CLASSIFICATION_STYLES[entry.classification]}`}>
          {entry.classification}
        </span>
      </td>
      <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">
        {entry.englishPercentile}
        <span className="text-slate-400"> / {entry.mathPercentile}</span>
      </td>
      <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.weightedAverage}</td>
      <td className="px-3 py-3 text-sm text-slate-600 dark:text-slate-300">{entry.importance}</td>
      <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">
        {entry.acceptanceRate === null ? '—' : `${(entry.acceptanceRate * 100).toFixed(1)}%`}
      </td>
      <td className={`px-3 py-3 text-sm font-medium ${RECOMMENDATION_STYLES[entry.testRecommendation]}`}>
        {entry.testRecommendation}
      </td>
    </tr>
  )
}
