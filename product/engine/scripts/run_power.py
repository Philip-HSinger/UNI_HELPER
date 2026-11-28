"""E7: how many past students a counselor needs for BKTST to be conclusive. Writes results/power.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from unimath.backtest import e7_backtest_power  # noqa: E402
from unimath.catalog import curated_only, load_catalog  # noqa: E402

CAT = curated_only(load_catalog())
r = {"scores_only": e7_backtest_power(CAT, sizes=(25, 50, 100, 200, 400, 800), reps=150),
     "with_counselor_rating": e7_backtest_power(CAT, sizes=(25, 50, 100, 200, 400, 800), reps=150, informed=True)}
(ROOT / "results" / "power.json").write_text(json.dumps(r, indent=1))
