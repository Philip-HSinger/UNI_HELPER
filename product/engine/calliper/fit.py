"""Estimation and evaluation: fit the model's global parameters to real outcomes, score forecasts.

Outcomes data (CSV) - one row per application:
    student_id, school_id, ebrw, math, decision[, holistic_pct][, submitted]
decision in {accepted, rejected, waitlisted, deferred}. This is exactly what an advising practice
already has in its CRM for past clients, or what a high school has in Naviance/Scoir exports.

Estimation: maximum *marginal* likelihood. Each student's shared factor S is integrated out on a
grid (so a student's 8 decisions are treated as 8 correlated observations, not 8 independent ones -
treating them as independent overstates the evidence and biases the noise parameters).
    L(theta) = prod_students  integral  prod_{j in apps} P(d_ij | S, theta)  N(S; mu_i, sd) dS
Optimized over (log sigma_eps, logit gamma, log test_scale, logit lapse) with L-BFGS-B; standard
errors from the numerical Hessian of the negative log-likelihood (observed information).

Evaluation (proper scoring rules, so a model can't game them by hedging):
    Brier  = mean (p - y)^2           log loss = -mean [y log p + (1-y) log(1-p)]
    AUC    = P(p_admit > p_reject) over admit/reject pairs (discrimination)
    ECE    = sum_bins (n_b/N) |mean p_b - mean y_b|    (calibration, 10 equal-mass bins)
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, replace

import numpy as np
from scipy import optimize, stats
from scipy.special import expit, logit, ndtr

from .model import DECISION_CODES, AdmissionModel, ModelParams


@dataclass
class Outcomes:
    student: np.ndarray   # int index per row
    school: np.ndarray    # school id per row (str)
    ebrw: np.ndarray
    math: np.ndarray
    code: np.ndarray      # 1 admit, 0 reject, 2 waitlist
    hpct: np.ndarray      # holistic percentile or nan
    submitted: np.ndarray

    def __len__(self):
        return len(self.code)

    def subset(self, mask) -> "Outcomes":
        return Outcomes(*(getattr(self, f)[mask] for f in self.__dataclass_fields__))

    @property
    def y(self) -> np.ndarray:
        return (self.code == 1).astype(float)


def load_outcomes(path: str) -> Outcomes:
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    sid = {s: i for i, s in enumerate(dict.fromkeys(r["student_id"] for r in rows))}
    get = lambda r, k, d: r.get(k) if r.get(k) not in (None, "") else d  # noqa: E731
    return Outcomes(
        np.array([sid[r["student_id"]] for r in rows]),
        np.array([r["school_id"] for r in rows]),
        np.array([float(r["ebrw"]) for r in rows]),
        np.array([float(r["math"]) for r in rows]),
        np.array([DECISION_CODES[r["decision"].strip().lower()] for r in rows]),
        np.array([float(get(r, "holistic_pct", "nan")) for r in rows]),
        np.array([str(get(r, "submitted", "true")).lower() in ("1", "true", "yes") for r in rows]),
    )


def save_outcomes(o: Outcomes, path: str) -> None:
    inv = {1: "accepted", 0: "rejected", 2: "waitlisted"}
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["student_id", "school_id", "ebrw", "math", "decision", "holistic_pct", "submitted"])
        for i in range(len(o)):
            w.writerow([f"s{o.student[i]}", o.school[i], int(o.ebrw[i]), int(o.math[i]), inv[int(o.code[i])],
                        "" if np.isnan(o.hpct[i]) else round(float(o.hpct[i]), 1), str(bool(o.submitted[i])).lower()])


# ------------------------------------------------------------------------------------------------
# Vectorized likelihood
# ------------------------------------------------------------------------------------------------
def _row_terms(model: AdmissionModel, o: Outcomes):
    """Per-row offset, shared-prior mean/sd, base rate, waitlist width - vectorized over rows."""
    p = model.params
    cal = model.cal
    m = np.array([cal[s].m for s in o.school])
    sd = np.array([cal[s].s for s in o.school])
    a = np.array([cal[s].a for s in o.school])
    c = np.array([cal[s].c for s in o.school])
    kap = np.array([cal[s].kappa for s in o.school])
    r = np.array([cal[s].rate for s in o.school])
    T = o.ebrw + o.math
    zt = np.where(o.submitted, (T - m) / sd, p.withheld_z)
    off = a * zt - p.holistic_weight * kap - c
    rated = ~np.isnan(o.hpct)
    hm = np.where(rated, stats.norm.ppf(np.clip(np.nan_to_num(o.hpct, nan=50) / 100, 0.001, 0.999)),
                  p.rho_th * (T - p.ref_mean) / p.ref_sd)
    hs = np.where(rated, 0.6, np.sqrt(1 - p.rho_th ** 2))
    b = p.holistic_weight
    s_mu = b * hm
    s_sd = np.sqrt((b * hs) ** 2 + p.shared_fit * p.sigma_eps ** 2)
    wl = p.waitlist_width * np.sqrt(a ** 2 + b ** 2 + p.sigma_eps ** 2)
    return off, s_mu, s_sd, r, wl


ZGRID = np.linspace(-6, 6, 121)
LOGW = stats.norm.logpdf(ZGRID) - np.logaddexp.reduce(stats.norm.logpdf(ZGRID))


def _prob_rows(model, o, off, s_mu, s_sd, r):
    x = off[:, None] + s_mu[:, None] + s_sd[:, None] * ZGRID[None, :]
    sd = np.sqrt(1 - model.params.shared_fit) * model.params.sigma_eps
    return (1 - model.params.lapse) * ndtr(x / sd) + model.params.lapse * r[:, None], x, sd


def marginal_loglik(model: AdmissionModel, o: Outcomes) -> float:
    off, s_mu, s_sd, r, wl = _row_terms(model, o)
    P, x, sd = _prob_rows(model, o, off, s_mu, s_sd, r)
    om = model.params.lapse
    band = ndtr(-x / sd) - ndtr(-(x + wl[:, None]) / sd)
    code = o.code[:, None]
    p_rej = (1 - om) * ndtr(-(x + wl[:, None]) / sd) + om * (1 - r[:, None])
    lik = np.where(code == 1, P, np.where(code == 0, p_rej, (1 - om) * band))
    ll = np.log(np.clip(lik, 1e-300, None))
    # sum rows within student, then integrate over the student's S grid
    order = np.argsort(o.student, kind="stable")
    stu = o.student[order]
    starts = np.r_[0, np.flatnonzero(np.diff(stu)) + 1]
    per_student = np.add.reduceat(ll[order], starts, axis=0)
    return float(np.logaddexp.reduce(per_student + LOGW[None, :], axis=1).sum())


def predict_marginal(model: AdmissionModel, o: Outcomes) -> np.ndarray:
    """P(admit) for each row using no other decisions (what a student sees before applying)."""
    off, s_mu, s_sd, r, _ = _row_terms(model, o)
    P, _, _ = _prob_rows(model, o, off, s_mu, s_sd, r)
    return P @ np.exp(LOGW)


def predict_leave_one_out(model: AdmissionModel, o: Outcomes) -> np.ndarray:
    """P(admit) for each row given *all the student's other decisions* (the Bayesian update)."""
    off, s_mu, s_sd, r, wl = _row_terms(model, o)
    P, x, sd = _prob_rows(model, o, off, s_mu, s_sd, r)
    om = model.params.lapse
    band = ndtr(-x / sd) - ndtr(-(x + wl[:, None]) / sd)
    code = o.code[:, None]
    p_rej = (1 - om) * ndtr(-(x + wl[:, None]) / sd) + om * (1 - r[:, None])
    lik = np.where(code == 1, P, np.where(code == 0, p_rej, (1 - om) * band))
    ll = np.log(np.clip(lik, 1e-300, None))
    out = np.empty(len(o))
    for s in np.unique(o.student):
        idx = np.flatnonzero(o.student == s)
        tot = ll[idx].sum(axis=0)
        for i in idx:
            lw = LOGW + tot - ll[i]
            w = np.exp(lw - np.logaddexp.reduce(lw))
            out[i] = P[i] @ w
    return out


