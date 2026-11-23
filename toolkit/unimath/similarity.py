"""Essay-reuse similarity: prompt x prompt matrix -> school x school coverage -> marginal effort.

Three layers, each one replaceable by better data:

1. Prompt-pair reuse R(p, q) in [0, 1] = share of the work for p already done by an essay for q.
   * Curated scores (data/similarity.csv, the same table as Supabase's prompt_similarity) always win.
   * Otherwise a transparent model:  R = max over shared themes t of  theta_t * (0.6 + 0.4*cos) * L
       theta_t  reuse coefficient of theme t (e.g. a 'why us' essay is only ~30% reusable since its
                content must be school-specific; an intellectual-curiosity essay ~75%)
       cos      TF-IDF cosine of the prompt texts (school names stripped), i.e. how closely the
                two questions are worded
       L        length-adaptation factor  max(0.5, 1 - 0.15*|ln(w_p / w_q)|): cutting a 650-word
                essay to 50 words, or blowing a 50 up to 300, is real work
     no shared theme -> R = 0.25*cos (pure wording overlap).
2. School coverage C(B | A) = mean over B's prompts of max_q in A R(p, q). Asymmetric on purpose:
   MIT covers a lot of a one-prompt school; that school covers little of MIT.
3. Effort, in "new-word equivalents":  E(p) = (w_p + overhead) * (1 - best reuse vs already-written
   set). Marginal effort of adding a school to a list is the sum over its prompts. Because "best
   match in the set" only improves as the set grows, marginal effort is non-increasing in the set
   (diminishing returns), which is what makes greedy list-building well behaved.
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

THEMES: dict[str, tuple[float, list[str]]] = {
    # theme: (reuse coefficient theta, regex cues)
    "academic": (0.75, [r"field of study", r"\bmajor\b", r"academic", r"intellectual", r"curios", r"learning",
                        r"excite", r"topic", r"pique", r"stud(y|ying)", r"ideas?\b"]),
    "community": (0.70, [r"communit", r"lived experience", r"background", r"identity", r"perspective",
                         r"divers", r"belong", r"contribut", r"dining hall", r"roommate"]),
    "challenge": (0.80, [r"challenge", r"obstacle", r"setback", r"fail", r"unexpected", r"difficult"]),
    "activity": (0.70, [r"extracurricular", r"activit", r"\bjob\b", r"responsibilit", r"summers?"]),
    "impact": (0.65, [r"service", r"civic", r"society", r"impact", r"problems?\b", r"world", r"change"]),
    "values": (0.50, [r"admire", r"important to you", r"values?\b", r"believe"]),
    "quick": (0.35, [r"for fun", r"joy", r"song", r"soundtrack", r"historical", r"new skill", r"five things"]),
    "why_us": (0.30, [r"\bwhy\b[^.?]*\b(us|college|university|school|here)\b", r"applying to", r"opportunities at",
                      r"programs offered", r"this campus", r"suit your", r"why do you want"]),
}
OVERHEAD_WORDS = 60          # ideation/outlining cost per prompt, in word-equivalents
UNKNOWN_LIMIT_WORDS = 250    # prompts with no stated limit
STOP = set("""a an the and or of to in on for with your you yours what how why who which that this
these those is are was were be been being do does did have has had it its as at by from about into
than then so if not no yes please describe tell us we our would will can could may might should
one more most some any all each other own such only also just own their them they he she his her
me my i am up out over under again further once here there when where while words word fewer
less respond response up""".split())


def _tokens(text: str, drop: set[str]) -> list[str]:
    toks = re.findall(r"[a-z']+", text.lower())
    return [t.rstrip("s") if len(t) > 4 else t for t in toks if t not in STOP and t not in drop and len(t) > 2]


def themes_of(text: str) -> set[str]:
    t = text.lower()
    found = {name for name, (_, cues) in THEMES.items() if any(re.search(c, t) for c in cues)}
    return found


def prompt_kind(text: str, limit: int | None) -> str:
    t = text.lower()
    if "optional" in t:
        return "optional"
    if re.search(r"submit a graded|graded written paper", t):
        return "existing-work"
    return "essay"


@dataclass
class PromptInfo:
    id: str
    school: str
    text: str
    words: int
    kind: str
    themes: frozenset


def fit_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Least-squares y ~ alpha + beta*x with beta >= 0 (monotone)."""
    if len(x) < 2 or np.ptp(x) == 0:
        return float(np.mean(y) - np.mean(x)), 1.0
    beta, alpha = np.polyfit(x, y, 1)
    if beta < 0:
        return float(np.mean(y) - np.mean(x)), 1.0
    return float(alpha), float(beta)


