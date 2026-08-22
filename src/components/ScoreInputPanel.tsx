import type { OwnScores } from '../types'
import { CARD_CLASS } from '../lib/uiStyles'

export function ScoreInputPanel({
  scores,
  onChange,
}: {
  scores: OwnScores
  onChange: (scores: OwnScores) => void
}) {
  return (
    <div className={CARD_CLASS}>
      <h2 className="mb-3 text-sm font-semibold text-ink">Your SAT scores</h2>
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-ink-muted">English (EBRW)</span>
          <input
            type="number"
            min={200}
            max={800}
            step={10}
            value={scores.english}
            onChange={(e) => onChange({ ...scores, english: Number(e.target.value) })}
            className="w-full rounded-md border border-hairline bg-surface px-3 py-2 font-mono text-sm tabular-nums text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-ink-muted">Math</span>
          <input
            type="number"
            min={200}
            max={800}
            step={10}
            value={scores.math}
            onChange={(e) => onChange({ ...scores, math: Number(e.target.value) })}
            className="w-full rounded-md border border-hairline bg-surface px-3 py-2 font-mono text-sm tabular-nums text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </label>
      </div>
      <p className="mt-2 text-xs text-ink-muted">
        Used to estimate your percentile at each school from its published 25th/50th/75th bands.
      </p>
    </div>
  )
}
