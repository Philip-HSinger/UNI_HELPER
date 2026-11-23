"""Is it better than chance? Uncertainty quantification for every backtest claim.

Two questions, kept separate:
  (1) Is the model better than a no-information forecast (coin flip / the school's base rate)?
  (2) Is an observed advantage bigger than what sampling luck alone would produce?
For (2) the unit of resampling is the *student*, not the application row: one student's eight
decisions are correlated, so treating rows as independent would overstate significance.
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def cluster_bootstrap_diff(loss_a, loss_b, clusters, B: int = 4000, seed: int = 0) -> dict:
    """Mean of (loss_a - loss_b) with a student-cluster bootstrap 95% CI and two-sided p-value.
    Negative = A has lower loss = A is better."""
    loss_a, loss_b, clusters = map(np.asarray, (loss_a, loss_b, clusters))
    d = loss_a - loss_b
    ids, inv = np.unique(clusters, return_inverse=True)
    sums = np.bincount(inv, weights=d)
    counts = np.bincount(inv)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(ids), size=(B, len(ids)))
    boot = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    est = d.mean()
    # p-value: centered bootstrap (H0: mean diff = 0)
    p = float(np.mean(np.abs(boot - est) >= abs(est)))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"diff": float(est), "ci95": [float(lo), float(hi)], "p": max(p, 1 / B), "n_clusters": int(len(ids)),
            "relative": float(est / loss_b.mean()) if loss_b.mean() else float("nan")}


def auc_test(p, y) -> dict:
    """AUC with Mann-Whitney test of H0: AUC = 0.5 (no better than random ordering)."""
    p, y = np.asarray(p), np.asarray(y)
    res = stats.mannwhitneyu(p[y == 1], p[y == 0], alternative="greater")
    auc = res.statistic / ((y == 1).sum() * (y == 0).sum())
    return {"auc": float(auc), "p_vs_random": float(res.pvalue)}


def wilson(k: int, n: int, z: float = 1.96) -> list[float]:
    if n == 0:
        return [0.0, 1.0]
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return [float(c - h), float(c + h)]


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> list[float]:
    lo = stats.beta.ppf(alpha / 2, k, n - k + 1) if k > 0 else 0.0
    hi = stats.beta.ppf(1 - alpha / 2, k + 1, n - k) if k < n else 1.0
    return [float(lo), float(hi)]


def poisson_binomial_test(ps, k_obs: int) -> dict:
    """Exact test: is observing k_obs successes consistent with independent Bernoulli(ps)?"""
    dist = np.array([1.0])
    for p in ps:
        dist = np.r_[dist * (1 - p), 0] + np.r_[0, dist * p]
    p_ge = float(dist[k_obs:].sum())
    p_le = float(dist[: k_obs + 1].sum())
    return {"expected": float(np.sum(ps)), "observed": int(k_obs), "p_two_sided": float(min(1.0, 2 * min(p_ge, p_le)))}


def permutation_spearman(x, y, n_perm: int = 20000, seed: int = 0) -> dict:
    x, y = np.asarray(x), np.asarray(y)
    rho = stats.spearmanr(x, y).statistic
    rng = np.random.default_rng(seed)
    null = np.array([stats.spearmanr(x, rng.permutation(y)).statistic for _ in range(n_perm)])
    return {"rho": float(rho), "p_one_sided": float((np.sum(null >= rho) + 1) / (n_perm + 1))}


def paired_tests(err_a, err_b) -> dict:
    """Paired comparison of two error vectors (A - B; negative = A better): t-test, Wilcoxon, bootstrap CI."""
    d = np.asarray(err_a) - np.asarray(err_b)
    t = stats.ttest_1samp(d, 0)
    w = stats.wilcoxon(d)
    rng = np.random.default_rng(0)
    boot = rng.choice(d, size=(4000, len(d))).mean(axis=1)
    return {"diff": float(d.mean()), "ci95": [float(x) for x in np.percentile(boot, [2.5, 97.5])],
            "p_t": float(t.pvalue), "p_wilcoxon": float(w.pvalue), "share_a_better": float(np.mean(d < 0)), "n": int(len(d))}
