#!/usr/bin/env bash
# Rebuild every number in the 10-school demo from the collected data.
# Research and scoring are done by agents (see README); this reruns the deterministic steps.
set -euo pipefail
cd "$(dirname "$0")/scripts"
python3 s1_merge.py      # raw + verified data -> data/prompts.json, data/schools.json, data/scores/pairs.json
python3 s3_matrix.py     # two scorers -> similarity_pairs.csv, school_matrix.json, essay_plan.json
python3 s4_odds.py       # verified CDS data -> odds.json