# ------------------------------------------------------------------------------------------------
# Fitting
# ------------------------------------------------------------------------------------------------
FIT_NAMES = ("sigma_eps", "shared_fit", "test_scale", "lapse")


def _pack(p: ModelParams) -> np.ndarray:
    return np.array([np.log(p.sigma_eps), logit(p.shared_fit), np.log(p.test_scale), logit(p.lapse)])


def _unpack(theta, base: ModelParams) -> ModelParams:
    return replace(base, sigma_eps=float(np.exp(theta[0])), shared_fit=float(expit(theta[1])),
                   test_scale=float(np.exp(theta[2])), lapse=float(expit(theta[3])))


@dataclass
class FitResult:
    params: ModelParams
    loglik: float
    n_obs: int
    n_students: int
    estimates: dict
    std_errors: dict  # on the natural scale, delta method
    converged: bool


def fit(schools: list[dict], o: Outcomes, base: ModelParams | None = None) -> FitResult:
    base = base or ModelParams()
    if not np.any(o.code == 2):
        base = replace(base, waitlist_width=0.0)  # no waitlist labels: every non-admit is a reject
    known = {s["id"] for s in schools if s.get("acceptanceRate")}
    o = o.subset(np.isin(o.school, list(known)))

    def nll(theta):
        try:
            return -marginal_loglik(AdmissionModel(schools, _unpack(theta, base)), o)
        except (ValueError, FloatingPointError):
            return 1e12

    bounds = [(np.log(0.2), np.log(5)), (logit(0.01), logit(0.95)), (np.log(0.1), np.log(5)), (logit(0.001), logit(0.4))]
    res = optimize.minimize(nll, _pack(base), method="L-BFGS-B", bounds=bounds)
    theta = res.x
    # observed-information standard errors via central-difference Hessian
    h, k = 1e-3, len(theta)
    H = np.zeros((k, k))
    f0 = nll(theta)
    for i in range(k):
        for j in range(i, k):
            ei, ej = np.eye(k)[i] * h, np.eye(k)[j] * h
            H[i, j] = H[j, i] = (nll(theta + ei + ej) - nll(theta + ei - ej) - nll(theta - ei + ej) + nll(theta - ei - ej)) / (4 * h * h)
    try:
        cov = np.linalg.inv(H)
        se_t = np.sqrt(np.clip(np.diag(cov), 0, None))
    except np.linalg.LinAlgError:
        se_t = np.full(k, np.nan)
    p = _unpack(theta, base)
    est = {n: getattr(p, n) for n in FIT_NAMES}
    # delta method: d natural / d transformed
    deriv = np.array([p.sigma_eps, p.shared_fit * (1 - p.shared_fit), p.test_scale, p.lapse * (1 - p.lapse)])
    se = {n: float(d * s) for n, d, s in zip(FIT_NAMES, deriv, se_t)}
    return FitResult(p, -f0, len(o), len(np.unique(o.student)), est, se, bool(res.success))


