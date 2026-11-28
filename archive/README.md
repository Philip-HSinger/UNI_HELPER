# Archive

Superseded material, kept for history. Nothing here is part of the current Calliper product.

- `superseded/`: the UNIMATH-era offer PDF (replaced by `sales/calliper-overview-v1.pdf`) and the v2 10-school sample
  report with its annotated derivations (replaced by v3, `product/demo/outputs/Calliper_report_v3_John_Smith.pdf`).
- `catalog-sources/`: the only part kept from *Application Efficiency Guide*, the unrelated student-facing
  React + Supabase web app this repository started as (August 2026; deleted 2026-11-28, recoverable from git history,
  e.g. `git show 6edac0c:src/App.tsx`). `supabase/seed_source.schools.json` (19 curated schools with prompts),
  `supabase/update_five_schools.sql` (researched 2026-27 corrections and the first scored prompt pairs) and
  `scripts/generate_seed_sql.py` (prompt-id slug scheme) are what `product/engine/scripts/build_catalog.py` reads to
  rebuild the engine's catalog.
