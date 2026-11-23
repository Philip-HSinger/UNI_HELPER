"""Score-distribution modelling: turning a published 25/50/75 band into a full distribution.

Why not "just a normal through the IQR" (what the web app does)?
  1. Bands at selective schools are skewed (e.g. 740/760/770): a symmetric normal cannot hit all
     three published quantiles. We fit a *two-piece (split) normal* that reproduces all three
     exactly when they are interior.
  2. Bands are censored at the 800 section ceiling (e.g. MIT math 780/800/800). A quantile equal
     to 800 only says "at least 25% of students are at the ceiling", so it is treated as an
     inequality, not a data point. The latent (uncapped) distribution is fitted from the
     uncensored quantiles and then capped.
  3. Scores are reported on a 10-point grid, so a student's percentile is the *mid-rank* of their
     10-point bin, P(X < x) + 0.5 P(X = x), which is what makes "800 at a school whose 75th is
     800" come out near the 75th-90th percentile rather than a meaningless 100.
  4. A single sitting is a noisy measurement (College Board-style SEM ~30 per section). Percentile
     is monotone in score, so a credible interval on the percentile is exactly the percentiles
     of the endpoints of the score interval.
  5. A composite (EBRW+Math) distribution is NOT the sum of section bands: the sections are
     correlated but imperfectly, so the composite spread is narrower than the summed IQR. We
     combine the two fitted section marginals with a Gaussian copula (correlation rho_em) and
     integrate numerically.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import optimize, stats

SECTION_MIN, SECTION_MAX = 200.0, 800.0
Z25, Z75 = stats.norm.ppf(0.25), stats.norm.ppf(0.75)  # +-0.6745
DEFAULT_SECTION_SD = 40.0  # fallback when censoring leaves the spread unidentified
SCORE_STEP = 10.0


@dataclass(frozen=True)
class SplitNormal:
    """Quantile-matched two-piece normal, capped to [lo, hi].

    Below the median `mu` the latent score is a half-normal of scale `sl`, above it a half-normal
    of scale `sr`, each carrying exactly 50% of the mass. With sl = (q50-q25)/0.6745 and
    sr = (q75-q50)/0.6745 it reproduces any published 25/50/75 band *exactly*, however skewed
    (a density-continuous split normal or a skew-normal cannot: their attainable quantile
    asymmetry is bounded, and real bands like 740/760/770 fall outside it).
    """

    mu: float
    sl: float
    sr: float
    lo: float = SECTION_MIN
    hi: float = SECTION_MAX
    method: str = "exact"

    def latent_cdf(self, x):
        x = np.asarray(x, dtype=float)
        return np.where(x < self.mu, stats.norm.cdf((x - self.mu) / self.sl), stats.norm.cdf((x - self.mu) / self.sr))

    def latent_ppf(self, p):
        z = stats.norm.ppf(np.asarray(p, dtype=float))
        return self.mu + np.where(z < 0, self.sl, self.sr) * z

    def cdf(self, x):
        """CDF of the *capped* score: point masses at lo and hi."""
        x = np.asarray(x, dtype=float)
        return np.where(x >= self.hi, 1.0, np.where(x < self.lo, 0.0, self.latent_cdf(x)))

    def ppf(self, p):
        return np.clip(self.latent_ppf(p), self.lo, self.hi)

    def mid_rank(self, score: float, step: float = SCORE_STEP) -> float:
        """Percentile (0-1) of a score reported on a `step` grid: P(X < bin) + 0.5 P(X in bin)."""
        below = float(self.cdf(score - step / 2)) if score - step / 2 >= self.lo else 0.0
        upto = 1.0 if score + step / 2 >= self.hi else float(self.cdf(score + step / 2))
        return 0.5 * (below + upto)

    def moments(self) -> tuple[float, float]:
        """Mean and sd of the capped distribution (numerical, via quantile grid)."""
        u = (np.arange(4000) + 0.5) / 4000
        x = self.ppf(u)
        return float(x.mean()), float(x.std())


MIN_SCALE = 7.5  # a 10-point-rounded quartile gap of 0 still means spread of ~ half a grid step


def fit_band(q25: float, q50: float, q75: float, lo: float = SECTION_MIN, hi: float = SECTION_MAX,
             fallback_sd: float = DEFAULT_SECTION_SD) -> SplitNormal:
    """Fit a capped two-piece normal to a published (25th, 50th, 75th) band.

    Cases, by how many quantiles sit strictly below the ceiling:
      q75 < hi  -> exact: both scales from the two quartile gaps
      q50 < hi  -> left scale from q50-q25; right scale unidentified, so it is set to the left
                   scale but widened if needed to satisfy the censoring inequality P(X >= hi) >= 25%
      q50 == hi -> only q25 interior: scale from `fallback_sd` (a prior), latent median pushed to
                   >= hi so that P(X >= hi) >= 50%
    """
    if not (q25 <= q50 <= q75):
        raise ValueError(f"band not ordered: {q25}/{q50}/{q75}")
    zq = -Z25  # 0.6745
    if q75 < hi:
        return SplitNormal(q50, max((q50 - q25) / zq, MIN_SCALE), max((q75 - q50) / zq, MIN_SCALE), lo, hi, "exact")
    if q50 < hi:
        sl = max((q50 - q25) / zq, MIN_SCALE)
        sr = max(sl, (hi - q50) / zq)
        return SplitNormal(q50, sl, sr, lo, hi, "censored-top")
    sd = fallback_sd
    mu = max(q25 + zq * sd, hi)
    return SplitNormal(mu, (mu - q25) / zq, sd, lo, hi, "censored-prior")


def percentile_with_interval(dist: SplitNormal, score: float, sem: float = 30.0, level: float = 0.90):
    """(point, low, high) percentile in 0-100, the interval reflecting test measurement error."""
    z = stats.norm.ppf(0.5 + level / 2)
    lo_s = max(SECTION_MIN, score - z * sem)
    hi_s = min(SECTION_MAX, score + z * sem)
    return (100 * dist.mid_rank(score), 100 * dist.mid_rank(lo_s), 100 * dist.mid_rank(hi_s))


@dataclass(frozen=True)
class CompositeDist:
    """EBRW+Math composite via Gaussian copula of the two fitted section marginals."""

    ebrw: SplitNormal
    math: SplitNormal
    rho: float = 0.6
    n: int = 400

    def _grid(self):
        u = (np.arange(self.n) + 0.5) / self.n
        return u, self.ebrw.ppf(u), stats.norm.ppf(u)

    def cdf(self, x: float) -> float:
        """P(E + M <= x) = E_E[ P(M <= x - E | E) ] under the copula."""
        u, e, ze = self._grid()
        m_cap = x - e
        # P(M <= m | E=e): Gaussian-copula conditional. Ceiling: M <= 800 always.
        fm = np.clip(self.math.cdf(m_cap), 1e-12, 1 - 1e-12)
        cond = stats.norm.cdf((stats.norm.ppf(fm) - self.rho * ze) / np.sqrt(1 - self.rho ** 2))
        cond = np.where(m_cap >= self.math.hi, 1.0, np.where(m_cap < self.math.lo, 0.0, cond))
        return float(cond.mean())

    def mid_rank(self, score: float) -> float:
        # composite of two 10-point grids lives on a 10-point grid as well
        return 0.5 * (self.cdf(score - 5) + (1.0 if score + 5 >= 1600 else self.cdf(score + 5)))

    def quantile(self, p: float) -> float:
        return float(optimize.brentq(lambda x: self.cdf(x) - p, 399, 1601, xtol=0.01))

    def moments(self) -> tuple[float, float]:
        """Mean/sd of the composite. Pearson corr of the capped sections ~= rho (copula approx)."""
        me, se = self.ebrw.moments()
        mm, sm = self.math.moments()
        return me + mm, float(np.sqrt(se ** 2 + sm ** 2 + 2 * self.rho * se * sm))


def fit_school(school: dict, rho_em: float = 0.6) -> CompositeDist:
    e = fit_band(school["englishP25"], school["englishP50"], school["englishP75"])
    m = fit_band(school["mathP25"], school["mathP50"], school["mathP75"])
    return CompositeDist(e, m, rho_em)
