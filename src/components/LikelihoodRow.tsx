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
          Combined approx. {composite.p25}/{composite.p50}/{composite.p75}
        </div>
      </td>
      <td className="px-3 py-3">
        <span
          className={`rounded-sm px-2 py-0.5 text-xs font-medium tracking-wide ${CLASSIFICATION_STYLES[entry.classification]}`}
        >
          {entry.classification}
        </span>
      </td>
      <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink-muted">
        {entry.englishP25}/{entry.englishP50}/{entry.englishP75}
      </td>
      <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">{entry.englishPercentile}</td>
      <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink-muted">
        {entry.mathP25}/{entry.mathP50}/{entry.mathP75}
      </td>
      <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">{entry.mathPercentile}</td>
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
