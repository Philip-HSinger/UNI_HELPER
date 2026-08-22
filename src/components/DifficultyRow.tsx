import type { EnrichedEntry, Prompt, SchoolEntry } from '../types'
import { Field, inputClass } from './FormField'

function wordCountSummary(prompts: Prompt[]): string {
  const known = prompts.filter((p) => p.wordLimit !== null)
  const total = known.reduce((sum, p) => sum + (p.wordLimit ?? 0), 0)
  const unknownCount = prompts.length - known.length
  if (prompts.length === 0) return '—'
  if (unknownCount === 0) return `${total.toLocaleString()} words`
  return `${total.toLocaleString()}+ words (${unknownCount} prompt${unknownCount === 1 ? '' : 's'} unstated)`
}

export function DifficultyRow({
  entry,
  expanded,
  onToggleExpand,
  onUpdate,
  onAddPrompt,
  onUpdatePromptText,
  onUpdatePromptWordLimit,
  onRemovePrompt,
}: {
  entry: EnrichedEntry
  expanded: boolean
  onToggleExpand: () => void
  onUpdate: (partial: Partial<SchoolEntry>) => void
  onAddPrompt: (text: string) => void
  onUpdatePromptText: (index: number, text: string) => void
  onUpdatePromptWordLimit: (index: number, wordLimit: number | null) => void
  onRemovePrompt: (index: number) => void
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
        <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.prompts.length}</td>
        <td className="px-3 py-3 text-sm text-slate-600 dark:text-slate-300">{wordCountSummary(entry.prompts)}</td>
        <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.difficulty}</td>
        <td className="px-3 py-3 text-sm tabular-nums text-slate-600 dark:text-slate-300">{entry.estimatedReuse}%</td>
        <td className="px-3 py-3 text-sm font-semibold tabular-nums text-indigo-600 dark:text-indigo-400">
          {entry.essayEffort}
        </td>
      </tr>

      {expanded && (
        <tr className="border-b border-slate-100 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-800/30">
          <td colSpan={6} className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div>
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
                <p className="mt-3 text-xs text-slate-400">
                  Estimated reuse ({entry.estimatedReuse}%) comes from the prompt-similarity
                  database, scored against your committed schools' prompts — it isn't editable
                  here.
                </p>
              </div>

              <div className="md:col-span-2">
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Supplemental prompts
                </h4>
                <div className="max-h-80 space-y-2 overflow-y-auto pr-1">
                  {entry.prompts.map((prompt, i) => (
                    <div key={prompt.id} className="rounded-lg border border-slate-200 p-2 dark:border-slate-700">
                      <div className="flex items-start gap-2">
                        <textarea
                          value={prompt.text}
                          onChange={(e) => onUpdatePromptText(i, e.target.value)}
                          rows={2}
                          className={`${inputClass} resize-none`}
                        />
                        <div className="w-20 shrink-0">
                          <input
                            type="number"
                            min={0}
                            placeholder="words"
                            value={prompt.wordLimit ?? ''}
                            onChange={(e) =>
                              onUpdatePromptWordLimit(i, e.target.value === '' ? null : Number(e.target.value))
                            }
                            className={inputClass}
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => onRemovePrompt(i)}
                          className="shrink-0 rounded-lg px-1.5 py-1 text-xs text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ))}
                  {entry.prompts.length === 0 && <p className="text-sm text-slate-400">No prompts yet — add one below.</p>}
                </div>
                <form
                  className="mt-2 flex gap-2"
                  onSubmit={(e) => {
                    e.preventDefault()
                    const form = e.currentTarget
                    const input = form.elements.namedItem('prompt') as HTMLInputElement
                    const text = input.value.trim()
                    if (!text) return
                    onAddPrompt(text)
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
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
