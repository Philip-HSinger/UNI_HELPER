# UNIMATH: admissions analytics terminal

UNIMATH is a terminal and Python library for college-admissions statistics, built for independent college counselors
and for quantitatively minded families. It takes published admissions data (each school's SAT bands and acceptance
rate, and its supplement prompts) plus the counselor's own read of a student, and produces:

- **odds per school** that account for how decisions move together (the same application is read everywhere, so a
  list of reaches is riskier than multiplying each school's odds suggests),
- **updated odds** for every remaining school after each early result, deferral or waitlist,
- **a zero-admit risk check** for a single list or a whole caseload, shown as a range rather than false precision,
- **an essay plan**: which supplements overlap, which schools are nearly free given the rest of the list, and what
  order to write them in,
- **plain-English briefs**, one for the counselor (with numbers) and one for families (in words).

It runs locally, needs no student names, and looks like a Bloomberg terminal: short function codes, dense amber
tables.

> **Status: v0.1, research grade.** The statistics are implemented and unit tested, and every accuracy claim was
> backtested, but **only on simulated students**. No real outcome data has been used yet. The essay-similarity
> heuristic did **not** beat chance in its test; only human-scored prompt pairs should be trusted. The full story,
> including what failed, is in **[`reports/UNIMATH_methods_manual.pdf`](reports/UNIMATH_methods_manual.pdf)**.

## Quick start

```bash
cd toolkit
pip install -e ".[report,test]"      # numpy + scipy; matplotlib/reportlab only for the manual
unimath                               # interactive terminal; type HELP, Q to quit
```

One-shot commands (scriptable, `--json` for machine-readable output):

```bash
unimath CHNC  -p examples/profile.toml          # odds for the schools in a student profile
unimath PORT  -p examples/profile.toml          # chance of 0, 1, 2... admits; zero-admit risk range
unimath BRIEF -p examples/profile.toml          # counselor brief; add "family" for the words-only version
unimath ROSTER examples/caseload_demo.csv       # screen a whole caseload at once
unimath BKTST  examples/past_class_demo.csv     # your past reach/target/likely calls vs UNIMATH
unimath CHNC  -p examples/profile.toml --json
```

## Commands

| Code | What you get | Technique |
|---|---|---|
| `PCTL` | Where a score sits at each school, with a test-day error range | Two-piece normal matched exactly to the published 25/50/75; 800-ceiling censoring; mid-rank; Gaussian-copula composite |
| `CHNC` | P(admit) per school, 80% band, submit/withhold call for test-optional schools | Probit selection model calibrated per school by inverting truncated-normal moments; lapse mixture |
| `XADM` | "If admitted (or rejected) at A, the odds at B become..." | Shared latent factor; exact 801-point grid integration |
| `DEC` / `UPDT` | Record a real decision; every remaining school is re-priced | Grid Bayesian posterior; ordered-probit waitlist band |
| `PORT` | Distribution of the number of admits; zero-admit risk range | Poisson-binomial mixed over the shared factor; range across link strengths |
| `ROSTER` | Whole caseload: no-admit risk and likely count per student, with flags | Batch PORT/CHNC |
| `BRIEF [family]` | Counselor brief (numbers) or family brief (low/moderate/high, no percentages) | Templated summary |
| `ESSY` / `FREE` | Essay coverage matrix, clusters, near-free schools given the list | Theme × TF-IDF × length heuristic, overridden by human scores (heuristic unvalidated) |
| `PLAN` | Best list for the student's preferences and writing budget | E[utility of best admit] − λ·words; exact search ≤12 candidates, else greedy + swap |
| `ED` | Use a school's early-round admit rate (from its Common Data Set) | Recalibration with the round-specific base rate (approximation) |
| `SENS` | How much each answer depends on each assumption | One-at-a-time perturbation (tornado) |
| `FIT` | Refit the model on a practice's own outcomes, with held-out accuracy | Maximum marginal likelihood; Brier, log loss, AUC, calibration error |
| `BKTST` | Score a counselor's past calls against UNIMATH on real outcomes | Label → rate conversion; student-cluster bootstrap CI (see power caveat below) |
| `LEDGER` / `SCORE` | Freeze forecasts now, grade them when decisions arrive | SHA-256 hash chain (tamper-evident); proper scoring rules |
| `SCH` / `DQ` / `CAT` | School calibration page, data-quality report, catalog listing | |
| `SAT` `HOL` `LIST` `UTIL` `SIM` | Session setup; synthetic outcomes for demos | |

## Input files

| File | Used by | Columns / fields |
|---|---|---|
| Student profile (`examples/profile.toml`) | most commands, `-p` | `[student]` sat_ebrw, sat_math, optional holistic_pct (counselor's 0-100 rating); `[[schools]]` id, utility, optional decision |
| Caseload CSV (`examples/caseload_demo.csv`) | `ROSTER` | student_id, ebrw, math, holistic_pct, schools (`;`-separated ids) |
| Past class CSV (`examples/past_class_demo.csv`) | `BKTST` | student_id, school_id, ebrw, math, decision, counselor_call (reach/target/likely) |
| Outcomes CSV | `FIT` | student_id, school_id, ebrw, math, decision, optional holistic_pct, submitted |

Decisions are `accepted`, `rejected`, `waitlisted` or `deferred`. School ids are listed by `CAT`.

## Data

`data/catalog.json` holds 412 four-year schools:

- **19 hand-curated schools** with real supplement prompts, built from `../supabase/seed_source.schools.json` and
  the researched 2026-27 corrections in `../supabase/update_five_schools.sql`.
- **393 schools from the US Department of Education's College Scorecard** (SAT quartiles and admission rate). Their
  "test importance" is a proxy from Scorecard's test-requirement code, and their supplements are placeholders
  (assumed one 250-word essay). `DQ` flags all of this.

`data/similarity.csv` holds the human-scored prompt pairs (same table as the web app's Supabase
`prompt_similarity`). Human scores always override the heuristic.

Refresh: `python scripts/fetch_scorecard.py` (resumable; the free DEMO_KEY allows ~10 requests/hour, or set
`SCORECARD_API_KEY`), then `python scripts/build_catalog.py`.

## Validation: is it better than chance?

Every claim is stated in math and in plain English, with confidence intervals and p-values, in Section B of the
manual. Summary (claims 2-6 and 10 tested on simulated students only):

| # | Claim | Result |
|---|---|---|
| 1 | Percentile curve beats a plain bell curve | Yes, small: 0.95 percentile points (95% CI 0.83-1.08), p < 0.001 |
| 2 | Odds beat quoting the acceptance rate | Yes: 20-33% lower error |
| 3 | Odds beat a simple logistic model | Yes, small: 7-8% lower error, significant in all 5 simulated worlds |
| 4 | A student's other decisions sharpen the rest | Yes, largest effect: 18-24% lower error |
| 5 | Multiplying odds understates zero-admit risk | Yes: 4.5-8x too optimistic; UNIMATH can over-warn ~2x when its assumptions fail |
| 6 | Settings are learnable from outcomes | Partly: one setting biased; error bars cover 65-75%, not 95% |
| 7 | Essay heuristic matches human scores | **No** (p = 0.12) |
| 8 | List optimizer finds the optimum | Yes: 30 of 30 |
| 9 | Beats existing tools on real students | **Untested** |
| 10 | Beats a counselor's own calls on one class | **No:** scores-only loses; with the counselor's rating it wins barely; 25 students can't show either |

## Reproducing everything

```bash
python scripts/build_catalog.py      # catalog from repo sources (+ cached Scorecard data)
pytest tests                         # 41 tests: formulas, calibration by simulation, CLI smoke tests
python scripts/run_backtests.py      # E1-E6 -> reports/backtest_results.json
python scripts/run_significance.py   # multi-seed tests, 20-rep recovery -> reports/significance.json (~15 min)
python scripts/run_power.py          # backtest power analysis -> reports/power.json
python scripts/make_figures.py && python scripts/make_report.py   # -> reports/UNIMATH_methods_manual.pdf
```

Backtests use the 19 curated schools so results stay comparable across versions.

## Layout

```
unimath/
  scores.py        band fitting, percentiles, composite distribution
  model.py         calibrated selection model, shared factor, Bayes updates, portfolio, risk ranges
  similarity.py    prompt reuse, coverage matrix, marginal effort, clustering
  planner.py       list optimizer
  fit.py           outcomes I/O, marginal likelihood, MLE, scoring rules, simulator
  backtest.py      validation experiments E1-E7 and sensitivity
  significance.py  cluster bootstrap, exact/permutation tests, Wilson/Clopper-Pearson intervals
  catalog.py       catalog loading and data-quality rules
  cli.py           the terminal
data/              catalog.json, similarity.csv, scorecard_raw.json (cached API download)
examples/          sample profile, caseload and past-class files
scripts/           data build, backtests, significance, power, figures, manual
tests/             pytest suite
reports/           methods manual (PDF), figures, results JSON, business documents (below)
```

## Business documents (drafts)

- `reports/pitch_email_v3.md`: counselor pitch led by essay planning. **Don't send it until:**
  1. the prompt-pair matrix is human-scored for the schools it names ([N] in the email),
  2. the similarity test (E5) is re-run on held-out human scores and beats a constant guess,
  3. the worked example is replaced with real numbers from 2-3 students' actual writing,
  4. the founder, company, price and contributor-benefit placeholders are filled in.
- `reports/pitch_email.md`, `reports/pitch_email_v2.md`: earlier versions, kept for comparison.
- `reports/DATA_TERMS_DRAFT.md`: data terms draft, for review with a lawyer.
- `reports/loop/`: the buyer/builder persuasion loop (each round's pitch, manual snapshot and verdicts), summarized in
  Section C of the manual.

## Known limitations

- No real-outcome validation yet; the first priority is running `FIT`/`BKTST` on real past classes and freezing
  forecasts with `LEDGER` this cycle.
- Essay similarity needs a larger human-scored matrix (target: the 50-100 most-applied schools) before it can be
  sold; the heuristic is a conservative fallback only.
- Early-decision/early-action rounds are approximated (`ED`), not modelled.
- Non-test strength enters only through the counselor's single 0-100 rating.
