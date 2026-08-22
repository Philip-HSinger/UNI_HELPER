import { useEffect, useState } from 'react'
import { fetchCatalog } from '../lib/catalog'
import { fetchSimilarityMatrix } from '../lib/similarity'
import { isSupabaseConfigured } from '../lib/supabaseClient'
import type { SchoolCatalogEntry } from '../types'
import type { SimilarityMatrix } from '../lib/scoring'

interface ReferenceData {
  catalog: SchoolCatalogEntry[]
  matrix: SimilarityMatrix
  loading: boolean
  error: string | null
}

/** Fetches the school catalog and the prompt-similarity matrix once on mount, in parallel. */
export function useReferenceData(): ReferenceData {
  const [catalog, setCatalog] = useState<SchoolCatalogEntry[]>([])
  const [matrix, setMatrix] = useState<SimilarityMatrix>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    if (!isSupabaseConfigured) {
      setError('Supabase is not configured — see .env.local.example.')
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    Promise.all([fetchCatalog(), fetchSimilarityMatrix()])
      .then(([catalogResult, matrixResult]) => {
        if (cancelled) return
        setCatalog(catalogResult)
        setMatrix(matrixResult)
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setError(err instanceof Error ? err.message : 'Failed to load reference data.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return { catalog, matrix, loading, error }
}
