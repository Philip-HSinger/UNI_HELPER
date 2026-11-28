"""Step 4: admission odds on the verified Common Data Set figures, with Bayesian updates after early results.
Writes outputs/odds.json. Uses the engine's (product/engine) AdmissionModel; three demo-level choices are made here and documented
in the annotated report:
  1. Early Decision school: priced halfway (log-odds) between its overall and its ED admit rate.
  2. Every other school: priced at its non-ED admit rate, (admits - ED admits) / (applicants - ED applicants).
  3. Sending scores at a test-optional school: send iff the SAT is at or above that school's 25th percentile."""
import sys

import numpy as np

from common import CANDIDATES, IDS, LIST, OUT, ROOT, SHORT, SUBMITTED, ENGINE, load, save

sys.path.insert(0, str(ENGINE))
from calliper import model as um  # noqa: E402
from calliper.model import AdmissionModel, Student  # noqa: E402

STUDENT = {"name": "John Smith (fictional)", "ebrw": 700, "math": 720}
ED = "tufts"
EA = ["fordham-university"]

schools = {s["school_id"]: s for s in load(ROOT / "data" / "schools.json")}


def logit(p):
    return float(np.log(p / (1 - p)))


def expit(x):
    return float(1 / (1 + np.exp(-x)))


def comp25(sid):
    st = schools[sid]["stats"]
    if st.get("sat_composite") and st["sat_composite"][0]:
        return st["sat_composite"][0]
    return st["sat_ebrw"][0] + st["sat_math"][0]


def non_ed_rate(sid):
    st = schools[sid]["stats"]
    if st.get("ed_admits") and st.get("ed_applicants"):
        return (st["admits"] - st["ed_admits"]) / (st["applicants"] - st["ed_applicants"])
    return st["admit_rate"]


ed_overall, ed_round = schools[ED]["stats"]["admit_rate"], schools[ED]["stats"]["ed_rate"]
ED_RATE = {"low": ed_overall, "central": expit((logit(ed_overall) + logit(ed_round)) / 2), "high": ed_round}
RATES = {s: (ED_RATE["central"] if s == ED else non_ed_rate(s)) for s in IDS}


def send_rule(self, student, sid):
    """Counselor's rule of thumb instead of the model's default: send iff at or above the 25th percentile."""
    if not self.cal[sid].test_optional:
        return True
    return student.composite >= comp25(sid)


um.AdmissionModel.submit_policy = send_rule  # applies to every model instance built below


def entry(sid, rate):
    st = schools[sid]["stats"]
    e, m = st.get("sat_ebrw"), st.get("sat_math")
    if not e or not m:  # composite only (Fordham): split evenly between the two sections; median = midpoint
        c = st["sat_composite"]
        e = m = [c[0] / 2, (c[1] or (c[0] + c[2]) / 2) / 2, c[2] / 2]
    pol = (st.get("test_policy_2026_27") or "").lower()
    return {"id": sid, "name": SHORT[sid], "acceptanceRate": rate,
            "englishP25": e[0], "englishP50": e[1] or (e[0] + e[2]) / 2, "englishP75": e[2],
            "mathP25": m[0], "mathP50": m[1] or (m[0] + m[2]) / 2, "mathP75": m[2],
            "importance": st.get("test_importance") or "Considered",
            "testOptional": "optional" in pol or "blind" in pol, "prompts": []}


def build(rates):
    return AdmissionModel([entry(s, rates[s]) for s in IDS])


M = build(RATES)
ST = Student(STUDENT["ebrw"], STUDENT["math"])


def odds(ids, decisions=None, model=M):
    p = model.chances(ST, ids, decisions)
    lo, hi = model.chances_interval(ST, ids, decisions)
    return {s: {"chance": float(a), "lo": float(b), "hi": float(c), "sends_sat": bool(model.submit_policy(ST, s))}
            for s, a, b, c in zip(ids, p, lo, hi)}


def risk(ids, decisions=None):
    p = M.chances(ST, ids, decisions)
    lo, mid, hi = M.p_none_range(ST, ids, decisions)
    return {"linked": mid, "lo": lo, "hi": hi, "naive": float(np.prod(1 - p))}


