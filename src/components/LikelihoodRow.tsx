import type { EnrichedEntry } from '../types'
import { compositeBand } from '../lib/scoring'
import { CLASSIFICATION_STYLES, RECOMMENDATION_STYLES } from '../lib/uiStyles'

export function LikelihoodRow({ entry }: { entry: EnrichedEntry }) {
  const composite = compositeBand(entry)

  return (
    <tr className="border-b border-hairline last:border-0">
      <td className="px-3 py-3">
        <div className="font-medium text-ink">{entry.name}</div>
        <div className="font-mono text-xs tabular-nums text-ink-muted">
          Composite (approx.) {composite.p25}/{composite.p50}/{composite.p75}
        </div>
      </td>
      <td className="px-3 py-3">
        <span
          className={`rounded-sm px-2 py-0.5 text-xs font-medium tracking-wide ${CLASSIFICATION_STYLES[entry.classification]}`}
        >
          {entry.classification}
        </span>
      </td>
      <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">
        {entry.englishPercentile}
        <span className="text-ink-muted"> / {entry.mathPercentile}</span>
      </td>
      <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">{entry.weightedAverage}</td>
      <td className="px-3 py-3 text-sm text-ink">{entry.importance}</td>
      <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">
        {entry.acceptanceRate === null ? '—' : `${(entry.acceptanceRate * 100).toFixed(1)}%`}
      </td>
      <td className={`px-3 py-3 text-sm font-medium ${RECOMMENDATION_STYLES[entry.testRecommendation]}`}>
        {entry.testRecommendation}
      </td>
    </tr>
  )
}
