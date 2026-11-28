import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined

export const isSupabaseConfigured = Boolean(url && anonKey)

if (!isSupabaseConfigured) {
  // Expected during local dev before .env.local is set up, or if a fork skips Supabase entirely.
  // Callers (useReferenceData) surface this as a friendly "not configured" state, not a crash.
  console.warn(
    'Supabase is not configured — set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY (see .env.local.example).',
  )
}

// Safe to embed: this is the public `anon` key, meant to ship in a client bundle. Access control
// is enforced by the Row Level Security policies in supabase/schema.sql, not by hiding this key.
export const supabase = createClient(url ?? 'https://placeholder.supabase.co', anonKey ?? 'placeholder')
