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
big = (va + vb) / 2 > 10  # agreement on the pairs that matter (most pairs are near zero, which inflates r)
agree["n_above_10"] = int(big.sum())
agree["pearson_r_above_10"] = float(np.corrcoef(va[big], vb[big])[0, 1]) if big.sum() > 2 else None
agree["mae_above_10"] = float(diff[big].mean()) if big.any() else None

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

# ---- writing order: try every order of the required essays; each essay reuses the best essay written before it
def walk(order, written0=()):
    written, steps = list(written0), []
    for p in order:
        best_q, best_r = None, 0.0
        for q in written:
            if prompts[q]["school_id"] != prompts[p]["school_id"]:
                r = R(p, q)[0]
                if r > best_r:
                    best_q, best_r = q, r
        L = prompts[p]["limit"]
        steps.append({"step": len(steps) + 1, "prompt": p, "school": prompts[p]["school"], "limit": L,
                      "reuse_from": best_q, "reuse_share": round(best_r, 3), "new_words": round(L * (1 - best_r))})
        written.append(p)
    return steps


best = min(itertools.permutations(REQ), key=lambda o: sum(s["new_words"] for s in walk(o)))
plan = walk(best)
naive = sum(prompts[p]["limit"] for p in REQ)
new = sum(s["new_words"] for s in plan)

# ---- December view: ED/EA essays already submitted (deadlines Nov 1-8); what is left for Jan deadlines
SUBMITTED_SCHOOLS = {"tufts", "fordham-university", "university-of-massachusetts-amherst"}
submitted = [p for p in REQ if prompts[p]["school_id"] in SUBMITTED_SCHOOLS]
left_fixed = [p for p in REQ if prompts[p]["school_id"] not in SUBMITTED_SCHOOLS and not prompts[p].get("choose_group")]
bc_opts = [p for p in prompts if prompts[p]["school_id"] == "boston-college"]
dec_best = None
for opt in bc_opts:
    todo = left_fixed + [opt]
    for o in itertools.permutations(todo):
        steps = walk(o, submitted)
        tot = sum(s["new_words"] for s in steps)
        if dec_best is None or tot < dec_best[0]:
            dec_best = (tot, opt, steps)
december = {"submitted": submitted, "bc_choice": dec_best[1], "steps": dec_best[2], "new_words": dec_best[0],
            "naive_words": sum(prompts[s["prompt"]]["limit"] for s in dec_best[2]),
            "bc_option_new_words": {opt: min(sum(s["new_words"] for s in walk(o, submitted))
                                         for o in itertools.permutations(left_fixed + [opt])) for opt in bc_opts}}
save(OUT / "school_matrix.json", {"ids": IDS, "names": [SHORT[i] for i in IDS], "matrix": M.round(3).tolist()})
save(OUT / "essay_plan.json", {"required": REQ, "choose_groups": PICKS, "plan": plan, "naive_words": naive,
                               "new_words": new, "saved_share": round(1 - new / naive, 3) if naive else 0,
                               "agreement": agree, "awaiting_adjudication": len(set(need_adj)), "december": december})
print("agreement", {k: round(v, 3) if isinstance(v, float) else v for k, v in agree.items()})
print(f"required prompts {len(REQ)}; words if written from scratch {naive}; with reuse {new}; saved {1 - new / naive:.0%}")
print(f"pairs awaiting adjudication: {len(set(need_adj))}")
