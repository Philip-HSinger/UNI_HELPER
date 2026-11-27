"""Step 3: combine the two independent scorers (+ adjudication), apply the length factor, and build
  - data/similarity_pairs.csv : every directed prompt pair with both scores, the mean, the length factor and R
  - outputs/school_matrix.json: share of school j's required words that school k's essays can supply
  - outputs/essay_plan.json   : a writing order and the new words each essay needs
R(p <- q) = content(p <- q)/100 * min(1, L_q / L_p)."""
import csv
import itertools

import numpy as np

from common import CANDIDATES, IDS, LIST, OUT, ROOT, SCORES, SHORT, SUBMITTED, WRITE_OPTIONAL, length_factor, load, save

prompts = {p["id"]: p for p in load(ROOT / "data" / "prompts.json")}
def scores(who):
    out = {}
    for name in (f"scorer_{who}.json", f"scorer_{who}_new_1.json", f"scorer_{who}_new_2.json"):
        if (SCORES / name).exists():
            out.update({r["pair"]: r for r in load(SCORES / name)})
    return out


pairs_all = [x["pair"] for x in load(SCORES / "pairs.json")]
sA = {k: v for k, v in scores("A").items() if k in set(pairs_all)}
sB = {k: v for k, v in scores("B").items() if k in set(pairs_all)}
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

# ---- what a school asks of this student: fixed required prompts + choose-k groups (optional groups only if written)
def school_needs(sid):
    fixed, groups = [], {}
    for p in prompts.values():
        if p["school_id"] != sid:
            continue
        g = p.get("choose_group")
        if g:
            groups.setdefault(g["group"], [g.get("choose", 1), [], False])
            groups[g["group"]][1].append(p["id"])
            groups[g["group"]][2] |= bool(p.get("required")) or (sid, g["group"]) in WRITE_OPTIONAL
        elif p.get("required"):
            fixed.append(p["id"])
    return fixed, [(k, opts) for k, opts, used in groups.values() if used]


def cost_of(order, written0=()):
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
    return sum(s["new_words"] for s in steps), steps


def best_order(items, written0=()):
    """Exact (subset DP) for up to 12 essays; otherwise greedy start + insertion local search."""
    items = list(items)
    n = len(items)
    if n <= 14:
        Rm = [[R(p, q)[0] if prompts[q]["school_id"] != prompts[p]["school_id"] else 0.0 for q in items] for p in items]
        base = [max([R(p, q)[0] for q in written0 if prompts[q]["school_id"] != prompts[p]["school_id"]] or [0.0]) for p in items]
        L = [prompts[p]["limit"] for p in items]
        full_mask = (1 << n) - 1
        best_r = [base[:]] + [None] * full_mask  # best_r[mask][i]: best reuse for essay i given essays in mask written
        for mask in range(1, 1 << n):
            low = (mask & -mask).bit_length() - 1
            prev = best_r[mask & (mask - 1)]
            best_r[mask] = [max(prev[i], Rm[i][low]) for i in range(n)]
        INF = float("inf")
        dp, par = [INF] * (1 << n), [None] * (1 << n)
        dp[0] = 0.0
        for mask in range(1 << n):
            d = dp[mask]
            if d == INF:
                continue
            br = best_r[mask]
            for i in range(n):
                if mask >> i & 1:
                    continue
                v = d + L[i] * (1 - br[i])
                nm = mask | 1 << i
                if v < dp[nm] - 1e-9:
                    dp[nm], par[nm] = v, (mask, i)
        order, mask = [], full_mask
        while mask:
            mask, i = par[mask]
            order.append(items[i])
        order.reverse()
        return cost_of(order, written0), "exact"
    order = []
    rest = items[:]
    while rest:  # greedy: next = the essay that supplies the most to the rest
        nxt = max(rest, key=lambda c: sum(prompts[p]["limit"] * R(p, c)[0] for p in rest if p != c
                                          and prompts[p]["school_id"] != prompts[c]["school_id"]))
        order.append(nxt)
        rest.remove(nxt)
    best = cost_of(order, written0)
    improved = True
    while improved:  # move any single essay to any other position while that lowers the total
        improved = False
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                o = [s["prompt"] for s in best[1]]
                p = o.pop(i)
                o.insert(j, p)
                c = cost_of(o, written0)
                if c[0] < best[0]:
                    best, improved = c, True
    return best, "local search"


