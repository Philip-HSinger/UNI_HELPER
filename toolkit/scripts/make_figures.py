"""Render every figure used in the methods manual into reports/figures/."""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from unimath.backtest import _continuous_split_normal  # noqa: E402
from unimath.catalog import SIMILARITY, curated_only, load_catalog  # noqa: E402
from unimath.model import AdmissionModel, Student  # noqa: E402
from unimath.scores import fit_band, fit_school  # noqa: E402
from unimath.similarity import SimilarityEngine  # noqa: E402

FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
R = json.loads((ROOT / "reports" / "backtest_results.json").read_text())
CAT = curated_only(load_catalog())
M = AdmissionModel(CAT)
E = SimilarityEngine(CAT, SIMILARITY)
ST = Student(750, 790)

AMBER, INK, GREY, BLUE, RED, GREEN = "#d98a00", "#1d1d1d", "#9a9a9a", "#2b6cb0", "#c0392b", "#2e8b57"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 10,
                     "axes.titleweight": "bold", "figure.dpi": 150, "savefig.bbox": "tight"})


def save(name):
    plt.savefig(FIG / f"{name}.png")
    plt.close()


# 1. band interpolation on a skewed band
q = (740, 760, 770)
x = np.linspace(640, 800, 400)
d = fit_band(*q)
cont = _continuous_split_normal(*q)
sd = (q[2] - q[0]) / 1.348
fig, ax = plt.subplots(figsize=(6.4, 2.8))
ax.plot(x, 100 * stats.norm.cdf(x, q[1], sd), color=GREY, ls="--", label="normal through IQR (web app)")
ax.plot(x, 100 * cont(x), color=BLUE, ls=":", label="continuous split normal (abandoned)")
ax.plot(x, 100 * d.cdf(x), color=AMBER, lw=2, label="two-piece quantile-matched (UNIMATH)")
ax.scatter(q, [25, 50, 75], color=INK, zorder=5, label="published 25/50/75")
ax.set(xlabel="EBRW score", ylabel="percentile", title="Band 740/760/770: only the two-piece fit passes through all three points")
ax.legend(frameon=False, fontsize=7)
save("f1_band_fit")

# 2. E1 error distribution
fig, ax = plt.subplots(figsize=(6.4, 2.4))
raw = R["e1"]["raw"]
ax.boxplot([raw[k] for k in raw], orientation="horizontal", tick_labels=list(raw), showfliers=False,
           medianprops={"color": AMBER, "lw": 2})
ax.set(xlabel="mean |percentile error| over scores 600-800 (points)", title=f"E1: interpolation error vs known truth ({R['e1']['n']} simulated bands)")
save("f2_e1")

# 3. calibration pipeline: pool vs admitted (MIT)
c = M.cal["mit"]
xs = np.linspace(1250, 1610, 400)
comp = fit_school(next(s for s in CAT if s["id"] == "mit"))
fig, ax = plt.subplots(figsize=(6.4, 2.6))
pool = stats.norm.pdf(xs, c.m, c.s)
ax.fill_between(xs, pool / pool.max(), color=GREY, alpha=0.35, label=f"inferred applicant pool  μ={c.m:.0f}, σ={c.s:.0f}")
adm = stats.norm.pdf(xs, c.adm_mean, c.adm_sd)
ax.plot(xs, adm / adm.max(), color=AMBER, lw=2, label=f"admitted class (from CDS band)  μ={c.adm_mean:.0f}, σ={c.adm_sd:.0f}")
ax.axvline(ST.composite, color=INK, lw=1, ls="--")
ax.text(ST.composite + 3, 0.9, "student 1540", fontsize=7)
ax.set(yticks=[], xlabel="SAT composite", title="MIT: truncated-normal inversion recovers the applicant pool from rate + band")
ax.legend(frameon=False, fontsize=7, loc="upper left")
save("f3_calibration")

