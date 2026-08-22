import type { EnrichedEntry } from '../types'
import { THEME_OPTIONS } from '../lib/themes'
import { computeThemeCoverage } from '../lib/scoring'

export function ThemeCoveragePanel({ entries }: { entries: EnrichedEntry[] }) {
  const committed = entries.filter((e) => e.committed)
  const coverage = computeThemeCoverage(committed.flatMap((e) => e.prompts))

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h2 className="mb-1 text-sm font-semibold text-slate-900 dark:text-slate-100">Your committed schools</h2>
      <p className="mb-3 text-xs text-slate-400">
        Mark a school "Committed" (100% going, essays happening regardless) in the table below.
        Every other school's essay reuse is estimated from how much its prompts overlap in theme
        with your committed schools' prompts — tag prompts in a school's expanded row to power this.
      </p>
      {committed.length === 0 ? (
        <p className="text-sm text-slate-400">No committed schools yet.</p>
      ) : (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {committed.map((e) => (
            <span
              key={e.id}
              className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
            >
              {e.name}
            </span>
          ))}
        </div>
      )}
      <div className="flex flex-wrap gap-1.5">
        {THEME_OPTIONS.map((t) => {
          const count = coverage[t.value] ?? 0
          return (
            <span
              key={t.value}
              title={t.hint}
              className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                count > 0
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300'
                  : 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500'
              }`}
            >
              {t.label}
              {count > 0 && <span className="ml-1 opacity-70">×{count}</span>}
            </span>
          )
        })}
      </div>
    </div>
  )
}
