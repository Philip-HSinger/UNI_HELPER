# Calliper

Calliper is admissions analytics for college counselors. It gives each student's college list honest odds that
account for how decisions move together, updates every remaining school with Bayes' rule after an early result, and
maps which supplement essays overlap so a student writes fewer new words. It is built by Philip Singer, a Brown
freshman, and is in its first admissions cycle: research grade, validated on simulated students, no paying customers yet.

New here (person or AI agent)? Read [`CONTEXT.md`](CONTEXT.md) first.

## Folders

| Folder | What is in it |
|---|---|
| [`product/engine/`](product/engine/) | The Python package `calliper`: odds model, Bayesian updates, zero-admit risk, essay-reuse planner, backtests, terminal CLI, tests, catalog data, PDF builder scripts |
| [`product/demo/`](product/demo/) | End-to-end demo pipeline on 14 real schools for the fictional student John Smith; data, scripts and the current sample report (`outputs/Calliper_report_v3_John_Smith.pdf`) |
| [`product/reports/`](product/reports/) | Product documents: methods manual, technical note, feature build spec, product plan, one-page summary, market analysis |
| [`sales/`](sales/) | Outreach: overview PDFs, pitch-email drafts, data terms draft, what a lead record holds (no real contact data) |
| [`research/`](research/) | Market research: 36 simulated buyer personas, emails and transcripts, results, persuasion loop, persona and expert reviews of the sample report (`report_review/`) |
| [`archive/`](archive/) | Superseded documents, and the catalog source files kept from the deleted web app this repository started as |
| `CONTEXT.md`, `CHANGELOG.md` | Briefing for collaborators; dated history |

## Run the tests

```bash
cd product/engine
pip install -e ".[report,test]"
pytest                      # 41 tests, about 80 seconds
calliper CHNC -p examples/profile.toml    # try the terminal (type `calliper` alone for interactive mode)
```

## Run the demo pipeline

```bash
product/demo/run_all.sh     # rebuilds data/prompts.json, schools.json, similarity_pairs.csv and outputs/*.json
```

The script reruns the deterministic steps (merge, similarity matrix and essay plan, odds). It needs the engine on the
path, which `scripts/common.py` sets up (`ENGINE = product/engine`). The rebuilt `outputs/odds.json` should be
identical to the committed one.

## Versions

- Documents carry their version in the file name (`calliper-methods-manual-v1.pdf`). Bump the number when the
  content changes materially; older versions stay in git history or move to `archive/`.
- Sample report versions are annotated git tags, `report-v2` (10-school report) and `report-v3` (John Smith report).
  List them with `git tag -n`, and open one with e.g.
  `git show report-v3:10_demo/outputs/Calliper_report_v3_John_Smith.pdf > report-v3.pdf` (paths are as they were
  at the tagged commit).
- Files moved in November 2026 kept their history (`git log --follow <path>`). Raw GitHub links pinned to an older
  commit still work.