class SimilarityEngine:
    def __init__(self, schools: list[dict], curated_csv: str | Path | None = None, recalibrate: bool = False):
        self.recalibrate = recalibrate
        self.schools = {s["id"]: s for s in schools}
        names = set()
        for s in schools:
            names |= set(re.findall(r"[a-z]+", s["name"].lower())) | set(s["id"].split("-"))
        self.prompts: list[PromptInfo] = []
        for s in schools:
            for p in s["prompts"]:
                kind = prompt_kind(p["text"], p.get("wordLimit"))
                wl = p.get("wordLimit")
                words = 0 if kind == "optional" else 50 if kind == "existing-work" else (wl if wl and wl >= 25 else UNKNOWN_LIMIT_WORDS if not wl else 25)
                self.prompts.append(PromptInfo(p["id"], s["id"], p["text"], words, kind, frozenset(themes_of(p["text"]))))
        self.index = {p.id: i for i, p in enumerate(self.prompts)}
        self.by_school: dict[str, list[int]] = {sid: [] for sid in self.schools}
        for i, p in enumerate(self.prompts):
            self.by_school[p.school].append(i)
        self.curated: dict[tuple[str, str], float] = {}
        if curated_csv and Path(curated_csv).exists():
            with open(curated_csv, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    a, b = sorted((row["prompt_a_id"], row["prompt_b_id"]))
                    self.curated[(a, b)] = float(row["score"]) / 100
        self._build(names)

    def _build(self, school_words: set[str]) -> None:
        docs = [_tokens(p.text, school_words) for p in self.prompts]
        vocab = sorted({t for d in docs for t in d})
        vi = {t: i for i, t in enumerate(vocab)}
        n = len(docs)
        tf = np.zeros((n, len(vocab)))
        for r, d in enumerate(docs):
            for t in d:
                tf[r, vi[t]] += 1
        df = (tf > 0).sum(axis=0)
        idf = np.log((1 + n) / (1 + df)) + 1
        X = np.where(tf > 0, 1 + np.log(np.maximum(tf, 1)), 0) * idf
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        X = X / np.where(norms == 0, 1, norms)
        self.cosine = X @ X.T
        R = np.zeros((n, n))
        self.source = np.full((n, n), "model", dtype=object)
        for i, p in enumerate(self.prompts):
            for j, q in enumerate(self.prompts):
                if i == j or p.school == q.school:
                    continue  # same-school prompts are each required separately: no credit
                key = tuple(sorted((p.id, q.id)))
                if key in self.curated:
                    R[i, j] = self.curated[key]
                    self.source[i, j] = "curated"
                    continue
                if "essay" not in (p.kind,) or q.kind != "essay":
                    continue
                cos = self.cosine[i, j]
                shared = p.themes & q.themes
                L = max(0.5, 1 - 0.15 * abs(math.log(max(p.words, 1) / max(q.words, 1))))
                if shared:
                    R[i, j] = max(THEMES[t][0] for t in shared) * (0.6 + 0.4 * cos) * L
                else:
                    R[i, j] = 0.25 * cos * L
        self.raw_R = np.clip(R, 0, 1)
        # Optional self-calibration onto the curator's scale (least-squares line on curated pairs).
        # OFF by default: in backtest E5 it did not beat a constant and it inflated reuse for weakly
        # related pairs. The raw heuristic is kept because it errs low (overstates effort), the safe
        # direction for planning.
        self.calibration = None
        model_mask = self.source == "model"
        if self.recalibrate and len(self.curated) >= 5:
            xs, ys = [], []
            for (a, b), v in self.curated.items():
                if a in self.index and b in self.index:
                    i, j = self.index[a], self.index[b]
                    xs.append(self._heuristic(i, j))
                    ys.append(v)
            self.calibration = fit_line(np.array(xs), np.array(ys))
            alpha, beta = self.calibration
            R = np.where(model_mask & (self.raw_R > 0), np.clip(alpha + beta * self.raw_R, 0, 1), self.raw_R)
        self.R = np.clip(R, 0, 1)

    def _heuristic(self, i: int, j: int) -> float:
        """The model score for a pair, ignoring any curated override."""
        p, q = self.prompts[i], self.prompts[j]
        if p.kind != "essay" or q.kind != "essay" or p.school == q.school:
            return 0.0
        cos = self.cosine[i, j]
        shared = p.themes & q.themes
        L = max(0.5, 1 - 0.15 * abs(math.log(max(p.words, 1) / max(q.words, 1))))
        return float(min(1, max(THEMES[t][0] for t in shared) * (0.6 + 0.4 * cos) * L if shared else 0.25 * cos * L))

    # ---- effort ----------------------------------------------------------------------------
    def prompt_cost(self, i: int) -> float:
        p = self.prompts[i]
        return 0.0 if p.words == 0 else p.words + OVERHEAD_WORDS

    def standalone_effort(self, sid: str) -> float:
        return sum(self.prompt_cost(i) for i in self.by_school[sid])

    def marginal_effort(self, sid: str, written: list[str]) -> tuple[float, list[tuple[int, float, int | None]]]:
        """Effort to add `sid` given essays already written for `written` schools.
        Returns (effort, per-prompt [(prompt idx, reuse, matched prompt idx)])."""
        pool = [j for w in written if w != sid for j in self.by_school[w]]
        detail, total = [], 0.0
        for i in self.by_school[sid]:
            if pool:
                j = max(pool, key=lambda k: self.R[i, k])
                reuse = self.R[i, j]
            else:
                j, reuse = None, 0.0
            detail.append((i, float(reuse), j if reuse > 0 else None))
            total += self.prompt_cost(i) * (1 - reuse)
        return total, detail

    def list_effort(self, sids: list[str]) -> float:
        """Total effort for a list, writing schools in the effort-minimizing greedy order
        (heaviest first, then whatever is cheapest given what's written)."""
        remaining, written, total = list(sids), [], 0.0
        while remaining:
            if not written:
                nxt = max(remaining, key=self.standalone_effort)
                cost = self.standalone_effort(nxt)
            else:
                nxt = min(remaining, key=lambda s: self.marginal_effort(s, written)[0])
                cost = self.marginal_effort(nxt, written)[0]
            total += cost
            written.append(nxt)
            remaining.remove(nxt)
        return total

    # ---- school-level matrices ----------------------------------------------------------------
    def coverage(self, target: str, source: str) -> float:
        """Effort-weighted share of `target`'s supplement covered by `source`'s essays."""
        ti, si = self.by_school[target], self.by_school[source]
        if not ti:
            return 1.0
        cost = np.array([self.prompt_cost(i) for i in ti])
        if cost.sum() == 0:
            return 1.0
        if not si:
            return 0.0
        best = self.R[np.ix_(ti, si)].max(axis=1)
        return float((cost * best).sum() / cost.sum())

    def coverage_matrix(self, sids: list[str]) -> np.ndarray:
        """C[i, j] = share of school i's work already done by school j's essays."""
        n = len(sids)
        C = np.zeros((n, n))
        for a in range(n):
            for b in range(n):
                C[a, b] = 1.0 if a == b else self.coverage(sids[a], sids[b])
        return C

    def clusters(self, sids: list[str], threshold: float = 0.6) -> list[list[str]]:
        """Average-linkage hierarchical clustering on distance 1 - symmetrized coverage."""
        sids = [s for s in sids if self.standalone_effort(s) > 0]
        if len(sids) < 2:
            return [sids]
        C = self.coverage_matrix(sids)
        D = 1 - (C + C.T) / 2
        np.fill_diagonal(D, 0)
        Z = linkage(squareform(np.clip(D, 0, None), checks=False), method="average")
        labels = fcluster(Z, t=threshold, criterion="distance")
        groups: dict[int, list[str]] = {}
        for s, l in zip(sids, labels):
            groups.setdefault(int(l), []).append(s)
        return sorted(groups.values(), key=len, reverse=True)
