"""List optimization: which schools to apply to, given chances, preferences and essay effort.

Objective (expected utility, in the student's own preference units):
    J(L) = E[ max_{j in L, admitted} u_j ]   -   lambda * Effort(L)
  * the first term is computed exactly under the correlated model (AdmissionModel.expected_best),
    so it correctly values *diversification*: a second near-identical reach adds little because
    its admission is correlated with the first;
  * Effort(L) is the reuse-aware word count (SimilarityEngine.list_effort), so a school whose
    supplement is covered by essays already on the list costs almost nothing;
  * lambda converts words into utility ("how many points of preference is 100 words worth").
Search: greedy forward selection (add the school with the best marginal gain until no gain is
positive or the cap is hit), then 1-swap local search. Brute force is used automatically when the
candidate set is small enough (<= 14 schools) so the optimum is exact there; the backtest suite
measures the greedy optimality gap against brute force.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

from .model import AdmissionModel, Student
from .similarity import SimilarityEngine


@dataclass
class Plan:
    schools: list[str]
    expected_best: float
    effort: float
    objective: float
    p_any: float
    method: str


def evaluate(model: AdmissionModel, sim: SimilarityEngine, student: Student, L: list[str], utility: dict,
             lam: float, fallback: float = 0.0) -> tuple[float, float, float]:
    eb = model.expected_best(student, L, utility, fallback)
    eff = sim.list_effort(L)
    return eb - lam * eff, eb, eff


def _p_any(model, student, L):
    return 1 - float(model.count_distribution(student, L)[0]) if L else 0.0


def plan(model: AdmissionModel, sim: SimilarityEngine, student: Student, candidates: list[str], utility: dict,
         lam: float = 0.01, max_apps: int = 12, must: list[str] | None = None, fallback: float = 0.0,
         exact_limit: int = 14) -> Plan:
    cands = [c for c in model.usable(candidates) if c in utility]
    must = [m for m in (must or []) if m in cands]
    if len(cands) <= exact_limit:
        best = None
        free = [c for c in cands if c not in must]
        for k in range(0, min(max_apps, len(cands)) - len(must) + 1):
            for combo in itertools.combinations(free, k):
                L = must + list(combo)
                obj, eb, eff = evaluate(model, sim, student, L, utility, lam, fallback)
                if best is None or obj > best[0]:
                    best = (obj, eb, eff, L)
        obj, eb, eff, L = best
        return Plan(L, eb, eff, obj, _p_any(model, student, L), "exact")
    L = list(must)
    cur = evaluate(model, sim, student, L, utility, lam, fallback)[0]
    while len(L) < max_apps:
        gains = [(evaluate(model, sim, student, L + [c], utility, lam, fallback)[0], c) for c in cands if c not in L]
        if not gains:
            break
        g, c = max(gains)
        if g <= cur:
            break
        L.append(c)
        cur = g
    improved = True
    while improved:
        improved = False
        for out in [x for x in L if x not in must]:
            for inn in [c for c in cands if c not in L]:
                trial = [x for x in L if x != out] + [inn]
                v = evaluate(model, sim, student, trial, utility, lam, fallback)[0]
                if v > cur + 1e-9:
                    L, cur, improved = trial, v, True
                    break
            if improved:
                break
    obj, eb, eff = evaluate(model, sim, student, L, utility, lam, fallback)
    return Plan(L, eb, eff, obj, _p_any(model, student, L), "greedy+swap")


def greedy_only(model, sim, student, candidates, utility, lam=0.01, max_apps=12, fallback=0.0) -> Plan:
    """Greedy without the exact shortcut (used to measure the optimality gap)."""
    return plan(model, sim, student, candidates, utility, lam, max_apps, None, fallback, exact_limit=0)
