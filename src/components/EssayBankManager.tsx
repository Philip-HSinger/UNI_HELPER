import { useState } from 'react'
import type { EssayBank } from '../types'

export function EssayBankManager({
  banks,
  onAdd,
  onRename,
  onRemove,
}: {
  banks: EssayBank[]
  onAdd: (name: string) => void
  onRename: (id: string, name: string) => void
  onRemove: (id: string) => void
}) {
  const [draft, setDraft] = useState('')

  function submit() {
    const name = draft.trim()
    if (!name) return
    onAdd(name)
    setDraft('')
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h2 className="mb-1 text-sm font-semibold text-slate-900 dark:text-slate-100">Your essay banks</h2>
      <p className="mb-3 text-xs text-slate-400">
        Stories or drafts you've already written (a Common App essay, a personal statement, a
        "why this major" answer...). Rate how reusable each one is per school below.
      </p>
      <ul className="mb-3 space-y-2">
        {banks.map((bank) => (
          <li key={bank.id} className="flex items-center gap-2">
            <input
              value={bank.name}
              onChange={(e) => onRename(bank.id, e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
            />
            <button
              type="button"
              onClick={() => onRemove(bank.id)}
              className="shrink-0 rounded-lg px-2 py-1.5 text-xs text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950"
              aria-label={`Remove ${bank.name}`}
            >
              Remove
            </button>
          </li>
        ))}
        {banks.length === 0 && (
          <li className="text-sm text-slate-400">No essay banks yet — add one below.</li>
        )}
      </ul>
      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="e.g. Leadership story"
          className="w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
        />
        <button
          type="button"
          onClick={submit}
          className="shrink-0 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Add
        </button>
      </div>
    </div>
  )
}
