import type { EnrichedEntry, Prompt } from '../types'

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
}: {
  entry: EnrichedEntry
  expanded: boolean
  onToggleExpand: () => void
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
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Supplemental prompts</h4>
            {entry.prompts.length === 0 ? (
              <p className="text-sm text-slate-400">No prompts on file for this school yet.</p>
            ) : (
              <ul className="space-y-2">
                {entry.prompts.map((prompt) => (
                  <li
                    key={prompt.id}
                    className="flex items-start justify-between gap-4 rounded-lg border border-slate-200 p-2 text-sm text-slate-700 dark:border-slate-700 dark:text-slate-200"
                  >
                    <span>{prompt.text}</span>
                    <span className="shrink-0 whitespace-nowrap text-xs text-slate-400">
                      {prompt.wordLimit === null ? 'no stated limit' : `${prompt.wordLimit} words`}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-3 text-xs text-slate-400">
              Difficulty and prompts are set by the site — estimated reuse ({entry.estimatedReuse}%) comes from the
              prompt-similarity database, scored against the prompts of schools you're applying to.
            </p>
          </td>
        </tr>
      )}
    </>
  )
}
