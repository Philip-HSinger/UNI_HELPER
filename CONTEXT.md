# Calliper: context briefing

Read this first. Last updated 2026-11-28.

## What Calliper is

Admissions analytics for college counselors (school-based counselors, independent counselors, essay coaches). Founder:
Philip Singer, a Brown freshman concentrating in electrical engineering. Contact address in use:
calliper@agentmail.to (temporary; see next steps). Delivery today is manual: a counselor sends one senior's scores
and list with no name, Philip runs the engine and sends back a PDF report.

Two things are being sold:

1. **Odds model with Bayesian updates.** Per-school admit odds calibrated to published data (SAT 25th/50th/75th
   percentiles and admit rates; ~400 schools from College Scorecard, Common Data Set for curated schools). One shared
   "application strength" factor links a student's decisions, so the real chance of zero admits is higher than
   multiplying odds suggests. After an early admit, deferral or rejection, every remaining school is re-priced with
   Bayes' rule. Results are shown as ranges.
2. **Essay-overlap map.** Which supplement prompts overlap across a student's list, which already-written essay
   covers which other prompt, how many new words each school really needs, and the best writing order. In the demo
   every prompt pair was scored by two independent scorers; the automatic similarity heuristic did not beat chance
   (p = 0.12), so only scored pairs are trusted.

## Current status

- Engine: `product/engine`, Python package `calliper` v0.1, research grade, 41 passing tests. Every accuracy claim
  was backtested on **simulated students only**; no real-outcome validation yet (see the methods manual).
- Sample report v3 (`product/demo/outputs/Calliper_report_v3_John_Smith.pdf`, 7 pages): a fictional student, "John
  Smith", SAT 1420, eight schools applied to (Early Decision Tufts) plus six he had not considered. Headline: a 40%
  chance of no admissions, which one added application brings to about 4%. Revised after an expert review and three
  persona reviews (`research/report_review/`).
- Outreach: 16 Rhode Island counselors and schools emailed on 2026-11-25. Two accepted meetings:
  - a private-school director of college counseling, proposed Thursday 2026-12-03,
  - an essay coach, proposed Tuesday 2026-12-08.
- No paying customers. Offer: free report now; free founding-counselor pilot this cycle in exchange for de-identified
  spring decisions; test prices after that of $390 per counselor per year and $1,500 per school or firm
  (`research/product_facts.md`).

## Timeline

| Date | What happened |
|---|---|
| 2026-08-22 | Built an unrelated student-facing web app (deleted 2026-11-28, recoverable from git history; its school-catalog sources are kept in `archive/catalog-sources/`) |
| 2026-11-23 | Built the engine (then called UNIMATH): odds model, Bayes updates, zero-admit risk, essay planner, backtests, significance tests, methods manual; 3-round simulated buyer/builder persuasion loop (`research/persuasion-loop/`); feature build spec and summary |
| 2026-11-23/24 | Simulated 36 buyer personas (`research/`). Calliper email v2: 7 of 36 opened, 4 agreed to a trial, 1 interested without commitment, 2 declined, 29 never opened (`research/results_v2.md`). Main blocker: unwillingness to send a stranger student data |
| 2026-11-24 | Product renamed Calliper in outreach; product plan, market analysis and overview PDF |
| 2026-11-25 | Email-sized overview PDF and 2-page technical note; emailed 16 Rhode Island counselors and schools |
| 2026-11-27 | Demo pipeline: prompts and Common Data Set figures collected and cross-checked, prompt pairs double-scored. Sample report v2 (10 schools), then v3 (John Smith) |
| 2026-11-28 | Expert and persona reviews of v3 (`research/report_review/`), fixes, final v3. Repository restructured into the current layout |

## Next steps

1. Prepare for and hold the two meetings (Dec 3, Dec 8); confirm the proposed times. Bring the v3 sample report.
2. Follow-up email to the Rhode Island contacts who have not replied, around 2026-12-02. In the simulation a
   follow-up that only repeats the ask got no response, so add something new.
3. One-page sample for cold email: a short version of the sample report that fits an attachment.
4. Providence lead batch: the next set of counselors and schools to contact.
5. Discovery feature: rank schools the student has not considered by how much they cut no-admit risk for how few new
   essay words (the "consider adding" section of the v3 report), as a product feature.
6. Real email domain: reviewers flagged the current address as looking temporary.
7. Backtest offer: score a counselor's past reach/target/likely calls against the model on last year's real outcomes
   (`calliper BKTST`). Caveat from the power analysis: one class is too small to prove either side better.

## Rules for working in this repo

- The repo is public. Never commit a real prospect's name, email address or other contact data; describe people by
  role. Lead records live outside the repo (`sales/leads/README.md`).
- Do not rewrite git history: sent emails contain raw GitHub links pinned to old commits.
- Verify before committing: `pytest` in `product/engine` and `product/demo/run_all.sh`; `outputs/odds.json` should not
  change unless the model or data changed on purpose.
- Personas in `research/` are fictional. Do not invent numbers; take them from the research and results files.

## Pipeline in progress: discovery panel + pitch sharpening (started 2026-11-28)

Resume from the first unchecked box; every stage commits its own output.

- [ ] 1. Data + scoring (one agent): 2026-27 prompts and CDS data for NYU, WashU, Tulane, Case Western into `product/demo/data/raw/` (prompts_<id>.json, stats_batch4.json); one-pass overlap scores of each new prompt against John's 14 planned essays into `product/demo/data/scores/discovery_scores.json`.
- [ ] 2. Compute (main session): chance per school (SAT bell-curve fit), new words needed given John's essays, risk of no admissions if added; ranking.
- [ ] 3. Report: "Schools worth a look" panel in the report v3 doc (claude.ai artifact E3kdBYvXXuHbw4DYP4XuKa) + PDF to `product/demo/outputs/`.
- [ ] 4. Pitch sharpening (one agent playing 4 personas: solo private counselor, essay-coaching business, private-school director, public-school counselor) -> `research/report_review/pitch_v4.md`. Conflicts: favour solo IECs and essay coaches, then private schools, then public schools and nonprofits; families last.
- [ ] 5. Apply the sharpened pitch to the report opening and `sales/` cold email.
