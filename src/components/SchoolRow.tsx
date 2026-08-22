import type { ReactNode } from 'react'
import type { EnrichedEntry, Importance, Prompt, SchoolEntry } from '../types'
import type { Theme } from '../lib/themes'
import { THEME_OPTIONS } from '../lib/themes'
import { StatusBadge } from './StatusBadge'

const IMPORTANCE_OPTIONS: Importance[] = ['Very Important', 'Important', 'Considered', 'Not Considered']

const CLASSIFICATION_STYLES: Record<string, string> = {
  Reach: 'bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300',
  Match: 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300',
  Safety: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300',
}

const RECOMMENDATION_STYLES: Record<string, string> = {
  Submit: 'text-emerald-600 dark:text-emerald-400',
  Helps: 'text-emerald-600 dark:text-emerald-400',
  "Don't Submit": 'text-rose-600 dark:text-rose-400',
  Hurts: 'text-rose-600 dark:text-rose-400',
}

export function SchoolRow({
  entry,
  expanded,
  onToggleExpand,
  onUpdate,
  onToggleCommitted,
  onAddPrompt,
  onUpdatePromptText,
  onTogglePromptTheme,
  onRemovePrompt,
  onRemove,
}: {
  entry: EnrichedEntry
  expanded: boolean
  onToggleExpand: () => void
  onUpdate: (partial: Partial<SchoolEntry>) => void
  onToggleCommitted: () => void
  onAddPrompt: (text: string) => void
  onUpdatePromptText: (index: number, text: string) => void
  onTogglePromptTheme: (index: number, theme: Theme) => void
  onRemovePrompt: (index: number) => void
  onRemove: () => void
}) {
  return (
    <>
      <tr
        className="cursor-pointer border-b border-slate-100 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50"
        onClick={onToggleExpand}
      >
        <td className="px-3 py-3">
          <div className="font-medium text-slate-900 dark:text-slate-100">{entry.name}</div>
          <div className="text-xs text-slate-400">{entry.platform}</div>
        </td>
        <td className="px-3 py-3" onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            onClick={onToggleCommitted}
            title={entry.committed ? "You're committed — 100% going here" : 'Mark as committed (100% going)'}
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              entry.committed
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-400 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700'
            }`}
          >
            {entry.committed ? '★ Committed' : '☆ Committed?'}
          </button>
        </td>
        <td className="px-3 py-3">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${CLASSIFICATION_STYLES[entry.classification]}`}>
            {entry.classification}
          </span>
        </td>
        <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.englishPercentile}</td>
        <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.mathPercentile}</td>
        <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.weightedAverage}</td>
        <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.estimatedReuse}%</td>
        <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.essayEffort}</td>
        <td className="px-3 py-3 text-sm font-semibold tabular-nums text-indigo-600 dark:text-indigo-400">
          {entry.efficiencyScore}
        </td>
        <td className={`px-3 py-3 text-sm font-medium ${RECOMMENDATION_STYLES[entry.testRecommendation]}`}>
          {entry.testRecommendation}
        </td>
        <td className="px-3 py-3" onClick={(e) => e.stopPropagation()}>
          <StatusBadge status={entry.status} onChange={(status) => onUpdate({ status })} />
        </td>
        <td className="px-3 py-3 text-right">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onRemove()
            }}
            className="rounded-lg px-2 py-1 text-xs text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950"
          >
            Remove
          </button>
        </td>
      </tr>

      {expanded && (
        <tr className="border-b border-slate-100 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-800/30">
          <td colSpan={12} className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">School</h4>
                <div className="space-y-2">
                  <Field label="Name">
                    <input
                      value={entry.name}
                      onChange={(e) => onUpdate({ name: e.target.value })}
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Application platform">
                    <input
                      value={entry.platform}
                      onChange={(e) => onUpdate({ platform: e.target.value })}
                      className={inputClass}
                    />
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

              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Score bands (25th / 50th / 75th)
                </h4>
                <div className="space-y-2">
                  <Field label="English (25th / 50th / 75th)">
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
                  <Field label="Math (25th / 50th / 75th)">
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
                  <Field label="Essay difficulty (1-100)">
                    <input
                      type="range"
                      min={1}
                      max={100}
                      value={entry.difficulty}
                      onChange={(e) => onUpdate({ difficulty: Number(e.target.value) })}
                      className="w-full accent-indigo-600"
                    />
                    <div className="text-right text-xs text-slate-400">{entry.difficulty}</div>
                  </Field>
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
                </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Supplemental prompts
                  </h4>
                  <span className="text-xs font-medium text-indigo-600 dark:text-indigo-400">
                    ~{entry.estimatedReuse}% reuse
                  </span>
                </div>
                <p className="mb-2 text-xs text-slate-400">
                  Tag each prompt's themes — reuse is estimated from overlap with your committed
                  schools' prompt themes.
                </p>
                <div className="max-h-80 space-y-3 overflow-y-auto pr-1">
                  {entry.prompts.map((prompt, i) => (
                    <PromptEditor
                      key={i}
                      prompt={prompt}
                      onChangeText={(text) => onUpdatePromptText(i, text)}
                      onToggleTheme={(theme) => onTogglePromptTheme(i, theme)}
                      onRemove={() => onRemovePrompt(i)}
                    />
                  ))}
                  {entry.prompts.length === 0 && (
                    <p className="text-sm text-slate-400">No prompts yet — add one below.</p>
                  )}
                </div>
                <AddPromptForm onAdd={onAddPrompt} />
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

function PromptEditor({
  prompt,
  onChangeText,
  onToggleTheme,
  onRemove,
}: {
  prompt: Prompt
  onChangeText: (text: string) => void
  onToggleTheme: (theme: Theme) => void
  onRemove: () => void
}) {
  return (
    <div className="rounded-lg border border-slate-200 p-2 dark:border-slate-700">
      <div className="flex items-start gap-2">
        <textarea
          value={prompt.text}
          onChange={(e) => onChangeText(e.target.value)}
          rows={2}
          className={`${inputClass} resize-none`}
        />
        <button
          type="button"
          onClick={onRemove}
          className="shrink-0 rounded-lg px-1.5 py-1 text-xs text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950"
        >
          ✕
        </button>
      </div>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {THEME_OPTIONS.map((t) => {
          const active = prompt.themes.includes(t.value)
          return (
            <button
              key={t.value}
              type="button"
              title={t.hint}
              onClick={() => onToggleTheme(t.value)}
              className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${
                active
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700'
              }`}
            >
              {t.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function AddPromptForm({ onAdd }: { onAdd: (text: string) => void }) {
  return (
    <form
      className="mt-2 flex gap-2"
      onSubmit={(e) => {
        e.preventDefault()
        const form = e.currentTarget
        const input = form.elements.namedItem('prompt') as HTMLInputElement
        const text = input.value.trim()
        if (!text) return
        onAdd(text)
        input.value = ''
      }}
    >
      <input name="prompt" placeholder="Add a prompt…" className={inputClass} />
      <button
        type="submit"
        className="shrink-0 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500"
      >
        Add
      </button>
    </form>
  )
}

const inputClass =
  'w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100'

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">{label}</span>
      {children}
    </label>
  )
}
