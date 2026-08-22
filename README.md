# Application Efficiency Guide

A tool for college applicants across three pages:

- **Overview** — your SAT scores, which schools you're applying to, and a ranked list by
  **Efficiency Score** — the best admissions "return" per unit of essay-writing effort.
- **Likelihood of getting in** — each school's composite/English/Math score bands, your estimated
  percentile (via bell-curve interpolation against the published 25th/50th/75th band), how much
  that school actually weighs standardized testing, its acceptance rate, and a Reach/Match/Safety
  read. All read-only — this reference data is curated in Supabase, not editable in the app.
- **Difficulty of applying** — essay count, total word count, the actual prompts, a difficulty
  rating (set by the site, not the user), and estimated essay reuse from a real prompt-to-prompt
  similarity database.

Adding schools is search-only, from a fixed catalog — there's no "add a custom school" escape
hatch, since every school's percentiles/prompts/difficulty are meant to be curated data, not
something a visitor free-types in.

Ported from a personal Excel workbook (`guide.xlsx`) — see `src/lib/scoring.ts` for the formulas
and `src/lib/scoring.test.ts` for tests confirming they reproduce the original spreadsheet's numbers.

## Stack

Vite + React + TypeScript + Tailwind CSS v4, hosted on GitHub Pages, backed by **Supabase**
(hosted Postgres) for shared reference data. Your own working list — which schools you've added,
each one's application `status`, own scores — stays in `localStorage`, per browser; there's no
login yet (see "Adding accounts" below).

**How essay reuse is estimated:** set a school's status to "Applying" (or further along —
Submitted/Accepted/etc.) and its prompts become part of the reference set every other school is
compared against. `prompt_similarity` (a Supabase table) holds real, curated pairwise scores — e.g.
"MIT's intellectual-curiosity prompt overlaps 75% with Princeton's 'what excites you academically'
prompt." A candidate school's reuse % is the best match across the prompts of schools you're
applying to, averaged over its own prompts (see `estimateSchoolReuse` in `src/lib/scoring.ts`);
essay effort then discounts difficulty by that reuse — a 75% match still leaves 25% of the work,
never zero, unless a pair is actually scored 100.

## Backend (Supabase)

The school catalog and the prompt-similarity matrix live in Postgres, read by the app with
Supabase's public `anon` key (safe to ship in the built JS — access control is Row Level Security,
not secrecy of that key; see `supabase/schema.sql`). One-time setup for a fresh clone/fork:

1. Create a free project at [supabase.com](https://supabase.com).
2. In its SQL editor, run `supabase/schema.sql` (tables + RLS policies), then
   `supabase/seed.sql` (the 19 starter schools + their prompts, generated from
   `supabase/seed_source.schools.json` by `scripts/generate_seed_sql.py`).
3. From Project Settings → API, copy the **Project URL** and **anon public key** into a local
   `.env.local` (copy `.env.local.example`) for `npm run dev`, and into the GitHub repo's
   **Settings → Secrets and variables → Actions** (as `VITE_SUPABASE_URL` /
   `VITE_SUPABASE_ANON_KEY`) so the deploy workflow can build with them.
4. From then on, edit school data and fill in `prompt_similarity` scores directly in Supabase's
   table editor (a spreadsheet-like grid) — see `src/data/README.md`. No redeploy needed; the live
   site reads this at runtime.

## Getting started

```bash
npm install
npm run dev      # http://localhost:5173 — needs .env.local (see above) to actually load data
npm run test     # unit tests — pure functions only, no network/Supabase needed
npm run build    # production build to dist/
```

## Deploying: GitHub Pages, free

1. Push this repo to GitHub (public, for the free Pages tier).
2. Settings → Pages → Source: "GitHub Actions".
3. Add the two Supabase secrets (above) under Settings → Secrets and variables → Actions.
4. Push to `master` — `.github/workflows/deploy.yml` builds and publishes automatically to
   `https://<your-username>.github.io/<repo-name>/`.

That workflow also runs `npm run test` on every push, so a scoring-formula regression fails the
build instead of quietly shipping.

## Adding accounts / a paywall later

A backend already exists (Supabase), which gets you partway to monetising without more
infrastructure changes:

1. **Accounts**: [Supabase Auth](https://supabase.com/auth) can hold each user's own working list
   (today's `localStorage` `AppState`) server-side instead, so it follows them across devices.
2. **Paywall**: [Stripe](https://stripe.com) Checkout + a webhook needs actual server code — add
   Vercel serverless functions (`api/*.ts`, works alongside this Vite app with no migration) or
   Supabase Edge Functions. A sensible freemium split: free tier caps schools on a list (e.g. 5);
   paid tier unlocks unlimited schools, CSV/PDF export, and synced accounts.
3. **Smarter reuse estimation**: once there's a backend calling an LLM is easy — let paid users
   paste actual essay drafts and get a real similarity score per prompt instead of relying on the
   manually-curated matrix, or use it to help seed matrix scores faster.

## Project structure

```
supabase/
  schema.sql                    # table definitions + Row Level Security policies
  seed.sql                      # generated INSERT statements (run once per fresh project)
  seed_source.schools.json      # one-time seed source (not imported by the app)
scripts/
  generate_seed_sql.py          # regenerates seed.sql from seed_source.schools.json
src/
  lib/scoring.ts                # ported formulas + matrix-based reuse estimation (unit tested)
  lib/catalog.ts, similarity.ts # Supabase fetch + row-shaping (shaping is unit tested)
  lib/supabaseClient.ts         # the Supabase client (anon key from env)
  lib/defaults.ts               # blank/catalog-derived entry helpers
  lib/storage.ts                # localStorage persistence
  hooks/usePersistentState.ts, useReferenceData.ts, useHashRoute.ts, useSortedEntries.ts
  context/AppContext.tsx        # shared state + handlers for all three pages
  pages/                        # OverviewPage, LikelihoodPage, DifficultyPage
  components/                   # NavBar, per-page rows, add-school search, status badge, etc.
  types.ts                      # shared data model
```