def plan_for(schools, written0=()):
    """Best plan over every combination of choose-group options for these schools."""
    fixed, groups = [], []
    for sid in schools:
        f, g = school_needs(sid)
        fixed += f
        groups += [(sid, k, opts) for k, opts in g]
    best = None
    combos = list(itertools.product(*[list(itertools.combinations(opts, k)) for _, k, opts in groups]))
    n_items = len(fixed) + sum(k for _, k, _ in groups)
    if len(combos) * (1 << min(n_items, 14)) > 3_000_000:
        pick = []
        for sid, k, opts in groups:
            others = [q for q in prompts if prompts[q]["school_id"] != sid]
            score = {o: np.mean([R(o, q)[0] + R(q, o)[0] for q in others]) for o in opts}
            pick.append(tuple(sorted(opts, key=lambda o: -score[o])[:k]))
        combos = [tuple(pick)]
    for combo in combos:
        items = fixed + [p for pick in combo for p in pick]
        (tot, steps), how = best_order(items, written0)
        if best is None or tot < best["new_words"]:
            best = {"new_words": tot, "steps": steps, "how": how, "chosen": [p for pick in combo for p in pick],
                    "naive_words": sum(prompts[p]["limit"] for p in items)}
    if best is None:
        return {"new_words": 0, "steps": [], "how": "none", "chosen": [], "naive_words": 0}
    return best


# ---- the student's full plan, the December view, and what each school he has not considered would cost
full = plan_for(LIST)
essays = [s["prompt"] for s in full["steps"]]
submitted = [p for p in essays if prompts[p]["school_id"] in SUBMITTED]
december = plan_for([s for s in LIST if s not in SUBMITTED], written0=submitted)
options_dec = {}
for sid in LIST:
    if sid in SUBMITTED:
        continue
    for k, opts in school_needs(sid)[1]:
        if len(opts) > 1:
            others = [s for s in LIST if s not in SUBMITTED and s != sid]
            dec_essays = [x["prompt"] for x in december["steps"]]
            base_written = submitted + [p for p in dec_essays if prompts[p]["school_id"] in others]
            options_dec[SHORT[sid]] = {o: cost_of([o], base_written)[0] for o in opts}
candidates = {}
for sid in CANDIDATES:
    c = plan_for([sid], written0=essays)
    candidates[sid] = {"new_words": c["new_words"], "naive_words": c["naive_words"], "steps": c["steps"]}

# ---- school x school matrix over all schools with essays
need = {sid: school_needs(sid)[0] + [o for _, opts in school_needs(sid)[1] for o in opts] for sid in IDS}
Mx = np.zeros((len(IDS), len(IDS)))
for i, j in enumerate(IDS):
    for k_, k in enumerate(IDS):
        if j != k and need[j] and need[k]:
            tot = sum(prompts[p]["limit"] for p in need[j])
            Mx[i, k_] = sum(prompts[p]["limit"] * max(R(p, q)[0] for q in need[k]) for p in need[j]) / tot

save(OUT / "school_matrix.json", {"ids": IDS, "names": [SHORT[i] for i in IDS], "matrix": Mx.round(3).tolist()})
save(OUT / "essay_plan.json", {"list": LIST, "full": full, "december": december, "december_options": options_dec,
                               "submitted": submitted, "candidates": candidates, "agreement": agree,
                               "awaiting_adjudication": len(set(need_adj))})
print("agreement", {k: round(v, 3) if isinstance(v, float) else v for k, v in agree.items()})
print(f"full plan ({full['how']}): {full['naive_words']} -> {full['new_words']} words; chosen {full['chosen']}")
print(f"December ({december['how']}): {december['naive_words']} -> {december['new_words']}")
print("December options", options_dec)
for sid, c in candidates.items():
    print(f"  consider {SHORT[sid]:15s} {c['naive_words']:4d} -> {c['new_words']:4d} new words")
print(f"pairs awaiting adjudication: {len(set(need_adj))}")
