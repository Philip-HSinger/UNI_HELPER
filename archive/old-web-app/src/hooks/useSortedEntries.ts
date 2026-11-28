import { useMemo, useState } from 'react'

/** Generic click-to-sort-a-column state, reused by each page's table. */
export function useSortedEntries<T, K extends keyof T>(entries: T[], initialKey: K, initialDir: 'asc' | 'desc' = 'desc') {
  const [sortKey, setSortKey] = useState<K>(initialKey)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initialDir)

  const sorted = useMemo(() => {
    const copy = [...entries]
    copy.sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      const cmp = typeof av === 'string' ? av.localeCompare(bv as string) : (av as number) - (bv as number)
      return sortDir === 'asc' ? cmp : -cmp
    })
    return copy
  }, [entries, sortKey, sortDir])

  function toggleSort(key: K) {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  return { sorted, sortKey, sortDir, toggleSort }
}
