# Where the data actually lives now

This directory used to hold `schools.json` as the app's "database" — a git-committed file. That's
been replaced: the school catalog (percentiles, acceptance rate, importance, prompts) and the
prompt-similarity matrix now live in a real Supabase (Postgres) project, fetched at runtime by
`src/lib/catalog.ts` / `src/lib/similarity.ts`. See the root `README.md`'s "Backend (Supabase)"
section for setup, and `supabase/schema.sql` for the table definitions.

`schools.json` itself moved to `supabase/seed_source.schools.json` — it's now only a one-time seed
source for `scripts/generate_seed_sql.py`, not something the app imports.

## Updating school data each admissions cycle

Once a school's new Common Data Set is out, edit the row directly in Supabase's table editor (or
via SQL): update the percentile bands and acceptance rate, check whether `test_optional`/
`importance` changed, replace/add `prompts` rows once the new cycle's supplements are released
(usually over the summer), and fill in `us_news_rank` from that year's US News National
Universities list if you track it. No redeploy needed — the live site reads this at runtime.

`supabase/update_five_schools.sql` is a worked example of what a complete, current entry looks
like — MIT, Princeton, Stanford, Georgia Tech, and Purdue, researched from each school's own
admissions pages and recent Common Data Sets for the 2026-27 cycle (including Georgia Tech
dropping its supplement entirely, a real change that happened days before that cycle opened).
Use it as the template/reference when bringing another school up to the same standard.

## Filling in the prompt-similarity matrix

In the `prompt_similarity` table, each row is one scored pair: `prompt_a_id`, `prompt_b_id`,
`score` (0-100) — e.g. "MIT's intellectual-curiosity prompt overlaps 75% with Princeton's 'what
excites you academically' prompt." The table editor's grid shows the real `prompts.text` right
alongside (join on `prompt_a_id`/`prompt_b_id`), so there's no separate legend file to maintain.

One constraint to know: `prompt_a_id` must sort alphabetically before `prompt_b_id` (a check
constraint enforces this, so a pair can't accidentally be scored twice in conflicting directions)
— if an insert fails, swap the two IDs.
