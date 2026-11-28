# Changelog

Reconstructed from `git log` (dates in UTC), newest first. Paths are given as they were at the time.

## 2026-11-28

- Restructured the repository: `product/engine` (package renamed `unimath` -> `calliper`), `product/demo`,
  `product/reports`, `sales/`, `research/`, `archive/`; old web app deleted (kept only its catalog
  sources in `archive/catalog-sources/`); README, CONTEXT and CHANGELOG added.
- Tagged sample report versions `report-v2` and `report-v3`.
- Renamed demo report files with version numbers (v2 10-school, v3 John Smith).
- John Smith report: fixes from the expert and persona reviews; final PDF.
- Report review: persona feedback from p03, p09 and p17 (`market_research/report_review/`).

## 2026-11-27

- 10-school demo v2: John Smith report (PDF) per review comments.
- 10-school demo v2: new student list and candidate schools, exact essay planner, "consider adding" ranking; new
  prompts (Penn, Emory, Villanova, Rice), eligibility rules, split scoring, faster planner; Common Data Set figures;
  scorer and checker output, adjudication, verified data, final pipeline run.
- 10-school demo: final report (sample report v2) and annotated report (PDF), README, `run_all.sh`.
- Review fixes: non-ED rates, test-score send rule, ED binding, optimal writing order, December view, rubric
  direction; set A rescored with the corrected rubric.
- Similarity scores, matrix, essay plan, ED pricing; stats verification and odds outputs.
- Prompt corrections and wording decisions; verifier corrections; composite-only SAT fallback; trial run.
- Prompt data for URI, UMass, Holy Cross, Fairfield, Wesleyan, Fordham; CDS stats batches 1-2; student eligibility
  and optional-essay handling.
- Pipeline scripts, scoring rubric, first prompt data.

## 2026-11-25

- Overview PDF: Brown's "concentrating in" wording.
- Ignore local Claude settings.
- Technical note (2 pages, for outreach): equations, worked example, figure, limitations; author full name.
- Lightweight overview PDF for email attachments.

## 2026-11-24

- Founder introduced as a Brown freshman in electrical engineering.
- Overview PDF: no-real-student ask, few-days turnaround, postal address.
- Pitch simulation v2: Calliper email on 36 personas; fact sheet v2 with methods; overview PDF fixes.
- Market analysis and offer PDFs for the pitch simulation.
- 3-page product plan: how each feature works, benefit, build, test, sell.

## 2026-11-23

- One-page summary of the feature build spec.
- Internal feature build spec PDF (three features, two engines).
- Market research: personas, seller emails, prompts, manager preflight; simulation fact sheet and protocol.
- Rewrote READMEs: repo overview, full UNIMATH guide.
- Essay-reuse-led pitch email draft.
- Significance tests, claims register, College Scorecard coverage, persuasion loop (rounds 1-3).
- Added the UNIMATH statistical admissions toolkit with backtests and methods manual.

## 2026-08-22

- Old web app (Application Efficiency Guide, deleted 2026-11-28; see git history): initial commit; essay-bank sliders
  replaced by theme overlap; deploy workflow fixes; three pages with catalog and similarity matrix in Supabase;
  admin-only catalog fields; warm editorial redesign; score bands, tooltips, easy-wins panel; traffic-light status,
  US News rank, free-tier cap and waitlist.
