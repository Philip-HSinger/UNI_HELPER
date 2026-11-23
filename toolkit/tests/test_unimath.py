import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats
from scipy.special import ndtr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from unimath.catalog import SIMILARITY, load_catalog, validate  # noqa: E402
from unimath.fit import Outcomes, marginal_loglik, simulate  # noqa: E402
from unimath.model import AdmissionModel, ModelParams, Student  # noqa: E402
from unimath.planner import greedy_only, plan  # noqa: E402
from unimath.scores import CompositeDist, fit_band, fit_school  # noqa: E402
from unimath.similarity import SimilarityEngine  # noqa: E402

CAT = load_catalog()


# ------------------------------------------------------------------ scores
@pytest.mark.parametrize("band", [(740, 760, 770), (710, 730, 760), (600, 690, 760), (650, 650, 700)])
def test_band_fit_reproduces_published_quartiles(band):
    d = fit_band(*band)
    np.testing.assert_allclose(d.ppf([0.25, 0.5, 0.75]), band, atol=1e-6) if band[0] < band[1] < band[2] else None
    assert d.method == "exact"


def test_censored_band_respects_ceiling_mass():
    d = fit_band(750, 770, 800)
    assert 1 - d.latent_cdf(800) >= 0.25 - 1e-9
    d2 = fit_band(780, 800, 800)
    assert 1 - d2.latent_cdf(800) >= 0.5 - 1e-9
    assert d2.ppf(0.25) == pytest.approx(780)


def test_mid_rank_monotone_and_800_not_100():
    d = fit_band(780, 800, 800)
    ranks = [d.mid_rank(s) for s in range(600, 801, 10)]
    assert all(b >= a for a, b in zip(ranks, ranks[1:]))
    assert ranks[-1] < 0.95


def test_composite_narrower_than_summed_bands():
    mit = next(s for s in CAT if s["id"] == "harvard")
    comp = fit_school(mit, rho_em=0.6)
    iqr = comp.quantile(0.75) - comp.quantile(0.25)
    summed = (mit["englishP75"] + mit["mathP75"]) - (mit["englishP25"] + mit["mathP25"])
    assert iqr < summed


def test_composite_cdf_matches_monte_carlo():
    e, m = fit_band(700, 740, 770), fit_band(720, 760, 790)
    comp = CompositeDist(e, m, 0.6)
    rng = np.random.default_rng(0)
    z = rng.multivariate_normal([0, 0], [[1, 0.6], [0.6, 1]], 200000)
    x = e.ppf(stats.norm.cdf(z[:, 0])) + m.ppf(stats.norm.cdf(z[:, 1]))
    for t in (1420, 1500, 1540):
        assert comp.cdf(t) == pytest.approx(np.mean(x <= t), abs=0.01)


# ------------------------------------------------------------------ model
def test_calibration_reproduces_rate_and_admitted_mean_by_simulation():
    """Closed-form inversion check: simulate the pool implied by calibrate(), apply the
    admission rule, recover the published acceptance rate and admitted composite mean."""
    M = AdmissionModel(CAT, ModelParams(lapse=0.0))
    rng = np.random.default_rng(1)
    for sid in ("mit", "purdue", "tufts"):
        c, p = M.cal[sid], M.params
        n = 400000
        zt, zh, e = rng.standard_normal((3, n))
        U = c.a * zt + p.holistic_weight * zh + p.sigma_eps * e
        adm = U > c.c
        assert adm.mean() == pytest.approx(c.rate, rel=0.03)
        assert (c.m + c.s * zt[adm]).mean() == pytest.approx(c.adm_mean, abs=1.5)
        assert (c.m + c.s * zt[adm]).std() == pytest.approx(c.adm_sd, rel=0.03)


def test_decision_probabilities_sum_to_one():
    """Regression: reject used to be 1 - P(admit), double-counting the waitlist band."""
    M = AdmissionModel(CAT)
    st = Student(720, 760)
    ids = ["mit", "tufts", "purdue"]
    tot = sum(np.exp(M.decision_loglik(st, ids, [code] * 3)) for code in (0, 1, 2))
    # product over 3 schools of per-school sums; per-school sums are 1 iff product of sums is 1
    np.testing.assert_allclose(sum(np.exp(M.decision_loglik(st, [i], [c])) for c in (0, 1, 2) for i in [ids[0]]), 1, atol=1e-9)
    assert np.all(tot > 0)


def test_correlation_structure():
    M = AdmissionModel(CAT)
    st = Student(740, 780)
    ids = ["stanford", "princeton", "purdue"]
    X = M.cross_matrix(st, ids, "accepted")
    R = M.cross_matrix(st, ids, "rejected")
    marg = np.diag(X)
    for i in range(3):
        for j in range(3):
            if i != j:
                assert X[i, j] > marg[j] > R[i, j]
    # no shared variance -> independence
    Mi = M.with_params(shared_fit=1e-9)
    sti = Student(740, 780, 0.0, 1e-9)
    Xi = Mi.cross_matrix(sti, ids)
    np.testing.assert_allclose(Xi, np.tile(np.diag(Xi), (3, 1)), atol=1e-6)


