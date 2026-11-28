"""Stage 2 of the discovery pipeline: for schools John has not considered, his chance (SAT bell-curve fit + linked model),
the new essay words each would cost given his 14 planned essays, and his risk of no admissions if he adds it.
Writes outputs/discovery.json."""
import contextlib, io, json
from common import LIST, OUT, RAW, ROOT, SCORES, load, save, length_factor
with contextlib.redirect_stdout(io.StringIO()):
    import s4_odds as base
from calliper.model import AdmissionModel

NEW = {"nyu": "NYU", "washu": "WashU", "tulane": "Tulane", "case-western": "Case Western"}
stats = {s["school_id"]: s for s in load(RAW / "stats_batch4.json")}
for sid, name in NEW.items():
    base.schools[sid] = {"school_id": sid, "school": name, "stats": stats[sid]}
    base.SHORT[sid] = name
prompts = {p["id"]: p for p in load(ROOT / "data" / "prompts.json")}
newp = {}
for sid in NEW:
    for p in load(RAW / f"prompts_{sid}.json").get("prompts", []):
        newp[p["id"]] = p
scores = load(SCORES / "discovery_scores.json")
rates = dict(base.RATES, **{s: base.non_ed_rate(s) for s in NEW})
ids = LIST + list(NEW)
M = AdmissionModel([base.entry(s, rates[s]) for s in ids])
ST = base.ST
risk_now = float(M.count_distribution(ST, LIST)[0])
out = {"risk_now": risk_now, "schools": []}
for sid, name in NEW.items():
    p = float(M.chances(ST, [sid])[0]); lo, hi = M.chances_interval(ST, [sid])
    risk = float(M.count_distribution(ST, LIST + [sid])[0])
    essays = []
    for pid, pp in newp.items():
        if not pid.startswith(sid + "-") or pid not in {s["new_prompt"] for s in scores}:
            continue
        L = pp.get("word_limit") or 250
        best = max((s for s in scores if s["new_prompt"] == pid),
                   key=lambda s: s["score"] / 100 * length_factor(prompts[s["source"]]["limit"], L))
        share = best["score"] / 100 * length_factor(prompts[best["source"]]["limit"], L)
        essays.append({"prompt": pid, "limit": L, "required": pp.get("required"), "reuse_from": best["source"],
                       "share": round(share, 3), "new_words": round(L * (1 - share))})
    words = sum(e["new_words"] for e in essays if e["required"]) 
    out["schools"].append({"id": sid, "name": name, "chance": p, "lo": float(lo[0]), "hi": float(hi[0]), "risk_with": risk,
                           "rate_used": rates[sid], "sends_sat": bool(M.submit_policy(ST, sid)), "essays": essays,
                           "required_new_words": words})
out["schools"].sort(key=lambda s: -(s["chance"] / (1 + s["required_new_words"] / 100)))
save(OUT / "discovery.json", out)
print(f"risk now {100*risk_now:.1f}%")
for s in out["schools"]:
    print(f"{s['name']:13s} chance {100*s['chance']:5.1f}% [{100*s['lo']:.1f},{100*s['hi']:.1f}] risk->{100*s['risk_with']:.1f}% "
          f"words {s['required_new_words']} rate {100*s['rate_used']:.1f}% essays {[(e['prompt'], e['reuse_from'], e['share'], e['new_words'], e['required']) for e in s['essays']]}")
