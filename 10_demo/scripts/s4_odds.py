"""Step 4: admission odds on the verified Common Data Set figures, with Bayesian updates after early results.
Writes outputs/odds.json. Uses the toolkit's AdmissionModel unchanged; only the school data are new."""
import sys

import numpy as np

from common import IDS, OUT, ROOT, SHORT, TOOLKIT, load, save

sys.path.insert(0, str(TOOLKIT))
from unimath.model import AdmissionModel, Student  # noqa: E402

STUDENT = {"ebrw": 710, "math": 710}
ED = "tufts"
EA = ["northeastern", "fordham-university", "fairfield-university", "university-of-massachusetts-amherst",
      "university-of-rhode-island"]
SIX = ["tufts", "boston-college", "northeastern", "boston-university", "college-of-the-holy-cross", "fairfield-university"]

schools = {s["school_id"]: s for s in load(ROOT / "data" / "schools.json")}


def entry(sid, rate=None):
    st = schools[sid]["stats"]
    e, m = st["sat_ebrw"], st["sat_math"]
    pol = (st.get("test_policy_2026_27") or "").lower()
    return {"id": sid, "name": SHORT[sid], "acceptanceRate": rate or st["admit_rate"],
            "englishP25": e[0], "englishP50": e[1] or (e[0] + e[2]) / 2, "englishP75": e[2],
            "mathP25": m[0], "mathP50": m[1] or (m[0] + m[2]) / 2, "mathP75": m[2],
            "importance": st.get("test_importance") or "Considered",
            "testOptional": "optional" in pol or "blind" in pol, "prompts": []}


M = AdmissionModel([entry(s) for s in IDS])
ST = Student(STUDENT["ebrw"], STUDENT["math"])


def odds(ids, decisions=None):
    p = M.chances(ST, ids, decisions)
    lo, hi = M.chances_interval(ST, ids, decisions)
    return {s: {"chance": float(a), "lo": float(b), "hi": float(c), "sends_sat": bool(M.submit_policy(ST, s))}
            for s, a, b, c in zip(ids, p, lo, hi)}


def risk(ids, decisions=None):
    p = M.chances(ST, ids, decisions)
    lo, mid, hi = M.p_none_range(ST, ids, decisions)
    return {"linked": mid, "lo": lo, "hi": hi, "naive": float(np.prod(1 - p))}


out = {"student": STUDENT, "ed": ED, "ea": EA, "baseline": odds(IDS), "risk_all10": risk(IDS), "risk_six": risk(SIX),
       "six": SIX, "scenarios": {}}
rest = [s for s in IDS if s != ED]
for res in ("accepted", "deferred", "rejected"):
    d = {ED: res}
    out["scenarios"][res] = {"odds": odds(rest, d), "risk_rest": risk(rest, d),
                             "risk_six_rest": risk([s for s in SIX if s != ED], d)}

# sensitivity: Tufts priced at its Early Decision admit rate instead of its overall rate (upper bound; ED pools differ)
ed_rate = schools[ED]["stats"].get("ed_rate")
if ed_rate:
    M_ed = AdmissionModel([entry(s, ed_rate if s == ED else None) for s in IDS])
    out["ed_sensitivity"] = {"ed_rate": ed_rate, "chance_at_ed_rate": float(M_ed.chances(ST, [ED])[0])}

# calibration details for the annotated report
out["calibration"] = {s: {"rate": M.cal[s].rate, "a_test_weight": M.cal[s].a, "cutoff_c": M.cal[s].c,
                          "pool_mean": M.cal[s].m, "pool_sd": M.cal[s].s, "test_optional": M.cal[s].test_optional}
                      for s in IDS}
out["params"] = {"gamma_shared": M.params.shared_fit, "lapse": M.params.lapse, "rho_th": M.params.rho_th}
save(OUT / "odds.json", out)
for s in IDS:
    b = out["baseline"][s]
    print(f"{SHORT[s]:15s} {100 * b['chance']:5.1f}%  [{100 * b['lo']:4.1f}, {100 * b['hi']:4.1f}]  sends SAT: {b['sends_sat']}")
for k in ("risk_all10", "risk_six"):
    r = out[k]
    print(k, f"linked {100 * r['linked']:.1f}% ({100 * r['lo']:.1f}-{100 * r['hi']:.1f}), naive {100 * r['naive']:.1f}%")
