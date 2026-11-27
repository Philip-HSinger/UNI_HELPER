# 10-school demo

A complete run of the Calliper pipeline on ten schools from Providence Country Day's acceptance list, for one example
student (SAT 1420, domestic arts-and-sciences applicant, Early Decision to Tufts).

## Outputs

- `outputs/Calliper_sample_report.pdf`: the report to bring to meetings (6 pages)
- `outputs/Calliper_sample_report_annotated.pdf`: how every number was derived (10 pages)
- `outputs/odds.json`, `outputs/essay_plan.json`, `outputs/school_matrix.json`: the numbers behind them
- `data/similarity_pairs.csv`: every directed prompt pair, both scores, length cap and reuse share

## Pipeline

| Step | Who | Output |
| --- | --- | --- |
| 1. Collect 2026-27 prompts word for word | 5 agents, 2 schools each | `data/raw/prompts_*.json` |
| 2. Collect Common Data Set figures | 2 agents, 5 schools each | `data/raw/stats_batch*.json` |
| 3. Re-check prompts and figures against sources | 2 independent agents | `data/verify/*_check.json` |
| 4. Merge, apply corrections and recorded decisions | `scripts/s1_merge.py` | `data/prompts.json`, `data/schools.json` |
| 5. Score every cross-school prompt pair, both directions | 2 independent agents, `scripts/rubric.md` | `data/scores/scorer_A.json`, `scorer_B.json` |
| 6. Agreement, length cap, matrix, best writing order | `scripts/s3_matrix.py` | `essay_plan.json`, `similarity_pairs.csv` |
| 7. Odds and Bayesian updates after Early Decision | `scripts/s4_odds.py` (toolkit `AdmissionModel`) | `odds.json` |
| 8. Audit everything | independent reviewer agent | `data/verify/pipeline_review.md` |

Steps 4, 6 and 7 rerun with `./run_all.sh`. The example student's eligibility (which prompts apply) and the optional
essays they write are set in `scripts/common.py`.

## Demo-level assumptions (documented in the annotated report)

- Early Decision school priced halfway, on the log-odds scale, between its overall and ED admit rates.
- Other schools priced at their non-ED admit rate; Early Action rates are not published, so the same rate is used.
- SAT sent at a test-optional school only if at or above its 25th percentile.
- Reuse share = mean content score x min(1, source word limit / needed word limit).
- First-round scores (before the rubric's direction fix) are kept in `data/scores/v1/`.
