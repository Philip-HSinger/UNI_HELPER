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
      <tr className="cursor-pointer border-b border-hairline hover:bg-accent-soft" onClick={onToggleExpand}>
        <td className="px-3 py-3">
          <div className="font-medium text-ink">{entry.name}</div>
          <div className="text-xs text-ink-muted">{entry.platform}</div>
        </td>
        <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">{entry.prompts.length}</td>
        <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">{wordCountSummary(entry.prompts)}</td>
        <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">{entry.difficulty}</td>
        <td className="px-3 py-3 font-mono text-sm tabular-nums text-ink">{entry.estimatedReuse}%</td>
        <td className="px-3 py-3">
          <span className="inline-flex items-center justify-center rounded-md border border-accent px-2 py-0.5 font-mono text-sm font-semibold tabular-nums text-accent">
            {entry.essayEffort}
          </span>
        </td>
      </tr>

      {expanded && (
        <tr className="border-b border-hairline bg-accent-soft">
          <td colSpan={6} className="px-4 py-4" onClick={(e) => e.stopPropagation()}>
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-muted">
              Supplemental prompts
            </h4>
            {entry.prompts.length === 0 ? (
              <p className="text-sm text-ink-muted">No prompts on file for this school yet.</p>
            ) : (
              <ul className="space-y-2">
                {entry.prompts.map((prompt) => (
                  <li
                    key={prompt.id}
                    className="flex items-start justify-between gap-4 rounded-md border border-hairline p-2 text-sm text-ink"
                  >
                    <span>{prompt.text}</span>
                    <span className="shrink-0 whitespace-nowrap font-mono text-xs text-ink-muted">
                      {prompt.wordLimit === null ? 'no stated limit' : `${prompt.wordLimit} words`}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-3 text-xs text-ink-muted">
              Difficulty and prompts are set by the site — estimated reuse (
              <span className="font-mono">{entry.estimatedReuse}%</span>) comes from the prompt-similarity
              database, scored against the prompts of schools you're applying to.
            </p>
          </td>
        </tr>
      )}
    </>
  )
}