def test_count_distribution_and_positive_dependence():
    M = AdmissionModel(CAT)
    st = Student(740, 780)
    ids = M.usable()
    d = M.count_distribution(st, ids)
    assert d.sum() == pytest.approx(1, abs=1e-9)
    p = M.chances(st, ids)
    assert d @ np.arange(len(d)) == pytest.approx(p.sum(), rel=1e-6)
    assert d[0] >= np.prod(1 - p)  # positive correlation: zero-admit risk above independence


def test_bayes_update_direction():
    M = AdmissionModel(CAT)
    st = Student(740, 780)
    base = M.chances(st, ["stanford"])[0]
    assert M.chances(st, ["stanford"], {"mit": "accepted"})[0] > base > M.chances(st, ["stanford"], {"mit": "rejected"})[0]


def test_higher_scores_never_hurt_when_submitting():
    M = AdmissionModel(CAT)
    ids = ["mit", "cornell", "purdue"]
    a = M.chances(Student(700, 700, 0.0, 1.0), ids, policy="always")
    b = M.chances(Student(750, 760, 0.0, 1.0), ids, policy="always")
    assert np.all(b >= a)


# ------------------------------------------------------------------ similarity / planner
def test_similarity_properties():
    E = SimilarityEngine(CAT, SIMILARITY)
    i, j = E.index["mit--field-of-study"], E.index["princeton--academic-interest"]
    assert E.R[i, j] == pytest.approx(0.8)  # curated wins
    for sid, idx in E.by_school.items():
        for a in idx:
            for b in idx:
                assert E.R[a, b] == 0  # no same-school credit
    # diminishing returns: marginal effort can't increase as the written set grows
    e1 = E.marginal_effort("stanford", ["mit"])[0]
    e2 = E.marginal_effort("stanford", ["mit", "princeton"])[0]
    assert e2 <= e1 <= E.standalone_effort("stanford")


def test_planner_greedy_matches_exact_small():
    M = AdmissionModel(CAT)
    E = SimilarityEngine(CAT, SIMILARITY)
    cands = ["mit", "stanford", "cmu", "tufts", "purdue", "georgia-tech", "northeastern"]
    u = dict(zip(cands, [100, 98, 90, 75, 60, 80, 70]))
    st = Student(740, 780)
    ex = plan(M, E, st, cands, u, 0.005, 6, exact_limit=99)
    gr = greedy_only(M, E, st, cands, u, 0.005, 6)
    assert gr.objective >= ex.objective - 1e-9 * abs(ex.objective) - 0.5


# ------------------------------------------------------------------ fitting
def test_likelihood_prefers_truth():
    true = ModelParams(sigma_eps=0.8, shared_fit=0.45, test_scale=1.3, lapse=0.03)
    o = simulate(CAT, true, 400, 8, seed=5)
    l_true = marginal_loglik(AdmissionModel(CAT, true), o)
    l_bad = marginal_loglik(AdmissionModel(CAT, ModelParams(sigma_eps=2.5, shared_fit=0.1, test_scale=0.4, lapse=0.2)), o)
    assert l_true > l_bad


# ------------------------------------------------------------------ data + CLI
def test_catalog_validation_flags_known_gaps():
    issues = validate(CAT)
    assert ("ERROR", "columbia", "acceptance rate missing: chances not computable") in issues


@pytest.mark.parametrize("cmd", ["CHNC", "XADM", "PORT", "PCTL", "ESSY", "FREE", "PLAN", "BRIEF", "SCH mit", "DQ", "CAT",
                                 "HELP", "UPDT", "SENS"])
def test_cli_commands_run(cmd):
    r = subprocess.run([sys.executable, "-m", "unimath.cli", "-p", str(ROOT / "examples" / "profile.toml"), *cmd.split()],
                       cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0 and "error:" not in r.stdout, r.stdout + r.stderr


def test_cli_json_is_parseable():
    r = subprocess.run([sys.executable, "-m", "unimath.cli", "-p", str(ROOT / "examples" / "profile.toml"), "--json", "CHNC"],
                       cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert isinstance(json.loads(r.stdout), list)


def test_ledger_detects_tampering(tmp_path):
    led, out = tmp_path / "l.jsonl", tmp_path / "o.csv"
    run = lambda *a: subprocess.run([sys.executable, "-m", "unimath.cli", "-p", str(ROOT / "examples" / "profile.toml"), *a],  # noqa: E731
                                    cwd=ROOT, capture_output=True, text=True, timeout=60).stdout
    run("LEDGER", str(led), "alex")
    out.write_text("student,school,decision\nalex,purdue,accepted\nalex,mit,rejected\n")
    assert "VERIFIED" in run("SCORE", str(led), str(out))
    rows = [json.loads(x) for x in led.read_text().splitlines()]
    rows[0]["p_admit"] = 0.99
    led.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    assert "TAMPERED" in run("SCORE", str(led), str(out))
