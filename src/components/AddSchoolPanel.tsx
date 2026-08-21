import { useMemo, useState } from 'react'
import { CATALOG } from '../lib/defaults'

export function AddSchoolPanel({
  excludeCatalogIds,
  onAddFromCatalog,
  onAddBlank,
}: {
  excludeCatalogIds: Set<string>
  onAddFromCatalog: (catalogId: string) => void
  onAddBlank: () => void
}) {
  const [query, setQuery] = useState('')

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase()
    return CATALOG.filter((s) => !excludeCatalogIds.has(s.id))
      .filter((s) => (q ? s.name.toLowerCase().includes(q) : true))
      .slice(0, 8)
  }, [query, excludeCatalogIds])

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h2 className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">Add a school</h2>
      <div className="flex flex-wrap items-start gap-2">
        <div className="relative min-w-56 flex-1">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search the built-in list…"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          />
          {query && (
            <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-800">
              {matches.length === 0 && (
                <div className="px-3 py-2 text-sm text-slate-400">No matches — try "Add custom school" instead.</div>
              )}
              {matches.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => {
                    onAddFromCatalog(s.id)
                    setQuery('')
                  }}
                  className="block w-full px-3 py-2 text-left text-sm hover:bg-indigo-50 dark:text-slate-100 dark:hover:bg-indigo-950"
                >
                  {s.name}
                </button>
              ))}
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onAddBlank}
          className="shrink-0 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-medium text-indigo-700 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"
        >
          + Add custom school
        </button>
      </div>
    </div>
  )
}