# 4. cross-admit heatmap
ids = ["mit", "stanford", "princeton", "cmu", "cornell", "georgia-tech", "northeastern", "purdue"]
X = M.cross_matrix(ST, ids)
lift = X / np.diag(X)[None, :]
fig, ax = plt.subplots(figsize=(5.6, 4.2))
im = ax.imshow(lift, cmap="YlOrBr", vmin=0.8, vmax=8)
for i in range(len(ids)):
    for j in range(len(ids)):
        ax.text(j, i, f"{100 * X[i, j]:.0f}", ha="center", va="center", fontsize=7, color=INK)
ax.set_xticks(range(len(ids)), [s[:8] for s in ids], rotation=45, ha="right")
ax.set_yticks(range(len(ids)), [s[:8] for s in ids])
ax.set(title="XADM: P(column | admitted at row) %, shaded by lift over marginal", xlabel="target", ylabel="given admitted at")
plt.colorbar(im, ax=ax, shrink=0.8, label="lift (×)")
save("f4_xadm")

# 5. count distribution correlated vs independent
ids9 = ["mit", "stanford", "princeton", "cmu", "cornell", "georgia-tech", "tufts", "northeastern", "purdue"]
dist = M.count_distribution(ST, ids9)
p = M.chances(ST, ids9)
ind = np.array([1.0])
for pi in p:
    ind = np.r_[ind * (1 - pi), 0] + np.r_[0, ind * pi]
fig, ax = plt.subplots(figsize=(6.4, 2.6))
n = np.arange(len(dist))
ax.bar(n - 0.2, 100 * dist, 0.4, color=AMBER, label=f"correlated model  P(0)={100 * dist[0]:.1f}%")
ax.bar(n + 0.2, 100 * ind, 0.4, color=GREY, label=f"independent product  P(0)={100 * ind[0]:.1f}%")
ax.set(xlabel="number of admits", ylabel="%", title="PORT: same marginals, very different risk of zero admits")
ax.legend(frameon=False, fontsize=7)
save("f5_port")

# 6. reliability diagrams E3
fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.0), sharey=True)
for ax, key, title in zip(axes, ("e3_well", "e3_miss"), ("world matches model", "misspecified world")):
    for name, col in (("logistic on z-score", GREY), ("unimath (fitted)", AMBER),
                      ("unimath fitted + other decisions (LOO posterior)", BLUE)):
        pts = np.array(R[key]["calib"][name])
        ax.plot(pts[:, 0], pts[:, 1], "o-", ms=3, color=col, label=name.replace("unimath fitted + other decisions (LOO posterior)", "unimath + other decisions"))
    ax.plot(np.linspace(0, 1, 50), np.linspace(0, 1, 50), color=INK, lw=0.6, ls=":")
    for setter in (ax.set_xscale, ax.set_yscale):
        setter("function", functions=(np.sqrt, np.square))
    ticks = [0, 0.02, 0.1, 0.25, 0.5, 0.75, 1]
    ax.set_xticks(ticks, [f"{t:g}" for t in ticks])
    ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
    ax.set(xlim=(0, 1), ylim=(0, 1), title=title, xlabel="predicted P(admit)")
axes[0].set_ylabel("observed admit rate")
axes[0].legend(frameon=False, fontsize=6)
save("f6_reliability")

# 7. P(no admits) for 'safe-looking' lists
fig, ax = plt.subplots(figsize=(6.4, 2.6))
labels, obs, cor, ind_ = [], [], [], []
for key, lab in (("e3_well", "matches model"), ("e3_miss", "misspecified")):
    pc, pi_, ob = (np.array(R[key]["p_any"][k]) for k in ("correlated", "independent", "observed"))
    m = pi_ > 0.95
    labels.append(f"{lab}\n(n={m.sum()} students)")
    obs.append(100 * (1 - ob[m]).mean()); cor.append(100 * (1 - pc[m]).mean()); ind_.append(100 * (1 - pi_[m]).mean())
