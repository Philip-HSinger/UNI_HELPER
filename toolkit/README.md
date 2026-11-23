# UNIMATH: admissions analytics terminal

A Bloomberg-style terminal and Python library for college-admissions statistics. It turns published
admissions data (Common Data Set score bands, acceptance rates, supplement prompts) into calibrated,
*correlated* admission probabilities, updates them by Bayes' rule as decisions arrive, plans essay
reuse, and optimizes the application list.

**Read [`reports/UNIMATH_methods_manual.pdf`](reports/UNIMATH_methods_manual.pdf).** It covers every
feature, the technique behind it, the backtests and their results (including what failed), and the
market and positioning analysis.

```bash
pip install -e ".[report,test]"        # numpy + scipy; matplotlib/reportlab only for the manual
unimath                                 # interactive terminal; type HELP
unimath CHNC -p examples/profile.toml   # one-shot
unimath BRIEF -p examples/profile.toml  # plain-English family brief
unimath CHNC -p examples/profile.toml --json
```

| Code | Function |
|---|---|
| `PCTL` | score percentiles: two-piece normal matched to 25/50/75, 800-ceiling censoring, SEM interval, copula composite |
| `CHNC` | P(admit): probit selection model calibrated per school by truncated-normal moment inversion |
| `XADM` | cross-admit matrix: P(B \| admitted/rejected at A) |
| `DEC` / `UPDT` | record decisions; grid-Bayesian posterior re-prices every remaining school |
| `PORT` | distribution of number of admits; P(≥1) vs the naive independence formula |
| `ESSY` / `FREE` | essay coverage matrix, clusters, near-free schools given your list |
| `PLAN` | list optimizer: E[utility of best admit] − λ·words, exact or greedy+swap |
| `SENS` | sensitivity of every answer to every assumption |
| `FIT` | maximum-marginal-likelihood refit on your own outcomes CSV + held-out Brier/log loss/AUC/ECE |
| `LEDGER` / `SCORE` | freeze forecasts in a SHA-256 hash chain; grade them when decisions arrive |
| `BRIEF` | plain-English summary for families |
| `SCH` / `DQ` / `CAT` | school calibration page, data-quality report, catalog |

## Layout

```
unimath/scores.py      band fitting, percentiles, composite
unimath/model.py       calibrated selection model, shared factor, Bayes updates, portfolio
unimath/similarity.py  prompt reuse, coverage matrix, marginal effort, clustering
unimath/planner.py     list optimizer
unimath/fit.py         outcomes I/O, marginal likelihood, MLE, scoring rules, simulator
unimath/backtest.py    validation experiments E1-E6 + sensitivity
unimath/cli.py         the terminal
data/catalog.json      built from ../supabase sources by scripts/build_catalog.py
data/similarity.csv    curated prompt-pair scores (same table as Supabase prompt_similarity)
scripts/               build_catalog, run_backtests, make_figures, make_report
```

Rebuild everything: `python scripts/build_catalog.py && pytest tests && python scripts/run_backtests.py
&& python scripts/make_figures.py && python scripts/make_report.py`.

Every number in the validation section is synthetic until real outcomes are loaded with `FIT` or `SCORE`.
