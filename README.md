# Application Efficiency Guide

A tool for college applicants to see, for every school on their list: their estimated percentile
against that school's SAT bands, whether submitting test scores helps or hurts them, and — the
core feature — an **Efficiency Score** ranking which supplements give the best admissions "return"
for the essay-writing effort they demand, after crediting reuse estimated from the schools you've
already committed to (100% going regardless of outcome).

Ported from a personal Excel workbook (`guide.xlsx`) into a standalone web app anyone can use with
their own scores. See `src/lib/scoring.ts` for the formulas and `src/lib/scoring.test.ts` for tests
confirming they reproduce the original spreadsheet's numbers.

## Stack

Vite + React + TypeScript + Tailwind CSS v4. All user data (own scores, the working school list,
prompt theme tags, application status) lives only in the browser via `localStorage` — there is no
backend in v1. The school reference data (percentile bands, prompts, acceptance rates) ships in
`src/data/schools.json`, versioned in git — see `src/data/README.md` for how to update it every
admissions cycle.

**How essay reuse is estimated:** mark a school "Committed" (100% going regardless of outcome) and
tag its prompts with themes (`src/lib/themes.ts` — "why this major", "identity/community",
"challenge/adversity", etc.). Every other school's reuse % comes from how much its own
(similarly-tagged) prompts overlap in theme with your committed schools' prompts — see
`estimateSchoolReuse` in `src/lib/scoring.ts`. This replaces a literal prompt-by-prompt similarity
matrix (which doesn't generalize past a fixed set of pre-scored schools) with something that works
for any school or custom prompt a user adds, at the cost of needing prompts tagged to be useful.
The catalog ships with prompts untagged; tagging them is a manual (or later, LLM-assisted) step.

## Getting started

```bash
npm install
npm run dev      # http://localhost:5173
npm run test     # scoring engine unit tests
npm run build    # production build to dist/
```

## Deploying (now): GitHub Pages, free

1. Push this repo to GitHub.
2. In the repo's Settings → Pages, set **Source** to "GitHub Actions".
3. Push to `main` — `.github/workflows/deploy.yml` builds and publishes automatically to
   `https://<your-username>.github.io/<repo-name>/`.

That workflow also runs `npm run test` on every push, so a scoring-formula regression fails the
build instead of quietly shipping.

## Upgrading to monetise it later

GitHub Pages only serves static files — no accounts, no payments, no server-side database are
possible there. When you're ready to monetise, the same codebase moves without a rewrite:

1. **Host on [Vercel](https://vercel.com) instead** (or alongside — Pages can stay as a free
   marketing/demo instance). Vercel auto-detects this Vite project; connecting the GitHub repo is
   the entire setup.
2. **Add a backend** via Vercel serverless functions (`api/*.ts` — works with any frontend
   framework, no migration off Vite/React required).
3. **Add accounts**, so a user's list follows them across devices instead of living in one
   browser's `localStorage` — e.g. [Clerk](https://clerk.com) or [Supabase Auth](https://supabase.com/auth)
   for the login flow, with the `AppState` shape in `src/types.ts` persisted server-side (Supabase/
   Postgres is a natural fit) instead of (or in addition to) `localStorage`.
4. **Add a paywall** with [Stripe](https://stripe.com) (Checkout + a webhook `api/` route). A
   sensible freemium split: free tier caps the number of schools on a list (e.g. 5); paid tier
   unlocks unlimited schools, CSV/PDF export, and synced accounts.
5. **Upgrade reuse estimation with an LLM**, once there's a backend to call one from: let paid
   users paste actual essay drafts and prompts and get a real similarity/reuse score per prompt
   instead of (or blended with) the free tag-overlap heuristic — a natural, clearly-better paid
   feature rather than an arbitrary tier cutoff.
6. Keep `src/data/schools.json` as the shared catalog either way — it's reference data, not user
   data, so it doesn't need to move into the per-user database.

## Project structure

```
src/
  data/schools.json      # the school reference "database" (~19 pre-seeded schools)
  data/README.md         # how to update it each admissions cycle
  lib/scoring.ts         # the ported formulas + theme-overlap reuse estimation (unit tested)
  lib/themes.ts          # the fixed prompt-theme vocabulary
  lib/defaults.ts        # catalog access + initial-state helpers
  lib/storage.ts         # localStorage persistence
  hooks/usePersistentState.ts
  components/            # UI: score input, theme coverage, school table/row, add-school, summary
  types.ts               # shared data model
```
