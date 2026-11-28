"""Backtest / validation suite. Every experiment returns plain data (for the CLI and the PDF).

What can be validated, and how:
  E1 band interpolation   - simulation with known truth: draw skewed, ceiling-censored score
                            distributions, publish their rounded 25/50/75, refit, compare
                            percentiles to the truth. Baselines: web-app normal-IQR, continuous
                            split normal.
  E2 parameter recovery   - simulate decisions from known parameters, refit by marginal ML,
                            check bias, spread and 95% CI coverage across replications.
  E3 predictive accuracy  - out-of-sample (split by student) Brier / log loss / AUC / ECE against
                            baselines, both when the world matches the model and when it doesn't
                            (heavy tails, per-school weight errors, hooked applicants).
  E4 cross-admit value    - does conditioning on a student's other decisions improve prediction
                            (leave-one-out posterior vs marginal)? Is P(at least one admit)
                            calibrated, vs the independence formula 1 - prod(1 - p)?
  E5 essay similarity     - model reuse scores vs the human-curated pairs (held out).
  E6 planner              - greedy+swap vs brute-force optimum on random instances.
On real data, E3/E4 run unchanged on an outcomes CSV (`unimath fit` / `BKTST <csv>`).
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
from scipy import optimize, stats
from scipy.special import expit, logit

from .fit import (Outcomes, fit, predict_leave_one_out, predict_marginal, score_all, simulate)
from .model import AdmissionModel, ModelParams, Student
from .planner import greedy_only, plan
from .scores import SplitNormal, fit_band
from .similarity import SimilarityEngine, fit_line


# ---------------------------------------------------------------------------------------- E1
def _continuous_split_normal(q25, q50, q75):
    """The approach tried first and abandoned: density-continuous split normal fitted to 3
    quantiles by least squares (bounded skew -> cannot reach real selective-school bands)."""
    def ppf(mu, sl, sr, p):
        wl = sl / (sl + sr)
        p = np.asarray(p)
        return np.where(p < wl, mu + sl * stats.norm.ppf(np.clip(p / (2 * wl), 1e-12, 1)),
                        mu + sr * stats.norm.ppf(np.clip(1 - (1 - p) / (2 * (1 - wl)), 0, 1 - 1e-12)))

    def resid(t):
        return ppf(t[0], np.exp(t[1]), np.exp(t[2]), [0.25, 0.5, 0.75]) - [q25, q50, q75]
    s0 = max((q75 - q25) / 1.349, 5)
    t = optimize.least_squares(resid, [q50, np.log(s0), np.log(s0)]).x
    mu, sl, sr = t[0], np.exp(t[1]), np.exp(t[2])
    wl = sl / (sl + sr)

    def cdf(x):
        return np.where(x < mu, 2 * wl * stats.norm.cdf((x - mu) / sl), 1 - 2 * (1 - wl) * stats.norm.sf((x - mu) / sr))
    return cdf


def e1_band_fit(n: int = 300, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    grid = np.arange(600, 801, 10)
    errs = {"normal-IQR (web app)": [], "continuous split normal": [], "two-piece quantile-matched": []}
    errs_800 = {k: [] for k in errs}
    for _ in range(n):
        loc = rng.uniform(680, 800)
        scale = rng.uniform(25, 70)
        alpha = rng.uniform(-6, 2)  # mostly left-skewed, like real selective bands
        xs = np.clip(stats.skewnorm.rvs(alpha, loc, scale, size=40000, random_state=rng), 200, 800)
        xs = np.round(xs / 10) * 10
        q = np.round(np.percentile(xs, [25, 50, 75]) / 10) * 10
        if not (q[0] < q[2]):
            continue
        true = np.array([(np.mean(xs < g) + 0.5 * np.mean(xs == g)) for g in grid])
        # ours
        d = fit_band(*q)
        ours = np.array([d.mid_rank(g) for g in grid])
        # web app: normal through IQR, clamped to [1, 99]%
        sd = (q[2] - q[0]) / 1.348
        web = np.clip(stats.norm.cdf(grid, q[1], sd), 0.01, 0.99)
        # continuous split normal with mid-rank + cap
        cdf = _continuous_split_normal(*q)
        cont = np.array([0.5 * (float(cdf(g - 5)) + (1.0 if g + 5 >= 800 else float(cdf(g + 5)))) for g in grid])
        for k, v in (("normal-IQR (web app)", web), ("continuous split normal", cont), ("two-piece quantile-matched", ours)):
            errs[k].append(np.abs(v - true).mean() * 100)
            errs_800[k].append(abs(v[-1] - true[-1]) * 100)
    return {"n": len(errs["normal-IQR (web app)"]), "grid": grid.tolist(),
            "mae": {k: float(np.mean(v)) for k, v in errs.items()},
            "p90": {k: float(np.percentile(v, 90)) for k, v in errs.items()},
            "mae_at_800": {k: float(np.mean(v)) for k, v in errs_800.items()},
            "raw": {k: list(map(float, v)) for k, v in errs.items()}}


# ---------------------------------------------------------------------------------------- E2
TRUE = ModelParams(sigma_eps=0.8, shared_fit=0.45, test_scale=1.3, lapse=0.03)


def e2_recovery(schools, reps: int = 4, n_students: int = 1500, apps: int = 8, true: ModelParams = TRUE) -> dict:
    names = ("sigma_eps", "shared_fit", "test_scale", "lapse")
    est = {k: [] for k in names}
    se = {k: [] for k in names}
    for r in range(reps):
        o = simulate(schools, true, n_students, apps, seed=100 + r)
        res = fit(schools, o)
        for k in names:
            est[k].append(res.estimates[k])
            se[k].append(res.std_errors[k])
    out = {}
    for k in names:
        e, s, t = np.array(est[k]), np.array(se[k]), getattr(true, k)
        out[k] = {"true": t, "mean": float(e.mean()), "sd": float(e.std(ddof=1)) if reps > 1 else float("nan"),
                  "mean_se": float(np.nanmean(s)), "coverage95": float(np.mean(np.abs(e - t) <= 1.96 * s)),
                  "estimates": e.tolist()}
    return out


# ---------------------------------------------------------------------------------------- E3/E4
def logistic_baseline(schools, train: Outcomes):
    """What a careful 'vibe-coded' tool would do: pooled logistic regression of admit on
    logit(acceptance rate) and the student's z-score vs the school's published band."""
    M = AdmissionModel(schools)

    def feats(o):
        r = np.array([M.cal[s].rate for s in o.school])
        mu = np.array([M.cal[s].adm_mean for s in o.school])
        sd = np.array([M.cal[s].adm_sd for s in o.school])
        z = (o.ebrw + o.math - mu) / sd
        return np.c_[np.ones(len(o)), logit(r), z]

    X, y = feats(train), train.y

    def nll(b):
        p = np.clip(expit(X @ b), 1e-9, 1 - 1e-9)
        return -np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))
    b = optimize.minimize(nll, np.zeros(3), method="BFGS").x
    return lambda o: expit(feats(o) @ b)


def split_students(o: Outcomes, frac=0.6, seed=0):
    rng = np.random.default_rng(seed)
    stu = np.unique(o.student)
    tr = set(rng.choice(stu, int(frac * len(stu)), replace=False).tolist())
    m = np.array([s in tr for s in o.student])
    return o.subset(m), o.subset(~m)


def independent_count_logscore(p_marg, o: Outcomes):
    """Mean log P(observed #admits) under independence (Poisson-binomial of marginals)."""
    out = []
    for s in np.unique(o.student):
        idx = o.student == s
        dist = np.array([1.0])
        for p in p_marg[idx]:
            dist = np.r_[dist * (1 - p), 0] + np.r_[0, dist * p]
        out.append(np.log(max(dist[int(o.y[idx].sum())], 1e-12)))
    return float(np.mean(out))


def correlated_count_logscore(model: AdmissionModel, o: Outcomes):
    from .fit import LOGW, _prob_rows, _row_terms
    off, s_mu, s_sd, r, _ = _row_terms(model, o)
    P, _, _ = _prob_rows(model, o, off, s_mu, s_sd, r)
    w = np.exp(LOGW)
    out, pany_c, pany_i, any_obs = [], [], [], []
    for s in np.unique(o.student):
        idx = np.flatnonzero(o.student == s)
        dist = np.zeros((len(idx) + 1, P.shape[1]))
        dist[0] = 1
        for i in idx:
            dist[1:] = dist[1:] * (1 - P[i]) + dist[:-1] * P[i]
            dist[0] *= 1 - P[i]
        mix = dist @ w
        out.append(np.log(max(mix[int(o.y[idx].sum())], 1e-12)))
        pm = P[idx] @ w
        pany_c.append(1 - mix[0])
        pany_i.append(1 - np.prod(1 - pm))
        any_obs.append(float(o.y[idx].max()))
    return float(np.mean(out)), np.array(pany_c), np.array(pany_i), np.array(any_obs)


def per_student_count_ll(model: AdmissionModel, o: Outcomes, p_marg) -> dict:
    """Per-student log P(observed #admits): correlated model vs independence. Paired by student."""
    from .fit import LOGW, _prob_rows, _row_terms
    off, s_mu, s_sd, r, _ = _row_terms(model, o)
    P, _, _ = _prob_rows(model, o, off, s_mu, s_sd, r)
    w = np.exp(LOGW)
    cor, ind = [], []
    for s in np.unique(o.student):
        idx = np.flatnonzero(o.student == s)
        k = int(o.y[idx].sum())
        dist = np.zeros((len(idx) + 1, P.shape[1]))
        dist[0] = 1
        for i in idx:
            dist[1:] = dist[1:] * (1 - P[i]) + dist[:-1] * P[i]
            dist[0] *= 1 - P[i]
        cor.append(float(np.log(max((dist @ w)[k], 1e-12))))
        d = np.array([1.0])
        for p in p_marg[idx]:
            d = np.r_[d * (1 - p), 0] + np.r_[0, d * p]
        ind.append(float(np.log(max(d[k], 1e-12))))
    return {"correlated": cor, "independent": ind}


def e3_e4_predictive(schools, misspecified: bool, n_students=2500, seed=7, true: ModelParams = TRUE,
                     return_preds: bool = False) -> dict:
    o = simulate(schools, true, n_students, 8, seed=seed, misspecified=misspecified)
    train, test = split_students(o, 0.6, seed)
    y = test.y
    res = fit(schools, train)
    fitted = AdmissionModel(schools, res.params)
    default = AdmissionModel(schools, ModelParams(waitlist_width=res.params.waitlist_width))
    base = np.array([default.cal[s].rate for s in test.school])
    logi = logistic_baseline(schools, train)(test)
    preds = {
        "base rate": base,
        "logistic on z-score": logi,
        "unimath (default priors)": predict_marginal(default, test),
        "unimath (fitted)": predict_marginal(fitted, test),
        "unimath fitted + other decisions (LOO posterior)": predict_leave_one_out(fitted, test),
    }
    scores = {k: score_all(v, y) for k, v in preds.items()}
    ls_c, pany_c, pany_i, any_obs = correlated_count_logscore(fitted, test)
    ls_i = independent_count_logscore(preds["unimath (fitted)"], test)
    extra = {}
    if return_preds:
        extra = {"preds": {k: v.tolist() for k, v in preds.items()}, "y": y.tolist(), "student": test.student.tolist(),
                 "pany_correlated": pany_c.tolist(), "pany_independent": pany_i.tolist(), "any_observed": any_obs.tolist(),
                 "count_ll": per_student_count_ll(fitted, test, preds["unimath (fitted)"])}
    return {**extra, "misspecified": misspecified, "n_train_rows": len(train), "n_test_rows": len(test),
            "fitted": res.estimates, "scores": scores,
            "count_logscore": {"correlated": ls_c, "independent": ls_i},
            "p_any": {"correlated": pany_c.tolist(), "independent": pany_i.tolist(), "observed": any_obs.tolist()},
            "calib": {k: _calib(v, y) for k, v in preds.items()}}


def _calib(p, y, bins=10):
    order = np.argsort(p)
    return [(float(p[c].mean()), float(y[c].mean())) for c in np.array_split(order, bins)]


# ---------------------------------------------------------------------------------------- E5
def e5_similarity(schools, curated_csv) -> dict:
    full = SimilarityEngine(schools, curated_csv)
    blind = SimilarityEngine(schools, None)
    pairs = []
    for (a, b), v in full.curated.items():
        i, j = blind.index[a], blind.index[b]
        pairs.append((a, b, v, float(max(blind.R[i, j], blind.R[j, i]))))
    cur = np.array([p[2] for p in pairs])
    raw = np.array([max(blind._heuristic(blind.index[a], blind.index[b]), blind._heuristic(blind.index[b], blind.index[a]))
                    for a, b, _, _ in pairs])
    # leave-one-out recalibration: fit the line on n-1 curated pairs, predict the held-out one
    loo = np.empty(len(pairs))
    for k in range(len(pairs)):
        m = np.arange(len(pairs)) != k
        al, be = fit_line(raw[m], cur[m])
        loo[k] = np.clip(al + be * raw[k], 0, 1) if raw[k] > 0 else 0.0
    const = np.array([cur[np.arange(len(cur)) != k].mean() for k in range(len(cur))])
    rho = lambda a: float(stats.spearmanr(cur, a).statistic) if len(pairs) > 2 else float("nan")  # noqa: E731
    mae = lambda a: float(np.mean(np.abs(cur - a)) * 100)  # noqa: E731
    return {"n_pairs": len(pairs),
            "raw": {"spearman": rho(raw), "mae_points": mae(raw)},
            "loo_calibrated": {"spearman": rho(loo), "mae_points": mae(loo)},
            "constant_baseline": {"mae_points": mae(const)},
            "pairs": [(a, b, float(c), float(r), float(l)) for (a, b, _, _), c, r, l in zip(pairs, cur, raw, loo)]}


# ---------------------------------------------------------------------------------------- E6
def e6_planner(schools, curated_csv, trials=25, seed=3) -> dict:
    rng = np.random.default_rng(seed)
    M = AdmissionModel(schools)
    E = SimilarityEngine(schools, curated_csv)
    ids = M.usable()
    gaps, exact_hits = [], 0
    for _ in range(trials):
        cands = list(rng.choice(ids, 10, replace=False))
        u = {c: float(rng.uniform(40, 100)) for c in cands}
        e, m = rng.integers(600, 801) // 10 * 10, rng.integers(600, 801) // 10 * 10
        st = Student(float(e), float(m))
        lam = float(rng.choice([0.002, 0.005, 0.01]))
        ex = plan(M, E, st, cands, u, lam, max_apps=8, exact_limit=99)
        gr = greedy_only(M, E, st, cands, u, lam, max_apps=8)
        gap = (ex.objective - gr.objective) / max(abs(ex.objective), 1e-9)
        gaps.append(gap * 100)
        exact_hits += sorted(ex.schools) == sorted(gr.schools)
    g = np.array(gaps)
    return {"trials": trials, "mean_gap_pct": float(g.mean()), "max_gap_pct": float(g.max()),
            "same_list": exact_hits / trials}


def sensitivity(schools, student: Student, sids: list[str]) -> dict:
    """P(admit) under +-1 step of each assumption - which assumptions the answer actually depends on."""
    base = AdmissionModel(schools)
    ids = base.usable(sids)
    p0 = base.chances(student, ids)
    knobs = {"sigma_eps": (0.7, 1.4), "shared_fit": (0.1, 0.5), "rho_th": (0.2, 0.6), "test_scale": (0.7, 1.3),
             "lapse": (0.02, 0.10), "rho_em": (0.4, 0.8), "enrolled_shift": (0.0, 20.0)}
    out = {"base": dict(zip(ids, p0.tolist()))}
    for k, (lo, hi) in knobs.items():
        out[k] = {"lo": lo, "hi": hi,
                  "p_lo": dict(zip(ids, base.with_params(**{k: lo}).chances(student, ids).tolist())),
                  "p_hi": dict(zip(ids, base.with_params(**{k: hi}).chances(student, ids).tolist()))}
    return out


# ---------------------------------------------------------------------------------------- E7 power
def e7_backtest_power(schools, sizes=(25, 50, 100, 200, 400), reps=150, seed=0, informed: bool = False) -> dict:
    """How many past students does BKTST need before 'UNIMATH beat my calls' is distinguishable from luck?

    Simulated counselor: knows each student's non-test strength (noisy rating, sd 0.6) - information UNIMATH's
    score-only forecast lacks - but reports only reach (<20%), target (20-60%) or likely (>60%) labels.
    UNIMATH: default parameters, scores only. Scoring exactly as BKTST: labels -> leave-one-student-out label
    rates; Brier difference with a student-cluster bootstrap 95% CI.
    """
    from .fit import predict_marginal
    from .significance import cluster_bootstrap_diff
    M = AdmissionModel(schools)
    out = {}
    for n in sizes:
        wins = losses = 0
        diffs = []
        for r in range(reps):
            o = simulate(schools, TRUE, n, 8, seed=seed * 100000 + n * 1000 + r, rated_share=1.0)
            y = o.y
            p_c_full = predict_marginal(M, o)                      # counselor's private, informed estimate
            calls = np.where(p_c_full < 0.2, 0, np.where(p_c_full < 0.6, 1, 2))
            blind = Outcomes(o.student, o.school, o.ebrw, o.math, o.code, np.full(len(o), np.nan), o.submitted)
            # UNIMATH: scores only, or (informed=True) scores + the counselor's own holistic rating via HOL
            p_u = predict_marginal(M, o if informed else blind)
            if informed:
                # counselor's rating is a separate noisy read, not the same one used for their labels
                rng = np.random.default_rng(r)
                from scipy import stats as _st
                h_lab = _st.norm.ppf(np.clip(o.hpct / 100, 1e-3, 1 - 1e-3))
                o2 = Outcomes(o.student, o.school, o.ebrw, o.math, o.code,
                              100 * _st.norm.cdf(h_lab + 0.3 * rng.standard_normal(len(o))), o.submitted)
                p_u = predict_marginal(M, o2)
            p_c = np.empty(len(o))
            for i in range(len(o)):
                m = (calls == calls[i]) & (o.student != o.student[i])
                p_c[i] = (y[m].sum() + 0.5) / (m.sum() + 1.0)
            d = cluster_bootstrap_diff((p_u - y) ** 2, (p_c - y) ** 2, o.student, B=600, seed=r)
            diffs.append(d["diff"])
            wins += d["ci95"][1] < 0
            losses += d["ci95"][0] > 0
        out[str(n)] = {"p_unimath_significantly_better": wins / reps, "p_counselor_significantly_better": losses / reps,
                       "p_inconclusive": 1 - (wins + losses) / reps, "mean_diff": float(np.mean(diffs))}
        print("power", n, out[str(n)], flush=True)
    return out
