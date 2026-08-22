import { useMemo, useState } from 'react'
import type { SchoolCatalogEntry } from '../types'
import { CARD_CLASS } from '../lib/uiStyles'
import { FREE_SCHOOL_LIMIT } from '../lib/limits'
import { joinWaitlist } from '../lib/waitlist'

function WaitlistForm() {
  const [email, setEmail] = useState('')
  const [state, setState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle')

  if (state === 'done') {
    return <p className="text-sm text-accent">You're on the list — we'll email you when it's ready.</p>
  }

  return (
    <form
      className="flex gap-2"
      onSubmit={async (e) => {
        e.preventDefault()
        setState('submitting')
        const { error } = await joinWaitlist(email)
        setState(error ? 'error' : 'done')
      }}
    >
      <input
        type="email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="you@email.com"
        className="w-full rounded-md border border-hairline bg-surface px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
      />
      <button
        type="submit"
        disabled={state === 'submitting'}
        className="shrink-0 rounded-md border border-accent px-3 py-2 text-sm font-medium text-accent hover:bg-accent-soft disabled:opacity-50"
      >
        Notify me
      </button>
      {state === 'error' && <p className="text-xs text-danger">Something went wrong — try again shortly.</p>}
    </form>
  )
}

export function AddSchoolPanel({
  catalog,
  excludeCatalogIds,
  onAddFromCatalog,
  atLimit,
}: {
  catalog: SchoolCatalogEntry[]
  excludeCatalogIds: Set<string>
  onAddFromCatalog: (catalogId: string) => void
  atLimit: boolean
}) {
  const [query, setQuery] = useState('')

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase()
    return catalog
      .filter((s) => !excludeCatalogIds.has(s.id))
      .filter((s) => (q ? s.name.toLowerCase().includes(q) : true))
      .slice(0, 8)
  }, [query, excludeCatalogIds, catalog])

  if (atLimit) {
    return (
      <div className={CARD_CLASS}>
        <h2 className="mb-1 text-sm font-semibold text-ink">Add a school</h2>
        <p className="mb-3 text-xs text-ink-muted">
          You've reached the free limit of {FREE_SCHOOL_LIMIT} schools. Leave your email and we'll let you know
          when unlimited premium lists are available.
        </p>
        <WaitlistForm />
      </div>
    )
  }

  return (
    <div className={CARD_CLASS}>
      <h2 className="mb-3 text-sm font-semibold text-ink">Add a school</h2>
      <div className="relative min-w-56">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search schools…"
          className="w-full rounded-md border border-hairline bg-surface px-3 py-2 text-sm text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
        {query && (
          <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-md border border-hairline bg-surface">
            {matches.length === 0 && (
              <div className="px-3 py-2 text-sm text-ink-muted">
                No matches — the school database only covers a set list; more schools get added over time.
              </div>
            )}
            {matches.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => {
                  onAddFromCatalog(s.id)
                  setQuery('')
                }}
                className="block w-full px-3 py-2 text-left text-sm text-ink hover:bg-accent-soft"
              >
                {s.name}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