xx = np.arange(2)
ax.bar(xx - 0.25, ind_, 0.25, color=GREY, label="independence formula predicts")
ax.bar(xx, cor, 0.25, color=AMBER, label="correlated model predicts")
ax.bar(xx + 0.25, obs, 0.25, color=INK, label="actually happened")
ax.set_xticks(xx, labels)
ax.set(ylabel="% with zero admits", title="Students whose list 'looks' ≥95% safe under independence")
ax.legend(frameon=False, fontsize=7)
save("f7_pnone")

# 8. parameter recovery
fig, ax = plt.subplots(figsize=(6.4, 2.4))
for i, (k, v) in enumerate(R["e2"].items()):
    e = np.array(v["estimates"]) / v["true"]
    ax.scatter(e, np.full_like(e, i) + np.random.default_rng(i).uniform(-0.12, 0.12, len(e)), color=AMBER, s=18)
    ax.text(max(e.max(), 1.05) + 0.03, i, f"cov95={100 * v['coverage95']:.0f}%", va="center", fontsize=7)
ax.axvline(1, color=INK, lw=0.8, ls=":")
ax.set_yticks(range(len(R["e2"])), list(R["e2"]))
ax.set(xlabel="estimate / true value", title="E2: parameter recovery, 6 replications × 1,500 students × 8 apps")
save("f8_recovery")

# 9. essay coverage heatmap
eids = ["mit", "stanford", "princeton", "purdue", "tufts", "cmu", "brown", "north-western", "usc", "yale"]
C = E.coverage_matrix(eids)
fig, ax = plt.subplots(figsize=(5.6, 4.2))
im = ax.imshow(100 * C, cmap="YlOrBr", vmin=0, vmax=100)
for i in range(len(eids)):
    for j in range(len(eids)):
        ax.text(j, i, f"{100 * C[i, j]:.0f}", ha="center", va="center", fontsize=6.5)
ax.set_xticks(range(len(eids)), [s[:8] for s in eids], rotation=45, ha="right")
ax.set_yticks(range(len(eids)), [s[:8] for s in eids])
ax.set(title="ESSY: % of row school's supplement covered by column's essays", xlabel="already written", ylabel="target")
plt.colorbar(im, ax=ax, shrink=0.8)
save("f9_essy")

# 10. similarity model vs curated
pairs = R["e5"]["pairs"]
fig, ax = plt.subplots(figsize=(4.2, 3.0))
cur = [100 * p_[2] for p_ in pairs]
ax.scatter(cur, [100 * p_[3] for p_ in pairs], color=GREY, label="raw heuristic")
ax.scatter(cur, [100 * p_[4] for p_ in pairs], color=AMBER, label="LOO-recalibrated")
ax.axhline(np.mean(cur), color=INK, lw=0.6, ls="--", label="constant (mean)")
ax.plot([0, 100], [0, 100], color=INK, lw=0.6, ls=":")
ax.set(xlim=(30, 90), ylim=(-5, 95), xlabel="curated score", ylabel="model score", title="E5: heuristic vs curated (n=10)")
ax.legend(frameon=False, fontsize=6)
save("f10_e5")

# 11. sensitivity tornado (MIT, Georgia Tech)
S = R["sens"]
fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8), sharey=True)
for ax, sid in zip(axes, ("mit", "georgia-tech")):
    base = 100 * S["base"][sid]
    keys = [k for k in S if k != "base"]
    spans = sorted(keys, key=lambda k: abs(S[k]["p_hi"][sid] - S[k]["p_lo"][sid]))
    for i, k in enumerate(spans):
        lo, hi = 100 * S[k]["p_lo"][sid], 100 * S[k]["p_hi"][sid]
        ax.barh(i, hi - base, left=base, color=AMBER)
        ax.barh(i, lo - base, left=base, color=GREY)
    ax.axvline(base, color=INK, lw=0.8)
    ax.set_yticks(range(len(spans)), [f"{k} {S[k]['lo']}→{S[k]['hi']}" for k in spans])
    ax.set(title=f"{sid}: base {base:.1f}%", xlabel="P(admit) %")
save("f11_sens")

