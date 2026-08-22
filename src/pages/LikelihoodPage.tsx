import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useAppContext } from '../context/AppContext'
import { useSortedEntries } from '../hooks/useSortedEntries'
import { LikelihoodRow } from '../components/LikelihoodRow'
import { CARD_CLASS, CARD_CLASS_FLUSH } from '../lib/uiStyles'
import type { EnrichedEntry } from '../types'

function InfoButton({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!open) return
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  return (
    <span ref={ref} className="relative inline-block align-middle">
      <button
        type="button"
        aria-label="What do these numbers mean?"
        onClick={() => setOpen((o) => !o)}
        className={`ml-1.5 inline-flex h-4 w-4 items-center justify-center rounded-full border text-[10px] font-semibold leading-none ${
          open ? 'border-accent text-accent' : 'border-ink-muted text-ink-muted hover:border-accent hover:text-accent'
        }`}
      >
        i
      </button>
      {open && (
        <div className="absolute left-0 top-full z-10 mt-2 w-72 rounded-md border border-hairline bg-surface p-3 text-xs leading-relaxed text-ink-muted">
          {children}
        </div>
      )}
    </span>
  )
}

// A hover/focus-only variant (vs. InfoButton's click-to-toggle above) for short, single-fact
// hints attached to a column header — no state needed, pure CSS via group-hover/focus-within.
function HoverInfo({ children }: { children: ReactNode }) {
  return (
    <span className="group relative ml-1 inline-flex normal-case" tabIndex={0}>
      <span className="inline-flex h-3.5 w-3.5 cursor-help items-center justify-center rounded-full border border-ink-muted text-[9px] font-semibold leading-none tracking-normal text-ink-muted group-hover:border-accent group-hover:text-accent group-focus-within:border-accent group-focus-within:text-accent">
        i
      </span>
      <span className="pointer-events-none absolute left-1/2 top-full z-10 hidden w-56 -translate-x-1/2 rounded-md border border-hairline bg-surface p-2 text-xs font-normal normal-case leading-relaxed tracking-normal text-ink-muted group-hover:block group-focus-within:block">
        {children}
      </span>
    </span>
  )
}

export function LikelihoodPage() {
  const { entries, ownScores } = useAppContext()
  const { sorted, sortKey, sortDir, toggleSort } = useSortedEntries<EnrichedEntry, keyof EnrichedEntry>(
    entries,
    'weightedAverage',
  )

  return (
    <div className="space-y-4">
      <div className={`${CARD_CLASS} flex items-center text-sm text-ink`}>
        <span className="font-mono font-medium tabular-nums">
          English {ownScores.english} · Math {ownScores.math}
        </span>
        <InfoButton>
          Percentiles are estimated from each school's published 25th/50th/75th score band via
          bell-curve interpolation. The weighted score then adjusts that for how much a school
          actually weighs standardized testing — a buff above the 50th percentile, a penalty below
          it, scaled by importance. Edit your scores on the Overview page.
        </InfoButton>
      </div>

      {entries.length === 0 ? (
        <div className={`${CARD_CLASS_FLUSH} border-dashed p-10 text-center text-sm text-ink-muted`}>
          No schools on your list yet — add one from the Overview page.
        </div>
      ) : (
        <div className={CARD_CLASS_FLUSH}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[920px] border-collapse text-left">
              <thead>
                <tr className="border-b border-hairline text-xs font-semibold uppercase tracking-wide text-ink-muted">
                  <th className="px-3 py-2">School</th>
                  <th className="px-3 py-2">Fit</th>
                  <th className="px-3 py-2">
                    English
                    <HoverInfo>
                      Your percentile is estimated via bell-curve interpolation against this
                      school's published 25th/50th/75th score band.
                    </HoverInfo>
                  </th>
                  <th className="px-3 py-2">
                    Math
                    <HoverInfo>
                      Your percentile is estimated via bell-curve interpolation against this
                      school's published 25th/50th/75th score band.
                    </HoverInfo>
                  </th>
                  <th
                    className="cursor-pointer select-none px-3 py-2 hover:text-ink"
                    onClick={() => toggleSort('weightedAverage')}
                  >
                    Weighted score{sortKey === 'weightedAverage' && (sortDir === 'asc' ? ' ▲' : ' ▼')}
                  </th>
                  <th className="px-3 py-2">Importance</th>
                  <th className="px-3 py-2">Raw acceptance rate</th>
                  <th className="px-3 py-2">Test rec.</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((entry) => (
                  <LikelihoodRow key={entry.id} entry={entry} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