out = {"student": STUDENT, "ed": ED, "ea": EA, "list": LIST, "candidates": CANDIDATES, "rates_used": RATES,
       "rates_overall": {s: schools[s]["stats"]["admit_rate"] for s in IDS},
       "sat_25th": {s: comp25(s) for s in IDS},
       "baseline": odds(IDS), "risk_list": risk(LIST), "scenarios": {}}
rest = [s for s in LIST if s != ED]
out["scenarios"]["accepted"] = {"done": True, "note": "Early Decision is binding: withdraw every other application."}
for res in ("deferred", "rejected"):
    d = {ED: res}
    out["scenarios"][res] = {"odds": odds(rest, d), "risk_rest": risk(rest, d)}

# schools he has not considered: how much each cuts the no-admit risk, now and after a Tufts rejection,
# and per 100 new essay words (essay cost from s3_matrix.py)
plan = load(OUT / "essay_plan.json")
adds = {}
for c in CANDIDATES:
    words = plan["candidates"][c]["new_words"]
    now, after = risk(LIST + [c]), risk(rest + [c], {ED: "rejected"})
    cut = out["risk_list"]["linked"] - now["linked"]
    cut_after = out["scenarios"]["rejected"]["risk_rest"]["linked"] - after["linked"]
    adds[c] = {"new_words": words, "risk_with": now, "risk_with_after_rejection": after, "cut": cut,
               "cut_after_rejection": cut_after, "cut_per_100_words": None if words == 0 else 100 * cut / words}
out["consider"] = dict(sorted(adds.items(), key=lambda kv: (-(kv[1]["cut"] / max(kv[1]["new_words"], 25)))))

# a two-school illustration for the report: Tufts and Boston University
a, b = "tufts", "boston-university"
pa, pb = M.chances(ST, [a, b])
both_no = float(M.count_distribution(ST, [a, b])[0])
bu_after_tufts_no = float(M.chances(ST, [b], {a: "rejected"})[0])
out["illustration"] = {"a": a, "b": b, "p_a": float(pa), "p_b": float(pb), "naive_both_no": float((1 - pa) * (1 - pb)),
                       "linked_both_no": both_no, "p_b_after_a_rejects": bu_after_tufts_no}

out["ed_rates"] = ED_RATE
out["ed_sensitivity"] = {k: {"rate_used": r, "chance": float(build(dict(RATES, **{ED: r})).chances(ST, [ED])[0])}
                         for k, r in ED_RATE.items()}
out["calibration"] = {s: {"rate": M.cal[s].rate, "a_test_weight": M.cal[s].a, "cutoff_c": M.cal[s].c,
                          "pool_mean": M.cal[s].m, "pool_sd": M.cal[s].s, "test_optional": M.cal[s].test_optional}
                      for s in IDS}
out["params"] = {"gamma_shared": M.params.shared_fit, "lapse": M.params.lapse, "rho_th": M.params.rho_th,
                 "withheld_z": M.params.withheld_z}
save(OUT / "odds.json", out)
for s in IDS:
    b = out["baseline"][s]
    print(f"{SHORT[s]:15s} rate {100 * RATES[s]:5.1f}%  chance {100 * b['chance']:5.1f}%  [{100 * b['lo']:4.1f}, {100 * b['hi']:4.1f}]"
          f"  SAT 25th {comp25(s)}  sends: {b['sends_sat']}")
r = out["risk_list"]
print(f"risk (list of {len(LIST)}): linked {100 * r['linked']:.1f}% ({100 * r['lo']:.1f}-{100 * r['hi']:.1f}), naive {100 * r['naive']:.1f}%")
for res in ("deferred", "rejected"):
    s = out["scenarios"][res]
    print(res, "risk", round(100 * s["risk_rest"]["linked"], 1), {SHORT[k]: round(100 * v["chance"]) for k, v in s["odds"].items()})
for c, v in out["consider"].items():
    print(f"  + {SHORT[c]:15s} words {v['new_words']:4d}  risk now {100 * v['risk_with']['linked']:.1f}%  after Tufts no {100 * v['risk_with_after_rejection']['linked']:.1f}%")
print("illustration", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out["illustration"].items()})
print("ED", {k: round(100 * v["chance"], 1) for k, v in out["ed_sensitivity"].items()})
