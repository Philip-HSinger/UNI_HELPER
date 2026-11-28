import type { EnrichedEntry } from '../types'
import { CARD_CLASS } from '../lib/uiStyles'

export function ApplyingSchoolsPanel({ entries }: { entries: EnrichedEntry[] }) {
  const applying = entries.filter((e) => e.status !== 'not_started')

  return (
    <div className={CARD_CLASS}>
      <h2 className="mb-1 text-sm font-semibold text-ink">Schools you're applying to</h2>
      <p className="mb-3 text-xs text-ink-muted">
        Set a school's status to "Applying" (or further along) below. Every other school's essay
        reuse is then estimated against these schools' prompts, using the prompt-similarity
        scores in the database — see the Difficulty page.
      </p>
      {applying.length === 0 ? (
        <p className="text-sm text-ink-muted">No schools marked as applying yet.</p>
      ) : (
        <ul className="space-y-1">
          {applying.map((e) => (
            <li key={e.id} className="flex items-center justify-between text-sm">
              <span className="font-medium text-ink">{e.name}</span>
              <span className="font-mono text-xs tabular-nums text-ink-muted">
                {e.prompts.length} prompt{e.prompts.length === 1 ? '' : 's'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
