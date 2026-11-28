"""Significance of every backtest claim: multi-seed E3/E4, 20-rep E2, exact/permutation tests.
Writes results/significance.json."""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from unimath import backtest as bt  # noqa: E402
from unimath import significance as sg  # noqa: E402
from unimath.catalog import curated_only, load_catalog  # noqa: E402

CAT = curated_only(load_catalog())
R = json.loads((ROOT / "results" / "backtest_results.json").read_text())
out, t0 = {}, time.time()

# ---- C1 band fit: paired across simulated bands
raw = R["e1"]["raw"]
ours = raw["two-piece quantile-matched"]
out["c1"] = {"vs_web": sg.paired_tests(ours, raw["normal-IQR (web app)"]),
             "vs_continuous": sg.paired_tests(ours, raw["continuous split normal"])}

# ---- C6 similarity: n=10
e5 = R["e5"]
cur = [p[2] for p in e5["pairs"]]
out["c6"] = {"raw_spearman": sg.permutation_spearman(cur, [p[3] for p in e5["pairs"]]),
             "loo_spearman": sg.permutation_spearman(cur, [p[4] for p in e5["pairs"]]),
             "abs_err_vs_constant": sg.paired_tests(np.abs(np.array(cur) - [p[3] for p in e5["pairs"]]) * 100,
                                                    np.abs(np.array(cur) - [np.mean([c for j, c in enumerate(cur) if j != i]) for i in range(len(cur))]) * 100)}

# ---- C7 planner
k, n = int(round(R["e6"]["same_list"] * R["e6"]["trials"])), R["e6"]["trials"]
out["c7"] = {"k": k, "n": n, "ci95": sg.clopper_pearson(k, n)}
print("fast parts", time.time() - t0, flush=True)

# ---- C2-C5 predictive, 5 seeds x 2 worlds, pooled with student-cluster bootstrap
def brier_rows(p, y):
    return (np.asarray(p) - np.asarray(y)) ** 2

def ll_rows(p, y):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    y = np.asarray(y)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))

for world, mis in (("well", False), ("miss", True)):
    pooled = {"preds": {}, "y": [], "student": [], "pc": [], "pi": [], "obs": [], "cnt_c": [], "cnt_i": [], "per_seed": []}
    for s_i, seed in enumerate((7, 8, 9, 10, 11)):
        r = bt.e3_e4_predictive(CAT, mis, seed=seed, return_preds=True)
        offset = s_i * 10 ** 6  # keep students distinct across seeds
        for kname, v in r["preds"].items():
            pooled["preds"].setdefault(kname, []).extend(v)
        pooled["y"] += r["y"]
        pooled["student"] += [st + offset for st in r["student"]]
        pooled["pc"] += r["pany_correlated"]; pooled["pi"] += r["pany_independent"]; pooled["obs"] += r["any_observed"]
        pooled["cnt_c"] += r["count_ll"]["correlated"]; pooled["cnt_i"] += r["count_ll"]["independent"]
        pooled["per_seed"].append({"seed": seed, "scores": r["scores"], "fitted": r["fitted"]})
        print(world, seed, time.time() - t0, flush=True)
    y, stu = np.array(pooled["y"]), np.array(pooled["student"])
    P = {k_: np.array(v) for k_, v in pooled["preds"].items()}
    fit_, logi, base = P["unimath (fitted)"], P["logistic on z-score"], P["base rate"]
    post, dflt = P["unimath fitted + other decisions (LOO posterior)"], P["unimath (default priors)"]
    coin = np.full_like(y, 0.5)
    res = {"n_rows": int(len(y)), "n_students": int(len(np.unique(stu))), "admit_rate": float(y.mean())}
    res["auc"] = {k_: sg.auc_test(v, y) for k_, v in P.items()}
    res["brier"] = {k_: float(brier_rows(v, y).mean()) for k_, v in P.items()}
    res["brier"]["coin flip (0.5)"] = float(brier_rows(coin, y).mean())
    cmp = lambda a, b: {"brier": sg.cluster_bootstrap_diff(brier_rows(a, y), brier_rows(b, y), stu),  # noqa: E731
                        "logloss": sg.cluster_bootstrap_diff(ll_rows(a, y), ll_rows(b, y), stu)}
    res["fitted_vs_base"] = cmp(fit_, base)
    res["fitted_vs_logistic"] = cmp(fit_, logi)
    res["default_vs_logistic"] = cmp(dflt, logi)
    res["posterior_vs_fitted"] = cmp(post, fit_)
    # C4 count distribution: per-student paired log-score (higher is better -> negate as loss)
    sid = np.arange(len(pooled["cnt_c"]))
    res["count_correlated_vs_independent"] = sg.cluster_bootstrap_diff(-np.array(pooled["cnt_c"]), -np.array(pooled["cnt_i"]), sid)
    # C4b zero-admit among 'safe-looking' lists
    pc, pi, obs = map(np.array, (pooled["pc"], pooled["pi"], pooled["obs"]))
    m = pi > 0.95
    k0 = int((1 - obs[m]).sum())
    res["safe_lists"] = {"n": int(m.sum()), "zero_admits": k0, "observed_rate": k0 / max(m.sum(), 1),
                         "observed_ci95": sg.wilson(k0, int(m.sum())),
                         "independence": sg.poisson_binomial_test(1 - pi[m], k0),
                         "correlated": sg.poisson_binomial_test(1 - pc[m], k0)}
    res["per_seed"] = pooled["per_seed"]
    out[f"pred_{world}"] = res
    (ROOT / "results" / "significance.json").write_text(json.dumps(out, indent=1))

# ---- C5 parameter recovery with 20 replications
e2 = bt.e2_recovery(CAT, reps=20)
for k_, v in e2.items():
    cov_k = int(round(v["coverage95"] * 20))
    v["coverage_ci95"] = sg.clopper_pearson(cov_k, 20)
    est = np.array(v["estimates"])
    v["bias_t_p"] = float(__import__("scipy").stats.ttest_1samp(est, v["true"]).pvalue)
out["c5"] = e2
(ROOT / "results" / "significance.json").write_text(json.dumps(out, indent=1))
print("done", time.time() - t0)
