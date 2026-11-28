"""The admissions model: a calibrated latent-index (probit) selection model with a shared factor.

Generative story, per school j
------------------------------
Within school j's applicant pool, every applicant has
    zT   standardized test composite (pool units)            ~ N(0, 1)
    zH   standardized non-test strength (grades, rigor, EC)  ~ N(0, 1)
    e_j  everything idiosyncratic to the read                ~ N(0, sigma_eps^2)
and is admitted iff  U_j = a_j*zT + b*zH + e_j  >  c_j.

a_j is the school's testing weight (from its Common Data Set "importance" label), b the holistic
weight. Two published numbers pin the school down:
  * acceptance rate r_j          ->  threshold c_j = Phi^-1(1 - r_j) * sqrt(a_j^2 + b^2 + sigma_eps^2)
  * admitted-class score band    ->  pool mean m_j and sd s_j of the composite, by inverting the
                                     truncated-normal selection moments (closed form, see
                                     `calibrate`):
        E[zT | admit]   = rho*lambda
        Var[zT | admit] = 1 - rho^2 * lambda*(lambda - k)
    with k = Phi^-1(1-r), lambda = phi(k)/r (inverse Mills ratio), rho = a/sqrt(a^2+b^2+sigma^2).
    So s_j = sd_adm / sqrt(1 - rho^2 lambda(lambda-k)),  m_j = mean_adm - s_j*rho*lambda.

Linking schools (this is where "accepted at A => probably at B" comes from)
-------------------------------------------------------------------------
The *same* student carries the same non-test strength h to every school, and the same essays/
recommendations, so decisions are correlated. We write the student's index as
    U_j = a_j*zT_j + b*(h - kappa_j) + sqrt(gamma)*sigma_eps*g + sqrt(1-gamma)*sigma_eps*e_j
  zT_j     their composite standardized against pool j: (T - m_j)/s_j   (known)
  kappa_j  how much stronger pool j is on non-test strength than the reference pool, tied to how
           much stronger it is on tests: kappa_j = rho_th * (m_j - ref_mean)/ref_sd
  g        a shared "application quality" factor (essays, recs read similarly everywhere)
  gamma    fraction of the read noise that is shared across schools
Collapse the shared parts into one latent S = b*h + sqrt(gamma)*sigma_eps*g ~ N(b*mu_h, b^2 sd_h^2 +
gamma*sigma_eps^2). Conditional on S decisions are independent, so every joint quantity is a
1-D integral over S, done on a dense grid (exact to grid precision, no Monte Carlo noise):
    P(admit_j | S) = Phi((a_j zT_j - b kappa_j - c_j + S) / (sqrt(1-gamma) sigma_eps))
Observed decisions update the distribution of S by Bayes' rule on that grid; predictions for the
remaining schools then integrate over the posterior.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
from scipy import stats
from scipy.special import ndtr

from .scores import fit_school

IMPORTANCE_WEIGHT = {"Very Important": 1.0, "Important": 0.8, "Considered": 0.5, "Not Considered": 0.0}


@dataclass(frozen=True)
class ModelParams:
    test_weight: dict = field(default_factory=lambda: dict(IMPORTANCE_WEIGHT))
    test_scale: float = 1.0      # global multiplier on all a_j (fitted by `fit`)
    holistic_weight: float = 1.0  # b; fixes the scale of the latent index
    sigma_eps: float = 1.0       # sd of everything not captured by tests + non-test strength
    shared_fit: float = 0.3      # gamma: share of read noise common to all of a student's schools
    rho_th: float = 0.4          # pool test level -> pool non-test strength linkage
    ref_mean: float = 1300.0     # reference pool composite mean (h is measured against this pool)
    ref_sd: float = 180.0
    rho_em: float = 0.6          # EBRW-Math correlation inside an admitted class
    enrolled_shift: float = 0.0  # composite points to add to published (enrolled) bands -> admitted
    withheld_z: float = -0.25    # pool-standardized test level a school imputes to a non-submitter
    waitlist_width: float = 0.25  # waitlist band below the threshold, in pool-index sd units
    lapse: float = 0.05          # omega: share of each decision unexplained by the index (hooks,
                                 # institutional priorities, data error). Mixture with base rate.
    grid_size: int = 801

    def weight(self, importance: str) -> float:
        return self.test_scale * self.test_weight[importance]


@dataclass(frozen=True)
class Calibration:
    school_id: str
    name: str
    ok: bool
    reason: str = ""
    rate: float = float("nan")
    a: float = float("nan")
    c: float = float("nan")
    m: float = float("nan")    # pool composite mean
    s: float = float("nan")    # pool composite sd
    kappa: float = float("nan")
    adm_mean: float = float("nan")
    adm_sd: float = float("nan")
    test_optional: bool = False


def calibrate(school: dict, p: ModelParams) -> Calibration:
    sid, name = school["id"], school["name"]
    r = school.get("acceptanceRate")
    if r is None or not (0 < r < 1):
        return Calibration(sid, name, False, "no acceptance rate in catalog")
    try:
        comp = fit_school(school, p.rho_em)
    except ValueError as exc:
        return Calibration(sid, name, False, str(exc))
    mu_a, sd_a = comp.moments()
    mu_a += p.enrolled_shift
    a = p.weight(school["importance"])
    b = p.holistic_weight
    V = a * a + b * b + p.sigma_eps ** 2
    k = stats.norm.isf(r)
    lam = stats.norm.pdf(k) / r
    rho = a / np.sqrt(V)
    shrink = 1 - rho ** 2 * lam * (lam - k)
    s = sd_a / np.sqrt(shrink)
    m = mu_a - s * rho * lam
    kappa = p.rho_th * (m - p.ref_mean) / p.ref_sd
    return Calibration(sid, name, True, "", r, a, k * np.sqrt(V), m, s, kappa, mu_a, sd_a,
                       bool(school.get("testOptional")))


@dataclass(frozen=True)
class Student:
    ebrw: float
    math: float
    holistic_mean: float | None = None  # h, sd units vs the reference pool. None = infer from tests
    holistic_sd: float | None = None    # None = residual uncertainty given tests; ~0.6 = advisor-rated

    @property
    def composite(self) -> float:
        return self.ebrw + self.math

    @staticmethod
    def from_percentile(ebrw, math, pct: float | None, sd: float | None = None) -> "Student":
        if pct is None:
            return Student(ebrw, math, None, sd)
        return Student(ebrw, math, float(stats.norm.ppf(np.clip(pct / 100, 0.001, 0.999))), 0.6 if sd is None else sd)


DECISION_CODES = {"accepted": 1, "admitted": 1, "rejected": 0, "denied": 0, "waitlisted": 2, "deferred": 2}


class AdmissionModel:
    def __init__(self, schools: list[dict], params: ModelParams | None = None):
        self.params = params or ModelParams()
        self.schools = {s["id"]: s for s in schools}
        self.cal = {s["id"]: calibrate(s, self.params) for s in schools}

    def with_params(self, **kw) -> "AdmissionModel":
        return AdmissionModel(list(self.schools.values()), replace(self.params, **kw))

    def usable(self, ids=None) -> list[str]:
        ids = list(self.schools) if ids is None else ids
        return [i for i in ids if i in self.cal and self.cal[i].ok]

    # ---- per-school linear index ------------------------------------------------------------
    def offset(self, student: Student, sid: str, submit: bool = True) -> float:
        """a*zT - b*kappa - c : the student-specific, S-free part of the index."""
        c = self.cal[sid]
        zt = (student.composite - c.m) / c.s if submit else self.params.withheld_z
        return c.a * zt - self.params.holistic_weight * c.kappa - c.c

    def submit_policy(self, student: Student, sid: str) -> bool:
        """Submit scores iff that raises P(admit) (test-optional schools only)."""
        c = self.cal[sid]
        if not c.test_optional:
            return True
        return self.offset(student, sid, True) >= self.offset(student, sid, False)

    def offsets(self, student: Student, ids: list[str], policy: str = "auto") -> np.ndarray:
        out = []
        for sid in ids:
            submit = {"auto": None, "always": True, "never": False}[policy]
            if submit is None or not self.cal[sid].test_optional:
                submit = self.submit_policy(student, sid) if submit is None else True
            out.append(self.offset(student, sid, submit))
        return np.array(out)

    # ---- the shared-factor grid ---------------------------------------------------------------
    def holistic_prior(self, student: Student) -> tuple[float, float]:
        """Prior on h. Unrated: E[h | T] = rho_th * (T - ref_mean)/ref_sd, sd = sqrt(1 - rho_th^2),
        the same test/non-test linkage used for pools (kappa), applied to the individual."""
        p = self.params
        mean = student.holistic_mean
        if mean is None:
            mean = p.rho_th * (student.composite - p.ref_mean) / p.ref_sd
        sd = student.holistic_sd
        if sd is None:
            sd = float(np.sqrt(1 - p.rho_th ** 2)) if student.holistic_mean is None else 0.6
        return float(mean), float(sd)

    def shared_prior(self, student: Student) -> tuple[float, float]:
        p = self.params
        b = p.holistic_weight
        hm, hs = self.holistic_prior(student)
        return b * hm, float(np.sqrt((b * hs) ** 2 + p.shared_fit * p.sigma_eps ** 2))

    def grid(self, student: Student) -> tuple[np.ndarray, np.ndarray]:
        mu, sd = self.shared_prior(student)
        z = np.linspace(-8, 8, self.params.grid_size)
        logw = stats.norm.logpdf(z)
        logw -= np.logaddexp.reduce(logw)
        return mu + sd * z, logw

    @property
    def idio_sd(self) -> float:
        return float(np.sqrt(1 - self.params.shared_fit) * self.params.sigma_eps)

    def prob_grid(self, student: Student, ids: list[str], policy="auto") -> tuple[np.ndarray, np.ndarray]:
        S, logw = self.grid(student)
        x = self.offsets(student, ids, policy)
        return self._mix(ids, ndtr((x[:, None] + S[None, :]) / self.idio_sd)), logw

    def _mix(self, ids, p_index):
        """Lapse mixture: P = (1-omega)*Phi(index) + omega*base_rate. Marginal pool rate unchanged."""
        om = self.params.lapse
        r = np.array([self.cal[i].rate for i in ids])[:, None]
        return (1 - om) * p_index + om * r

    def decision_loglik(self, student: Student, ids: list[str], codes: list[int], policy="auto") -> np.ndarray:
        """log P(observed decisions | S) on the grid. Codes: 1 admit, 0 reject, 2 waitlist/defer."""
        S, _ = self.grid(student)
        x = self.offsets(student, ids, policy)[:, None] + S[None, :]
        sd = self.idio_sd
        wl = self.params.waitlist_width * np.sqrt(np.array([self.cal[i].a ** 2 for i in ids]) +
                                                  self.params.holistic_weight ** 2 + self.params.sigma_eps ** 2)[:, None]
        codes = np.array(codes)[:, None]
        om = self.params.lapse
        r = np.array([self.cal[i].rate for i in ids])[:, None]
        p_admit = (1 - om) * ndtr(x / sd) + om * r
        # three mutually exclusive outcomes (they sum to 1; lapse decisions are admit/reject only):
        #   admit    U > c                 waitlist  c - w < U < c        reject  U < c - w
        ll_admit = np.log(np.clip(p_admit, 1e-300, None))
        ll_reject = np.log(np.clip((1 - om) * ndtr(-(x + wl) / sd) + om * (1 - r), 1e-300, None))
        band = ndtr(-x / sd) - ndtr(-(x + wl) / sd)
        ll_wait = np.log(np.clip((1 - om) * band, 1e-300, None))
        ll = np.where(codes == 1, ll_admit, np.where(codes == 0, ll_reject, ll_wait))
        return ll.sum(axis=0)

    def posterior_logw(self, student: Student, decisions: dict[str, str], policy="auto") -> np.ndarray:
        _, logw = self.grid(student)
        ids = [i for i in decisions if i in self.cal and self.cal[i].ok]
        if not ids:
            return logw
        post = logw + self.decision_loglik(student, ids, [DECISION_CODES[decisions[i]] for i in ids], policy)
        return post - np.logaddexp.reduce(post)

    # ---- queries ------------------------------------------------------------------------------
    def chances(self, student: Student, ids: list[str], decisions: dict | None = None, policy="auto") -> np.ndarray:
        P, logw = self.prob_grid(student, ids, policy)
        if decisions:
            logw = self.posterior_logw(student, decisions, policy)
        return P @ np.exp(logw)

    def chances_interval(self, student: Student, ids, decisions=None, level=0.8, policy="auto"):
        """Spread of P(admit) across the (posterior) uncertainty in the shared factor S."""
        P, logw = self.prob_grid(student, ids, policy)
        if decisions:
            logw = self.posterior_logw(student, decisions, policy)
        cdf = np.cumsum(np.exp(logw))
        lo_i, hi_i = np.searchsorted(cdf, (1 - level) / 2), np.searchsorted(cdf, (1 + level) / 2)
        return P[:, min(lo_i, P.shape[1] - 1)], P[:, min(hi_i, P.shape[1] - 1)]

    def cross_matrix(self, student: Student, ids: list[str], given: str = "accepted", policy="auto") -> np.ndarray:
        """M[i, j] = P(admit j | outcome `given` at i). Diagonal = marginal P(admit i)."""
        P, logw = self.prob_grid(student, ids, policy)
        w = np.exp(logw)
        cond = P if given == "accepted" else 1 - P
        joint = (cond * w) @ P.T          # [i, j] = E[cond_i * p_j]
        M = joint / (cond @ w)[:, None]
        np.fill_diagonal(M, P @ w)
        return M

    def independent_cross_matrix(self, student, ids, policy="auto"):
        """What you'd get assuming decisions are independent: rows all equal the marginals."""
        m = self.chances(student, ids, policy=policy)
        return np.tile(m, (len(ids), 1))

    def count_distribution(self, student: Student, ids: list[str], decisions=None, policy="auto") -> np.ndarray:
        """P(exactly n admits) for n = 0..J: Poisson-binomial on each grid node, mixed over S."""
        P, logw = self.prob_grid(student, ids, policy)
        if decisions:
            logw = self.posterior_logw(student, decisions, policy)
        dist = np.zeros((len(ids) + 1, P.shape[1]))
        dist[0] = 1.0
        for p in P:
            dist[1:] = dist[1:] * (1 - p) + dist[:-1] * p
            dist[0] *= 1 - p
        return dist @ np.exp(logw)

    def expected_best(self, student: Student, ids: list[str], utility: dict[str, float],
                      fallback: float = 0.0, decisions=None, policy="auto") -> float:
        """E[utility of the best school you're admitted to] (fallback if none)."""
        if not ids:
            return fallback
        order = sorted(ids, key=lambda i: -utility[i])
        P, logw = self.prob_grid(student, order, policy)
        if decisions:
            logw = self.posterior_logw(student, decisions, policy)
        none_above = np.ones(P.shape[1])
        val = np.zeros(P.shape[1])
        for sid, p in zip(order, P):
            val += utility[sid] * p * none_above
            none_above *= 1 - p
        val += fallback * none_above
        return float(val @ np.exp(logw))

    def shared_posterior_summary(self, student: Student, decisions: dict) -> tuple[float, float, float, float]:
        """(prior mean, prior sd, posterior mean, posterior sd) of the shared factor S."""
        S, logw = self.grid(student)
        post = self.posterior_logw(student, decisions)
        w0, w1 = np.exp(logw), np.exp(post)
        m0, m1 = S @ w0, S @ w1
        return float(m0), float(np.sqrt(((S - m0) ** 2) @ w0)), float(m1), float(np.sqrt(((S - m1) ** 2) @ w1))

    def p_none_range(self, student: Student, ids: list[str], decisions=None) -> tuple[float, float, float]:
        """(low, central, high) P(no admits) across plausible link strengths and lapse rates. The misspecified
        backtest showed the central value can over-warn ~2x when the world has hooks and heavy tails, so the
        honest output is a range, not one number."""
        from dataclasses import replace as _rep
        vals = []
        hm, hs = self.holistic_prior(student)
        for gamma in (0.05, 0.3, 0.5):
            for lapse in (0.02, 0.05, 0.10):
                for hsd in (0.5 * hs, hs):  # how much of the applicant's non-test strength is unknown
                    m = self.with_params(shared_fit=gamma, lapse=lapse)
                    st = _rep(student, holistic_mean=hm, holistic_sd=hsd)
                    vals.append(float(m.count_distribution(st, ids, decisions)[0]))
        return min(vals), float(self.count_distribution(student, ids, decisions)[0]), max(vals)

