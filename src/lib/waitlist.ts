import { supabase } from './supabaseClient'

/** Writes an email into the `waitlist_emails` table (see supabase/schema.sql) — public INSERT-only
 * by RLS, so a visitor can join the list but nothing client-side can ever read it back. Signing up
 * twice with the same email hits the table's unique constraint, which is treated as success rather
 * than an error — "you're already on the list" is not a failure from the visitor's side. */
export async function joinWaitlist(email: string): Promise<{ error: string | null }> {
  const trimmed = email.trim().toLowerCase()
  if (!trimmed) return { error: 'Enter an email address.' }

  const { error } = await supabase.from('waitlist_emails').insert({ email: trimmed })
  if (error && error.code !== '23505') return { error: error.message }
  return { error: null }
}
