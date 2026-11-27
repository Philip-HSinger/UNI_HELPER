"""Step 3: combine the two independent scorers (+ adjudication), apply the length factor, and build
  - data/similarity_pairs.csv : every directed prompt pair with both scores, the mean, the length factor and R
  - outputs/school_matrix.json: share of school j's required words that school k's essays can supply
  - outputs/essay_plan.json   : a writing order and the new words each essay needs
R(p <- q) = content(p <- q)/100 * min(1, L_q / L_p)."""
import csv
import itertools

import numpy as np

from common import IDS, OUT, ROOT, SCORES, SHORT, WRITE_OPTIONAL, length_factor, load, save

prompts = {p["id"]: p for p in load(ROOT / "data" / "prompts.json")}
sA = {r["pair"]: r for r in load(SCORES / "scorer_A.json")}
sB = {r["pair"]: r for r in load(SCORES / "scorer_B.json")}
adj = {r["pair"]: r for r in load(SCORES / "adjudicated.json")} if (SCORES / "adjudicated.json").exists() else {}
pairs = [x["pair"] for x in load(SCORES / "pairs.json")]
assert set(pairs) == set(sA) == set(sB), "scorers did not cover exactly the listed pairs"

# ---- agreement between the two scorers (before adjudication)
va, vb, rows = [], [], []
for key in pairs:
    for d in ("a_from_b", "b_from_a"):
        va.append(float(sA[key][d]))
        vb.append(float(sB[key][d]))
va, vb = np.array(va), np.array(vb)
diff = np.abs(va - vb)
agree = {"n_scores": int(len(va)), "mae": float(diff.mean()), "pearson_r": float(np.corrcoef(va, vb)[0, 1]),
         "within_15": float((diff <= 15).mean()), "over_25": int((diff > 25).sum())}

# ---- directed content scores C(p <- q)
C = {}
need_adj = []
for key in pairs:
    a, b = key.split("|")
    for d, (p, q) in (("a_from_b", (a, b)), ("b_from_a", (b, a))):
        x, y = float(sA[key][d]), float(sB[key][d])
        if abs(x - y) > 25:
            if key in adj:
                val, src = float(adj[key][d]), "adjudicated"
            else:
                need_adj.append(key)
                val, src = (x + y) / 2, "mean (awaiting adjudication)"
        else:
            val, src = (x + y) / 2, "mean"
        C[(p, q)] = dict(a=x, b=y, content=val, source=src, reason_a=sA[key].get("reason", ""), reason_b=sB[key].get("reason", ""))
save(SCORES / "needs_adjudication.json", sorted(set(need_adj)))


def R(p, q):
    lf = length_factor(prompts[q]["limit"], prompts[p]["limit"])
    return C[(p, q)]["content"] / 100 * lf, lf


with open(ROOT / "data" / "similarity_pairs.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["needs (p)", "school p", "limit p", "source (q)", "school q", "limit q", "scorer A", "scorer B",
                "content", "how", "length factor", "R = reuse"])
    for (p, q), c in sorted(C.items()):
        r, lf = R(p, q)
        w.writerow([p, prompts[p]["school"], prompts[p]["limit"], q, prompts[q]["school"], prompts[q]["limit"],
                    c["a"], c["b"], round(c["content"], 1), c["source"], round(lf, 3), round(r, 3)])

# ---- which prompts a student must answer: required ones; a choose-k group counts its k most reusable options
def required_set():
    req = []
    groups = {}
    for p in prompts.values():
        g = p.get("choose_group")
        if g:
            groups.setdefault((p["school_id"], g["group"]), (g.get("choose", 1), []))[1].append(p["id"])
        elif p.get("required"):
            req.append(p["id"])
    picks = {}
    for (sid, g), (k, opts) in groups.items():
        others = [q for q in prompts if prompts[q]["school_id"] != sid]
        score = {o: np.mean([R(o, q)[0] + R(q, o)[0] for q in others]) for o in opts}
        chosen = sorted(opts, key=lambda o: -score[o])[:k]
        picks[f"{SHORT[sid]} group {g}"] = {"options": opts, "chosen": chosen,
                                            "why": {o: round(float(score[o]), 3) for o in opts}}
        if any(prompts[o].get("required") for o in opts) or (sid, g) in WRITE_OPTIONAL:
            req += chosen
    return req, picks


REQ, PICKS = required_set()

# ---- school x school matrix: share of school j's required words school k's essays can supply
by_school = {sid: [p for p in REQ if prompts[p]["school_id"] == sid] for sid in IDS}
M = np.zeros((len(IDS), len(IDS)))
for i, j in enumerate(IDS):
    need = by_school[j]
    tot = sum(prompts[p]["limit"] for p in need)
    for k_, k in enumerate(IDS):
        if j == k or not need or not by_school[k]:
            continue
        M[i, k_] = sum(prompts[p]["limit"] * max(R(p, q)[0] for q in by_school[k]) for p in need) / tot

# ---- writing order: greedy, start with the essay that supplies the most words to the essays not yet written
order, written, plan = [], [], []
remaining = list(REQ)
while remaining:
    def supply(c):
        return sum(prompts[p]["limit"] * R(p, c)[0] for p in remaining if p != c and prompts[p]["school_id"] != prompts[c]["school_id"])
    nxt = max(remaining, key=supply)
    best_q, best_r = None, 0.0
    for q in written:
        if prompts[q]["school_id"] != prompts[nxt]["school_id"]:
            r = R(nxt, q)[0]
            if r > best_r:
                best_q, best_r = q, r
    L = prompts[nxt]["limit"]
    plan.append({"step": len(plan) + 1, "prompt": nxt, "school": prompts[nxt]["school"], "limit": L,
                 "reuse_from": best_q, "reuse_share": round(best_r, 3), "new_words": round(L * (1 - best_r))})
    written.append(nxt)
    remaining.remove(nxt)

naive = sum(prompts[p]["limit"] for p in REQ)
new = sum(s["new_words"] for s in plan)
save(OUT / "school_matrix.json", {"ids": IDS, "names": [SHORT[i] for i in IDS], "matrix": M.round(3).tolist()})
save(OUT / "essay_plan.json", {"required": REQ, "choose_groups": PICKS, "plan": plan, "naive_words": naive,
                               "new_words": new, "saved_share": round(1 - new / naive, 3) if naive else 0,
                               "agreement": agree, "awaiting_adjudication": len(set(need_adj))})
print("agreement", {k: round(v, 3) if isinstance(v, float) else v for k, v in agree.items()})
print(f"required prompts {len(REQ)}; words if written from scratch {naive}; with reuse {new}; saved {1 - new / naive:.0%}")
print(f"pairs awaiting adjudication: {len(set(need_adj))}")
