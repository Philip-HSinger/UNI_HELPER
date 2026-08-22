import type { EnrichedEntry } from '../types'

export function CommittedSchoolsPanel({ entries }: { entries: EnrichedEntry[] }) {
  const committed = entries.filter((e) => e.committed)

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h2 className="mb-1 text-sm font-semibold text-slate-900 dark:text-slate-100">Your committed schools</h2>
      <p className="mb-3 text-xs text-slate-400">
        Mark a school "Committed" (100% going, essays happening regardless) below. Every other
        school's essay reuse is estimated against these schools' prompts, using the
        prompt-similarity scores in the database — see the Difficulty page.
      </p>
      {committed.length === 0 ? (
        <p className="text-sm text-slate-400">No committed schools yet.</p>
      ) : (
        <ul className="space-y-1">
          {committed.map((e) => (
            <li key={e.id} className="flex items-center justify-between text-sm">
              <span className="font-medium text-slate-700 dark:text-slate-200">{e.name}</span>
              <span className="text-xs text-slate-400">
                {e.prompts.length} prompt{e.prompts.length === 1 ? '' : 's'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