# 12. posterior on shared factor
Sg, logw = M.grid(ST)
fig, ax = plt.subplots(figsize=(6.4, 2.4))
for dec, col, lab in (({}, GREY, "prior"), ({"mit": "rejected", "stanford": "rejected"}, RED, "after MIT + Stanford rejections"),
                      ({"cmu": "accepted"}, GREEN, "after CMU admit"), ({"mit": "accepted"}, BLUE, "after MIT admit")):
    w = np.exp(M.posterior_logw(ST, dec)) if dec else np.exp(logw)
    ax.plot(Sg, w / (Sg[1] - Sg[0]), color=col, label=lab)
ax.set(xlim=(-3, 5), yticks=[], xlabel="shared strength factor S", title="UPDT: decisions reshape the belief about the applicant")
ax.legend(frameon=False, fontsize=7)
save("f12_posterior")
print("figures written to", FIG)

# 13. forest plot of every effect with 95% CI (from significance.json)
SIGP = ROOT / "reports" / "significance.json"
if SIGP.exists():
    SG = json.loads(SIGP.read_text())
    rows = []
    for world, lab in (("pred_well", "matched"), ("pred_miss", "misspec.")):
        if world not in SG:
            continue
        w = SG[world]
        for key, name in (("fitted_vs_base", "chances vs acceptance rate"), ("fitted_vs_logistic", "chances vs logistic model"),
                          ("default_vs_logistic", "no-data chances vs logistic"), ("posterior_vs_fitted", "using other decisions")):
            d = w[key]["brier"]
            base = d["diff"] / d["relative"]
            rows.append((f"{name} ({lab})", -100 * d["relative"], -100 * d["ci95"][1] / base, -100 * d["ci95"][0] / base))
    c1 = SG["c1"]["vs_web"]
    rows.append(("percentile curve vs bell curve", -c1["diff"] / np.mean(R["e1"]["raw"]["normal-IQR (web app)"]) * 100,
                 -c1["ci95"][1] / np.mean(R["e1"]["raw"]["normal-IQR (web app)"]) * 100,
                 -c1["ci95"][0] / np.mean(R["e1"]["raw"]["normal-IQR (web app)"]) * 100))
    fig, ax = plt.subplots(figsize=(6.4, 0.32 * len(rows) + 0.8))
    for i, (name, est, lo, hi) in enumerate(rows[::-1]):
        col = GREEN if lo > 0 else GREY
        ax.plot([lo, hi], [i, i], color=col, lw=2.5)
        ax.plot(est, i, "o", color=INK, ms=4)
    ax.axvline(0, color=RED, lw=0.8, ls="--")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]])
    ax.set(xlabel="% reduction in error (bar = 95% CI; right of red line = better than the comparison)",
           title="Is it better than chance? Every comparison with its 95% interval")
    save("f13_forest")
    print("forest written")

# 14. backtest power
PW = ROOT / "reports" / "power.json"
if PW.exists():
    pw = json.loads(PW.read_text())
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
    for ax, key, title in zip(axes, ("scores_only", "with_counselor_rating"),
                              ("A. scores-only UNIMATH vs counselor", "B. UNIMATH + counselor rating vs counselor")):
        ns = [int(k) for k in pw[key]]
        ax.plot(ns, [100 * pw[key][str(n)]["p_unimath_significantly_better"] for n in ns], "o-", color=AMBER, label="UNIMATH significantly better")
        ax.plot(ns, [100 * pw[key][str(n)]["p_counselor_significantly_better"] for n in ns], "o-", color=BLUE, label="counselor significantly better")
        ax.plot(ns, [100 * pw[key][str(n)]["p_inconclusive"] for n in ns], "o--", color=GREY, label="inconclusive")
        ax.axvline(25, color=RED, lw=0.7, ls=":")
        ax.set(xscale="log", xlabel="past students in the backtest", title=title)
        ax.set_xticks(ns, [str(n) for n in ns])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axes[0].set_ylabel("% of simulated backtests")
    axes[0].legend(frameon=False, fontsize=6.5)
    save("f14_power")
    print("power fig written")
