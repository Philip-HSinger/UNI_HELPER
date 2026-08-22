import { useMemo, useState } from 'react'
import type { SchoolCatalogEntry } from '../types'
import { CARD_CLASS } from '../lib/uiStyles'

export function AddSchoolPanel({
  catalog,
  excludeCatalogIds,
  onAddFromCatalog,
}: {
  catalog: SchoolCatalogEntry[]
  excludeCatalogIds: Set<string>
  onAddFromCatalog: (catalogId: string) => void
}) {
  const [query, setQuery] = useState('')

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase()
    return catalog
      .filter((s) => !excludeCatalogIds.has(s.id))
      .filter((s) => (q ? s.name.toLowerCase().includes(q) : true))
      .slice(0, 8)
  }, [query, excludeCatalogIds, catalog])

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