# ------------------------------------------------------------------------------------------------
# Scoring rules
# ------------------------------------------------------------------------------------------------
def brier(p, y):
    return float(np.mean((p - y) ** 2))


def log_loss(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def auc(p, y):
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    ranks = stats.rankdata(np.r_[pos, neg])
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def calibration_table(p, y, bins=10):
    order = np.argsort(p)
    chunks = np.array_split(order, bins)
    return [(float(p[c].mean()), float(y[c].mean()), len(c)) for c in chunks if len(c)]


def ece(p, y, bins=10):
    tab = calibration_table(p, y, bins)
    n = sum(t[2] for t in tab)
    return float(sum(t[2] / n * abs(t[0] - t[1]) for t in tab))


def score_all(p, y) -> dict:
    return {"brier": brier(p, y), "log_loss": log_loss(p, y), "auc": auc(p, y), "ece": ece(p, y)}


# ------------------------------------------------------------------------------------------------
# Synthetic data (for parameter recovery + misspecification stress tests)
# ------------------------------------------------------------------------------------------------
def simulate(schools: list[dict], params: ModelParams, n_students: int = 2000, apps: int = 8,
             seed: int = 0, misspecified: bool = False, rated_share: float = 0.0) -> Outcomes:
    """Draw applicants and decisions.

    misspecified=False: decisions drawn from exactly the fitted model's generative process.
    misspecified=True : a *different* world, to test robustness -
        * read noise is Student-t (df=3, heavy tails) instead of normal
        * each school's true test weight is perturbed by a random factor in [0.5, 1.5]
        * 4% of students are 'hooked' (athletes/legacies): admitted with prob 0.6 regardless
        * advisor holistic ratings (if any) are noisier than the model assumes
    """
    rng = np.random.default_rng(seed)
    model = AdmissionModel(schools, params)
    ids = model.usable()
    p = params
    cov = [[1, 0.7], [0.7, 1]]
    z = rng.multivariate_normal([0, 0], cov, n_students)
    ebrw = np.clip(np.round((650 + 85 * z[:, 0]) / 10) * 10, 200, 800)
    math = np.clip(np.round((660 + 95 * z[:, 1]) / 10) * 10, 200, 800)
    T = ebrw + math
    h = p.rho_th * (T - p.ref_mean) / p.ref_sd + np.sqrt(1 - p.rho_th ** 2) * rng.standard_normal(n_students)
    g = rng.standard_normal(n_students)
    hooked = rng.random(n_students) < (0.04 if misspecified else 0)
    tilt = {s: (rng.uniform(0.5, 1.5) if misspecified else 1.0) for s in ids}
    adm_mean = np.array([model.cal[s].adm_mean for s in ids])
    rows = {k: [] for k in ("student", "school", "ebrw", "math", "code", "hpct", "submitted")}
    rated = rng.random(n_students) < rated_share
    for i in range(n_students):
        # students apply where their composite is within reach: softmax on closeness to admitted mean
        w = np.exp(-((T[i] - adm_mean) / 120) ** 2) + 0.05
        chosen = rng.choice(len(ids), size=min(apps, len(ids)), replace=False, p=w / w.sum())
        for j in chosen:
            sid = ids[j]
            c = model.cal[sid]
            zt = (T[i] - c.m) / c.s
            idx = (tilt[sid] * c.a) * zt + p.holistic_weight * (h[i] - c.kappa) + np.sqrt(p.shared_fit) * p.sigma_eps * g[i]
            noise = rng.standard_t(3) / np.sqrt(3) if misspecified else rng.standard_normal()
            u = idx + np.sqrt(1 - p.shared_fit) * p.sigma_eps * noise
            if hooked[i]:
                code = int(rng.random() < 0.6)
            elif rng.random() < p.lapse:
                code = int(rng.random() < c.rate)
            else:
                wl = p.waitlist_width * np.sqrt(c.a ** 2 + p.holistic_weight ** 2 + p.sigma_eps ** 2)
                code = 1 if u > c.c else (2 if u > c.c - wl else 0)
            rows["student"].append(i)
            rows["school"].append(sid)
            rows["ebrw"].append(ebrw[i])
            rows["math"].append(math[i])
            rows["code"].append(code)
            noise_h = (1.0 if misspecified else 0.6) * rng.standard_normal()
            rows["hpct"].append(100 * stats.norm.cdf(h[i] + noise_h) if rated[i] else np.nan)
            rows["submitted"].append(True)
    return Outcomes(*(np.array(rows[k]) for k in ("student", "school", "ebrw", "math", "code", "hpct", "submitted")))
