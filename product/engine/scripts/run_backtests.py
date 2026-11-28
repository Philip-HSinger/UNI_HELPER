"""Run the full validation suite and write results/backtest_results.json (feeds the PDF)."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from calliper import backtest as bt  # noqa: E402
from calliper.catalog import curated_only, load_catalog  # noqa: E402
from calliper.model import Student  # noqa: E402

schools = curated_only(load_catalog())
sim_csv = ROOT / "data" / "similarity.csv"
out, t0 = {}, time.time()
out["e1"] = bt.e1_band_fit(400); print("e1", time.time() - t0, flush=True)
out["e5"] = bt.e5_similarity(schools, sim_csv)
out["e6"] = bt.e6_planner(schools, sim_csv, trials=30); print("e6", time.time() - t0, flush=True)
out["e3_well"] = bt.e3_e4_predictive(schools, misspecified=False); print("e3w", time.time() - t0, flush=True)
out["e3_miss"] = bt.e3_e4_predictive(schools, misspecified=True); print("e3m", time.time() - t0, flush=True)
out["e2"] = bt.e2_recovery(schools, reps=6); print("e2", time.time() - t0, flush=True)
out["sens"] = bt.sensitivity(schools, Student(750, 790), ["mit", "stanford", "cmu", "georgia-tech", "purdue"])
(ROOT / "results" / "backtest_results.json").write_text(json.dumps(out, indent=1))
print("done", time.time() - t0)
