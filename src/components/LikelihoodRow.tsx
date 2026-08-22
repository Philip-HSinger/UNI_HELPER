import type { EnrichedEntry, Importance, SchoolEntry } from '../types'
import { compositeBand } from '../lib/scoring'
import { CLASSIFICATION_STYLES, RECOMMENDATION_STYLES } from '../lib/uiStyles'
import { Field, inputClass } from './FormField'

const IMPORTANCE_OPTIONS: Importance[] = ['Very Important', 'Important', 'Considered', 'Not Considered']

export function LikelihoodRow({
  entry,
  expanded,
  onToggleExpand,
  onUpdate,
}: {
  entry: EnrichedEntry
  expanded: boolean
  onToggleExpand: () => void
  onUpdate: (partial: Partial<SchoolEntry>) => void
}) {
  const composite = compositeBand(entry)

  return (
    <>
      <tr
        className="cursor-pointer border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
        onClick={onToggleExpand}
      >
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

      {expanded && (
        <tr className="border-b border-slate-100 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-800/30">
          <td colSpan={7} className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Score bands (25th / 50th / 75th)
                </h4>
                <Field label="English">
                  <div className="flex gap-1">
                    <input
                      type="number"
                      value={entry.englishP25}
                      onChange={(e) => onUpdate({ englishP25: Number(e.target.value) })}
                      className={`${inputClass} w-full`}
                    />
                    <input
                      type="number"
                      value={entry.englishP50}
                      onChange={(e) => onUpdate({ englishP50: Number(e.target.value) })}
                      className={`${inputClass} w-full`}
                    />
                    <input
                      type="number"
                      value={entry.englishP75}
                      onChange={(e) => onUpdate({ englishP75: Number(e.target.value) })}
                      className={`${inputClass} w-full`}
                    />
                  </div>
                </Field>
                <Field label="Math">
                  <div className="flex gap-1">
                    <input
                      type="number"
                      value={entry.mathP25}
                      onChange={(e) => onUpdate({ mathP25: Number(e.target.value) })}
                      className={`${inputClass} w-full`}
                    />
                    <input
                      type="number"
                      value={entry.mathP50}
                      onChange={(e) => onUpdate({ mathP50: Number(e.target.value) })}
                      className={`${inputClass} w-full`}
                    />
                    <input
                      type="number"
                      value={entry.mathP75}
                      onChange={(e) => onUpdate({ mathP75: Number(e.target.value) })}
                      className={`${inputClass} w-full`}
                    />
                  </div>
                </Field>
              </div>

              <div className="space-y-2">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Admissions context</h4>
                <Field label="How much this school weighs testing">
                  <select
                    value={entry.importance}
                    onChange={(e) => onUpdate({ importance: e.target.value as Importance })}
                    className={inputClass}
                  >
                    {IMPORTANCE_OPTIONS.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Acceptance rate (%)">
                  <input
                    type="number"
                    min={0}
                    max={100}
                    step={0.1}
                    value={entry.acceptanceRate === null ? '' : entry.acceptanceRate * 100}
                    placeholder="unknown"
                    onChange={(e) =>
                      onUpdate({ acceptanceRate: e.target.value === '' ? null : Number(e.target.value) / 100 })
                    }
                    className={inputClass}
                  />
                </Field>
                <label className="flex items-center gap-2 pt-1 text-sm text-slate-600 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={entry.testOptional}
                    onChange={(e) => onUpdate({ testOptional: e.target.checked })}
                    className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  Test-optional
                </label>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
