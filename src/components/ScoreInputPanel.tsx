import type { OwnScores } from '../types'

export function ScoreInputPanel({
  scores,
  onChange,
}: {
  scores: OwnScores
  onChange: (scores: OwnScores) => void
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">Your SAT scores</h2>
      <div className="grid grid-cols-2 gap-3">
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
            English (EBRW)
          </span>
          <input
            type="number"
            min={200}
            max={800}
            step={10}
            value={scores.english}
            onChange={(e) => onChange({ ...scores, english: Number(e.target.value) })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">Math</span>
          <input
            type="number"
            min={200}
            max={800}
            step={10}
            value={scores.math}
            onChange={(e) => onChange({ ...scores, math: Number(e.target.value) })}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
        </label>
      </div>
      <p className="mt-2 text-xs text-slate-400">
        Used to estimate your percentile at each school from its published 25th/50th/75th bands.
      </p>
    </div>
  )
}
