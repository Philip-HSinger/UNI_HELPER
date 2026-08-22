import type { EnrichedEntry } from '../types'
import { CLASSIFICATION_STYLES, RECOMMENDATION_STYLES } from '../lib/uiStyles'

function ScoreCell({ percentile, p25, p50, p75 }: { percentile: number; p25: number; p50: number; p75: number }) {
  return (
    <td className="px-3 py-3">
      <div className="font-mono text-sm tabular-nums text-ink">
        {percentile}
        <span className="text-ink-muted"> %ile</span>
      </div>
      <div className="font-mono text-xs tabular-nums text-ink-muted">
        band {p25}/{p50}/{p75}
      </div>
    </td>
  )
}

export function LikelihoodRow({ entry }: { entry: EnrichedEntry }) {
  return (
    <tr className="border-b border-hairline last:border-0">
      <td className="px-3 py-3 font-medium text-ink">{entry.name}</td>
      <td className="px-3 py-3">
        <span
          className={`rounded-sm px-2 py-0.5 text-xs font-medium tracking-wide ${CLASSIFICATION_STYLES[entry.classification]}`}
        >
          {entry.classification}
        </span>
      </td>
      <ScoreCell
        percentile={entry.englishPercentile}
        p25={entry.englishP25}
        p50={entry.englishP50}
        p75={entry.englishP75}
      />
      <ScoreCell percentile={entry.mathPercentile} p25={entry.mathP25} p50={entry.mathP50} p75={entry.mathP75} />
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
