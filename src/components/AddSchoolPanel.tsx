import { useMemo, useState, type FormEvent } from 'react'
import type { SchoolCatalogEntry } from '../types'
import { CARD_CLASS } from '../lib/uiStyles'
import { FREE_SCHOOL_LIMIT } from '../lib/limits'
import { joinWaitlist } from '../lib/waitlist'

// Once someone closes the big banner, keep it closed for good (even across future visits, and
// future times they hit the cap again) — reopening it every time would get old fast.
const BANNER_DISMISSED_KEY = 'waitlist-banner-dismissed'

function readBannerDismissed(): boolean {
  try {
    return localStorage.getItem(BANNER_DISMISSED_KEY) === 'true'
  } catch {
    return false
  }
}

function WaitlistForm() {
  const [email, setEmail] = useState('')
  const [state, setState] = useState<'idle' | 'submitting' | 'done' | 'error'>('idle')
  const [expanded, setExpanded] = useState(() => !readBannerDismissed())

  const dismiss = () => {
    setExpanded(false)
    try {
      localStorage.setItem(BANNER_DISMISSED_KEY, 'true')
    } catch {
      // Private browsing / storage disabled — just collapse for this visit instead.
    }
  }

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setState('submitting')
    const { error } = await joinWaitlist(email)
    setState(error ? 'error' : 'done')
  }

  const errorNote = state === 'error' && (
    <p className="mt-2 text-xs text-danger">Something went wrong — try again shortly.</p>
  )

  // Collapsed: the small inline form this used to always be.
  if (!expanded) {
    return (
      <div className={CARD_CLASS}>
        <h2 className="mb-1 text-sm font-semibold text-ink">Add a school</h2>
        <p className="mb-3 text-xs text-ink-muted">You've reached the free limit of {FREE_SCHOOL_LIMIT} schools.</p>
        {state === 'done' ? (
          <p className="text-sm text-accent">You're on the list — we'll email you when it's ready.</p>
        ) : (
          <form className="flex gap-2" onSubmit={submit}>
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
          </form>
        )}
        {errorNote}
      </div>
    )
  }

  // Expanded: a big banner across the page, until they close it.
  return (
    <div className="relative overflow-hidden rounded-lg border-2 border-accent bg-accent-soft px-6 py-10 text-center sm:px-12">
      <button
        type="button"
        onClick={dismiss}
        aria-label="Dismiss"
        className="absolute right-3 top-3 rounded-md px-2 py-1 text-lg leading-none text-ink-muted hover:bg-surface hover:text-ink"
      >
        ✕
      </button>
      <h2 className="font-display text-2xl font-semibold text-ink sm:text-3xl">Unlimited lists are on the way</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-ink-muted">
        You've reached the free limit of {FREE_SCHOOL_LIMIT} schools. Leave your email and we'll let you know the
        moment premium is ready.
      </p>
      {state === 'done' ? (
        <p className="mt-5 text-sm font-medium text-accent">You're on the list — we'll email you when it's ready.</p>
      ) : (
        <form onSubmit={submit} className="mx-auto mt-5 flex max-w-sm gap-2">
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
            className="shrink-0 rounded-md border border-accent bg-accent px-4 py-2 text-sm font-medium text-paper hover:opacity-90 disabled:opacity-50"
          >
            Notify me
          </button>
        </form>
      )}
      {errorNote}
    </div>
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
    return <WaitlistForm />
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
