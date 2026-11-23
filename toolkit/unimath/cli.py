"""UNIMATH terminal. Bloomberg-style mnemonics, dense amber tables, a stateful REPL.

  unimath                         interactive terminal
  unimath CHNC -p profile.toml    one-shot command (any mnemonic), scriptable
  unimath CHNC -p profile.toml --json
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import tomllib
from dataclasses import asdict, dataclass, field

import numpy as np

from .catalog import SIMILARITY, load_catalog, validate
from .model import AdmissionModel, Student
from .scores import fit_school, percentile_with_interval
from .similarity import SimilarityEngine

# ---------------------------------------------------------------------------------------------
# styling
# ---------------------------------------------------------------------------------------------
COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code):
    return (lambda s: f"\033[{code}m{s}\033[0m") if COLOR else (lambda s: str(s))


AMB = _c("38;5;214")
WHT = _c("97;1")
GRN = _c("38;5;46")
RED = _c("38;5;196")
DIM = _c("38;5;244")
BAR = _c("30;48;5;214;1")
CYN = _c("38;5;45")


def header(code: str, title: str, sub: str = "") -> None:
    w = 96
    line = f" {code:<6}{title}"
    sub = sub[: max(0, w - len(line) - 3)]
    print(BAR(line + " " * max(1, w - len(line) - len(sub) - 1) + sub + " "))


def table(cols: list[tuple[str, int, str]], rows: list[list], color_fn=None) -> None:
    """cols: (title, width, align '<' or '>'). color_fn(row_idx, col_idx, value) -> styled str."""
    print(WHT("".join(f"{t:{a}{w - 1}.{w - 1}} " for t, w, a in cols)))
    print(DIM("".join("-" * (w - 1) + " " for _, w, _ in cols)))
    for ri, r in enumerate(rows):
        cells = []
        for ci, ((_, w, a), v) in enumerate(zip(cols, r)):
            if isinstance(v, float) and np.isnan(v):
                v = "—"
            s = f"{v:{a}{w - 1}}" if not isinstance(v, float) else f"{v:{a}{w - 1}.1f}"
            s = (s[: w - 1] if len(s) > w - 1 else s) + " "
            cells.append(color_fn(ri, ci, v, s) if color_fn else AMB(s))
        print("".join(cells))


def pct_color(p: float, s: str) -> str:
    if not isinstance(p, float) or np.isnan(p):
        return AMB(s)
    return GRN(s) if p >= 50 else AMB(s) if p >= 15 else RED(s)


def note(msg: str) -> None:
    print(DIM(msg))


def bar_spark(p: float, width: int = 20) -> str:
    n = int(round(p * width))
    return "█" * n + "·" * (width - n)


# ---------------------------------------------------------------------------------------------
# session state
# ---------------------------------------------------------------------------------------------
@dataclass
class Session:
    ebrw: float = 700
    math: float = 720
    holistic_pct: float | None = None
    holistic_sd: float | None = None
    schools: list[str] = field(default_factory=list)
    decisions: dict = field(default_factory=dict)
    utility: dict = field(default_factory=dict)
    effort_cost: float = 0.01  # utility points per word
    max_apps: int = 12
    fallback: float = 0.0
    json: bool = False

    def student(self) -> Student:
        return Student.from_percentile(self.ebrw, self.math, self.holistic_pct, self.holistic_sd)


def load_profile(path: str, sess: Session) -> None:
    d = tomllib.load(open(path, "rb"))
    st = d.get("student", {})
    sess.ebrw = st.get("sat_ebrw", sess.ebrw)
    sess.math = st.get("sat_math", sess.math)
    sess.holistic_pct = st.get("holistic_pct", sess.holistic_pct)
    sess.holistic_sd = st.get("holistic_sd", sess.holistic_sd)
    plan = d.get("plan", {})
    sess.effort_cost = plan.get("effort_cost", sess.effort_cost)
    sess.max_apps = plan.get("max_apps", sess.max_apps)
    sess.fallback = plan.get("fallback_utility", sess.fallback)
    for s in d.get("schools", []):
        sess.schools.append(s["id"])
        if "utility" in s:
            sess.utility[s["id"]] = float(s["utility"])
        if "decision" in s:
            sess.decisions[s["id"]] = s["decision"]


class Terminal:
    def __init__(self, sess: Session, catalog_path=None):
        self.sess = sess
        self.cat = load_catalog(catalog_path)
        self.by_id = {s["id"]: s for s in self.cat}
        self.model = AdmissionModel(self.cat)
        self.sim = SimilarityEngine(self.cat, SIMILARITY)

    # helpers
    def ids(self, args=None) -> list[str]:
        ids = [a for a in (args or []) if a in self.by_id] or self.sess.schools or self.model.usable()
        return ids

    def name(self, sid: str) -> str:
        return self.by_id[sid]["name"][:22]

    def out(self, obj) -> bool:
        if self.sess.json:
            print(json.dumps(obj, indent=1, default=float))
            return True
        return False

    def skipped(self, ids):
        bad = [i for i in ids if not self.model.cal[i].ok]
        if bad:
            note(f"  not modelled (missing data, see DQ): {', '.join(bad)}")

    # ------------------------------------------------------------------- commands
    def cmd_PCTL(self, args):
        """PCTL [school..]       score percentile vs each school's fitted distribution, 90% CI from test SEM"""
        s = self.sess
        ids = self.ids(args)
        rows, js = [], []
        for sid in ids:
            sc = self.by_id[sid]
            comp = fit_school(sc)
            e = percentile_with_interval(comp.ebrw, s.ebrw)
            m = percentile_with_interval(comp.math, s.math)
            c = 100 * comp.mid_rank(s.ebrw + s.math)
            q = [comp.quantile(p) for p in (0.25, 0.5, 0.75)]
            js.append({"school": sid, "ebrw": e, "math": m, "composite": c, "composite_band": q,
                       "fit": [comp.ebrw.method, comp.math.method]})
            rows.append([self.name(sid), f"{sc['englishP25']}/{sc['englishP50']}/{sc['englishP75']}", e[0],
                         f"{e[1]:.0f}-{e[2]:.0f}", f"{sc['mathP25']}/{sc['mathP50']}/{sc['mathP75']}", m[0],
                         f"{m[1]:.0f}-{m[2]:.0f}", f"{q[0]:.0f}/{q[1]:.0f}/{q[2]:.0f}", c,
                         "*" if "censored" in comp.ebrw.method + comp.math.method else ""])
        if self.out(js):
            return
        header("PCTL", "SCORE PERCENTILES", f"EBRW {s.ebrw:.0f}  MATH {s.math:.0f}  COMP {s.ebrw + s.math:.0f}")
        table([("SCHOOL", 23, "<"), ("EBRW BAND", 12, "<"), ("PCT", 6, ">"), ("90%CI", 9, ">"), ("  MATH BAND", 13, "<"),
               ("PCT", 6, ">"), ("90%CI", 9, ">"), ("  COMP BAND (model)", 21, "<"), ("PCT", 6, ">"), ("", 2, "<")], rows,
              lambda r, c, v, st: pct_color(v, st) if isinstance(v, float) else AMB(st))
        note("  two-piece normal matched to the published 25/50/75; mid-rank on 10-pt grid; composite via Gaussian")
        note("  copula (rho=0.6), not summed bands. * = 800-ceiling censoring, upper tail partly from prior.")

    def cmd_CHNC(self, args):
        """CHNC [school..]       P(admit) per school, 80% band, vs base rate, submit/withhold call"""
        s, M = self.sess, self.model
        ids = M.usable(self.ids(args))
        st = s.student()
        p = M.chances(st, ids, s.decisions or None)
        lo, hi = M.chances_interval(st, ids, s.decisions or None)
        rows, js = [], []
        for i, sid in enumerate(ids):
            c = M.cal[sid]
            sub = M.submit_policy(st, sid)
            tag = "SUBMIT" if sub else "WITHHOLD"
            tag = tag if c.test_optional else "required"
            lift = p[i] / c.rate
            dec = s.decisions.get(sid, "")
            tier = "LIKELY" if p[i] >= 0.6 else "TARGET" if p[i] >= 0.3 else "REACH" if p[i] >= 0.08 else "LONG SHOT"
            rows.append([self.name(sid), 100 * c.rate, 100 * p[i], f"{100 * lo[i]:.0f}-{100 * hi[i]:.0f}",
                         f"{lift:.2f}x", tier, tag, bar_spark(p[i], 16), dec.upper()])
            js.append({"school": sid, "p_admit": p[i], "band80": [lo[i], hi[i]], "base_rate": c.rate, "tier": tier,
                       "tests": tag, "decision": dec})
        if self.out(js):
            return
        hdr = f"COMP {st.composite:.0f}  HOL {'n/a' if s.holistic_pct is None else f'{s.holistic_pct:.0f}p'}"
        header("CHNC", "ADMISSION PROBABILITY" + ("  (POSTERIOR)" if s.decisions else ""), hdr)
        table([("SCHOOL", 23, "<"), ("BASE%", 7, ">"), ("P(ADM)%", 9, ">"), ("80% BAND", 10, ">"), ("LIFT", 7, ">"),
               ("  TIER", 11, "<"), ("TESTS", 10, "<"), ("", 18, "<"), ("DECIDED", 9, "<")], rows,
              lambda r, c, v, st_: pct_color(v, st_) if c == 2 else (CYN(st_) if c == 7 else AMB(st_)))
        self.skipped(self.ids(args))
        note("  calibrated probit selection model, shared-factor integration on 801-pt grid; band = spread over the")
        note("  unknown non-test strength. Decisions entered with DEC update every row (Bayes).")

    def cmd_XADM(self, args):
        """XADM [school..]       cross-admit matrix: P(col | admitted at row), and lift vs independence"""
        M, st = self.model, self.sess.student()
        ids = M.usable(self.ids(args))[:10]
        X = M.cross_matrix(st, ids, "accepted")
        R = M.cross_matrix(st, ids, "rejected")
        if self.out({"ids": ids, "given_admit": X.tolist(), "given_reject": R.tolist()}):
            return
        header("XADM", "CROSS-ADMIT MATRIX  P(column | row ACCEPTED)", "diag = marginal")
        short = [i[:7].upper() for i in ids]
        cols = [("GIVEN ↓", 12, "<")] + [(s, 8, ">") for s in short]
        rows = [[ids[i][:11]] + [100 * X[i, j] for j in range(len(ids))] for i in range(len(ids))]
        marg = np.diag(X)
        table(cols, rows, lambda r, c, v, s_: WHT(s_) if c - 1 == r else (
            GRN(s_) if c and v / 100 > marg[c - 1] * 1.25 else AMB(s_)) if c else AMB(s_))
        print()
        header("XADM", "P(column | row REJECTED)", "")
        rows = [[ids[i][:11]] + [100 * R[i, j] if i != j else 0.0 for j in range(len(ids))] for i in range(len(ids))]
        table(cols, rows, lambda r, c, v, s_: DIM(s_) if c - 1 == r else (
            RED(s_) if c and v / 100 < marg[c - 1] * 0.8 else AMB(s_)) if c else AMB(s_))
        note("  green = >25% lift over the marginal; red = >20% drop. Independence would make every row equal the diagonal.")

    def cmd_DEC(self, args):
        """DEC <school> <accepted|rejected|waitlisted|deferred|clear>   record a real decision"""
        if len(args) < 2 or args[0] not in self.by_id:
            return print(RED("usage: DEC mit accepted"))
        if args[1].lower() == "clear":
            self.sess.decisions.pop(args[0], None)
        else:
            self.sess.decisions[args[0]] = args[1].lower()
        if args[0] not in self.sess.schools:
            self.sess.schools.append(args[0])
        self.cmd_UPDT([])

    def cmd_UPDT(self, args):
        """UPDT                  Bayesian update: what your decisions so far imply for the rest"""
        s, M, st = self.sess, self.model, self.sess.student()
        if not s.decisions:
            return note("no decisions yet: DEC <school> accepted|rejected|waitlisted")
        m0, s0, m1, s1 = M.shared_posterior_summary(st, s.decisions)
        pending = [i for i in M.usable(self.ids()) if i not in s.decisions]
        prior = M.chances(st, pending)
        post = M.chances(st, pending, s.decisions)
        if self.out({"shared_factor": {"prior": [m0, s0], "posterior": [m1, s1]},
                     "pending": {i: {"prior": a, "posterior": b} for i, a, b in zip(pending, prior, post)}}):
            return
        header("UPDT", "POSTERIOR UPDATE", " ".join(f"{k}:{v[:3].upper()}" for k, v in s.decisions.items()))
        print(AMB(f"  shared strength factor S   prior {m0:+.2f} ± {s0:.2f}   →   posterior {m1:+.2f} ± {s1:.2f}"))
        rows = [[self.name(i), 100 * a, 100 * b, 100 * (b - a), f"{b / a:.2f}x"] for i, a, b in zip(pending, prior, post)]
        table([("PENDING", 23, "<"), ("PRIOR%", 8, ">"), ("POST%", 8, ">"), ("CHG pts", 9, ">"), ("RATIO", 8, ">")], rows,
              lambda r, c, v, st_: (GRN(st_) if v > 0 else RED(st_)) if c == 3 else AMB(st_))

    def cmd_PORT(self, args):
        """PORT [school..]       distribution of the number of admits; P(at least one) vs independence"""
        s, M, st = self.sess, self.model, self.sess.student()
        ids = M.usable(self.ids(args))
        dist = M.count_distribution(st, ids, s.decisions or None)
        marg = M.chances(st, ids, s.decisions or None)
        p_ind = 1 - np.prod(1 - marg)
        if self.out({"ids": ids, "count_dist": dist.tolist(), "p_any": 1 - dist[0], "p_any_independent": p_ind,
                     "expected_admits": float(dist @ np.arange(len(dist)))}):
            return
        header("PORT", "PORTFOLIO OUTCOME DISTRIBUTION", f"{len(ids)} schools")
        for n, p in enumerate(dist):
            if p < 5e-4 and n > 3:
                continue
            print(AMB(f"  {n:>2} admits  {100 * p:6.2f}%  ") + CYN(bar_spark(p, 50)))
        e = float(dist @ np.arange(len(dist)))
        print(WHT(f"  P(≥1 admit) {100 * (1 - dist[0]):.1f}%   ") + DIM(f"naive independent 1-∏(1-p): {100 * p_ind:.1f}%")
              + WHT(f"   E[#admits] {e:.2f}"))
        note("  the gap between those two numbers is why list-balancing tools that multiply probabilities overstate safety.")

    def cmd_ESSY(self, args):
        """ESSY [school..]       essay coverage matrix: % of row school's work done by column school's essays"""
        sim = self.sim
        ids = self.ids(args)[:10]
        C = sim.coverage_matrix(ids)
        if self.out({"ids": ids, "coverage": C.tolist(), "standalone_words": {i: sim.standalone_effort(i) for i in ids}}):
            return
        header("ESSY", "ESSAY COVERAGE  (row covered by column)", "curated pairs override model")
        cols = [("SCHOOL", 12, "<"), ("WORDS", 7, ">")] + [(i[:7].upper(), 8, ">") for i in ids]
        rows = [[ids[r][:11], f"{sim.standalone_effort(ids[r]):.0f}"] + [100 * C[r, c] for c in range(len(ids))] for r in range(len(ids))]
        table(cols, rows, lambda r, c, v, s_: DIM(s_) if c - 2 == r else (GRN(s_) if isinstance(v, float) and v >= 40 else AMB(s_)))
        print()
        groups = sim.clusters(self.ids(args) if args else [s["id"] for s in self.cat])
        print(WHT("  CLUSTERS (write once, reuse within):"))
        for g in groups:
            if len(g) > 1:
                print(AMB("   · " + " + ".join(g)))
        note("  words incl. 60/prompt overhead; reuse = theme coefficient × TF-IDF wording × length adaptation.")

    def cmd_FREE(self, args):
        """FREE                  schools that are nearly free given what your list already makes you write"""
        sim, M = self.sim, self.model
        base = [i for i in self.sess.schools] or ["mit", "stanford"]
        rows, js = [], []
        for s in self.cat:
            sid = s["id"]
            if sid in base:
                continue
            eff, det = sim.marginal_effort(sid, base)
            alone = sim.standalone_effort(sid)
            best = max(det, key=lambda d: d[1] * sim.prompt_cost(d[0])) if det else None
            via = sim.prompts[best[2]].school if best and best[2] is not None else "-"
            rows.append([self.name(sid), alone, eff, 100 * (1 - eff / alone) if alone else 100.0, via,
                         100 * M.chances(self.sess.student(), [sid])[0] if M.cal[sid].ok else float("nan")])
            js.append({"school": sid, "standalone": alone, "marginal": eff, "via": via})
        rows.sort(key=lambda r: r[2])
        if self.out(js):
            return
        header("FREE", "MARGINAL ESSAY COST GIVEN CURRENT LIST", "base: " + ",".join(base))
        table([("SCHOOL", 23, "<"), ("ALONE", 8, ">"), ("MARGINAL", 10, ">"), ("SAVED%", 8, ">"), ("  MAIN SOURCE", 16, "<"),
               ("P(ADM)%", 9, ">")], rows,
              lambda r, c, v, s_: GRN(s_) if c == 2 and v < 200 else AMB(s_))

    def cmd_PLAN(self, args):
        """PLAN                  optimal list: max E[utility of best admit] - effort_cost x words"""
        from .planner import plan
        s, M = self.sess, self.model
        cands = [c for c in (self.sess.schools or M.usable()) if M.cal.get(c) and M.cal[c].ok]
        util = {c: s.utility.get(c, 50.0) for c in cands}
        if not s.utility:
            note("  no utilities set (UTIL <school> <0-100>); using 50 for every school")
        p = plan(M, self.sim, s.student(), cands, util, s.effort_cost, s.max_apps, fallback=s.fallback, exact_limit=12)
        if self.out(asdict(p)):
            return
        header("PLAN", "LIST OPTIMIZER", f"{p.method}  λ={s.effort_cost}/word  cap={s.max_apps}")
        ch = M.chances(s.student(), p.schools)
        rows = [[self.name(i), util[i], 100 * c] for i, c in zip(p.schools, ch)]
        table([("APPLY TO", 23, "<"), ("UTILITY", 9, ">"), ("P(ADM)%", 9, ">")], rows)
        print(WHT(f"  E[best admit utility] {p.expected_best:.1f}   essay words {p.effort:.0f}   objective {p.objective:.1f}"
                  f"   P(≥1) {100 * p.p_any:.1f}%"))

    def cmd_SENS(self, args):
        """SENS [school..]       sensitivity of P(admit) to every modelling assumption (tornado)"""
        from .backtest import sensitivity
        ids = self.model.usable(self.ids(args))[:6]
        r = sensitivity(self.cat, self.sess.student(), ids)
        if self.out(r):
            return
        header("SENS", "ASSUMPTION SENSITIVITY  P(admit)% at low / base / high", "")
        cols = [("PARAM", 16, "<"), ("RANGE", 12, "<")] + [(i[:9].upper(), 16, ">") for i in ids]
        rows = []
        for k, v in r.items():
            if k == "base":
                continue
            rows.append([k, f"{v['lo']}–{v['hi']}"] + [f"{100 * v['p_lo'][i]:.1f}/{100 * r['base'][i]:.1f}/{100 * v['p_hi'][i]:.1f}" for i in ids])
        table(cols, rows)
        note("  fit these to your own outcomes with FIT <csv> instead of trusting defaults.")

    def cmd_SCH(self, args):
        """SCH <school>          school description page: data, fitted distributions, calibration"""
        if not args or args[0] not in self.by_id:
            return print(RED("usage: SCH mit"))
        sc, c = self.by_id[args[0]], self.model.cal[args[0]]
        comp = fit_school(sc)
        header("SCH", sc["name"].upper(), sc.get("provenance", ""))
        kv = [("platform", sc["platform"]), ("test policy", "optional" if sc["testOptional"] else "required"),
              ("CDS test importance", sc["importance"]), ("acceptance rate", f"{100 * sc['acceptanceRate']:.1f}%" if sc.get("acceptanceRate") else "MISSING"),
              ("EBRW band / fit", f"{sc['englishP25']}/{sc['englishP50']}/{sc['englishP75']}  {comp.ebrw.method}  σL={comp.ebrw.sl:.0f} σR={comp.ebrw.sr:.0f}"),
              ("Math band / fit", f"{sc['mathP25']}/{sc['mathP50']}/{sc['mathP75']}  {comp.math.method}  σL={comp.math.sl:.0f} σR={comp.math.sr:.0f}")]
        if c.ok:
            kv += [("admitted composite μ/σ", f"{c.adm_mean:.0f} / {c.adm_sd:.0f}"),
                   ("implied APPLICANT pool μ/σ", f"{c.m:.0f} / {c.s:.0f}   (inverted truncated-normal selection)"),
                   ("test weight a / threshold c", f"{c.a:.2f} / {c.c:.2f}"), ("pool strength shift κ", f"{c.kappa:+.2f}")]
        else:
            kv.append(("model", "NOT CALIBRATED: " + c.reason))
        kv.append(("supplement", f"{len(sc['prompts'])} prompts, {self.sim.standalone_effort(sc['id']):.0f} word-equiv"))
        for k, v in kv:
            print(WHT(f"  {k:<30}") + AMB(v))
        for p in sc["prompts"]:
            pi = self.sim.prompts[self.sim.index[p["id"]]]
            print(DIM(f"   [{pi.words:>3}w {','.join(sorted(pi.themes)) or '-':<22}] ") + AMB(p["text"][:70]))

    def cmd_DQ(self, args):
        """DQ                    data-quality report for the catalog"""
        issues = validate(self.cat)
        if self.out(issues):
            return
        header("DQ", "DATA QUALITY", f"{sum(1 for i in issues if i[0] == 'ERROR')} errors / {sum(1 for i in issues if i[0] == 'WARN')} warnings")
        for sev, sid, msg in issues:
            print((RED if sev == "ERROR" else AMB)(f"  {sev:<6}") + WHT(f"{sid:<20}") + AMB(msg))

    def cmd_FIT(self, args):
        """FIT <outcomes.csv>    fit model parameters to real outcomes (marginal ML) + out-of-sample scores"""
        from .backtest import split_students
        from .fit import fit, load_outcomes, predict_leave_one_out, predict_marginal, score_all
        if not args:
            return print(RED("usage: FIT outcomes.csv   (student_id,school_id,ebrw,math,decision[,holistic_pct])"))
        o = load_outcomes(args[0])
        tr, te = split_students(o, 0.7)
        res = fit(self.cat, tr)
        Mf, Md = AdmissionModel(self.cat, res.params), AdmissionModel(self.cat)
        known = np.isin(te.school, Mf.usable())
        te = te.subset(known)
        sc = {"base rate": score_all(np.array([Md.cal[s].rate for s in te.school]), te.y),
              "default": score_all(predict_marginal(Md, te), te.y),
              "fitted": score_all(predict_marginal(Mf, te), te.y),
              "fitted + other decisions": score_all(predict_leave_one_out(Mf, te), te.y)}
        if self.out({"estimates": res.estimates, "se": res.std_errors, "scores": sc}):
            return
        header("FIT", "MAXIMUM MARGINAL LIKELIHOOD", f"{res.n_obs} apps / {res.n_students} students (70% train)")
        for k in res.estimates:
            print(WHT(f"  {k:<14}") + AMB(f"{res.estimates[k]:8.3f}  ± {1.96 * res.std_errors[k]:.3f} (95%)"))
        print()
        table([("HOLDOUT MODEL", 28, "<"), ("BRIER", 8, ">"), ("LOGLOSS", 9, ">"), ("AUC", 7, ">"), ("ECE", 7, ">")],
              [[k, f"{v['brier']:.4f}", f"{v['log_loss']:.4f}", f"{v['auc']:.3f}", f"{v['ece']:.3f}"] for k, v in sc.items()])

    def cmd_SIM(self, args):
        """SIM <out.csv> [n]     write a synthetic outcomes file (to try FIT / for demos)"""
        from .fit import save_outcomes, simulate
        from .backtest import TRUE
        path = args[0] if args else "synthetic_outcomes.csv"
        n = int(args[1]) if len(args) > 1 else 1000
        save_outcomes(simulate(self.cat, TRUE, n, 8, seed=42), path)
        print(AMB(f"  wrote {path} ({n} students × 8 apps)"))

    # session setters
    def cmd_SAT(self, args):
        """SAT <ebrw> <math>     set scores"""
        self.sess.ebrw, self.sess.math = float(args[0]), float(args[1])
        print(AMB(f"  EBRW {self.sess.ebrw:.0f}  MATH {self.sess.math:.0f}"))

    def cmd_HOL(self, args):
        """HOL <pct|off> [sd]    advisor-rated non-test strength as a percentile among applicants"""
        if not args or args[0].lower() == "off":
            self.sess.holistic_pct = None
        else:
            self.sess.holistic_pct = float(args[0])
            self.sess.holistic_sd = float(args[1]) if len(args) > 1 else None
        print(AMB(f"  holistic {self.sess.holistic_pct}"))

    def cmd_LIST(self, args):
        """LIST [+id|-id|id..]   show/replace/add/remove schools on the working list"""
        if args:
            if all(a[0] in "+-" for a in args):
                for a in args:
                    sid = a[1:]
                    if a[0] == "+" and sid in self.by_id and sid not in self.sess.schools:
                        self.sess.schools.append(sid)
                    elif a[0] == "-" and sid in self.sess.schools:
                        self.sess.schools.remove(sid)
            else:
                self.sess.schools = [a for a in args if a in self.by_id]
        print(AMB("  list: " + (" ".join(self.sess.schools) or "(empty = whole catalog)")))

    def cmd_UTIL(self, args):
        """UTIL <school> <0-100> preference utility for PLAN"""
        self.sess.utility[args[0]] = float(args[1])
        print(AMB(f"  utility {args[0]} = {args[1]}"))

    def cmd_CAT(self, args):
        """CAT                   catalog listing"""
        header("CAT", "CATALOG", f"{len(self.cat)} schools")
        rows = [[s["id"], s["name"][:24], f"{100 * s['acceptanceRate']:.1f}" if s.get("acceptanceRate") else "—",
                 s["importance"], len(s["prompts"]), s.get("provenance", "")] for s in self.cat]
        table([("ID", 20, "<"), ("NAME", 26, "<"), ("ADM%", 7, ">"), ("  TEST IMPORTANCE", 18, "<"), ("PROMPTS", 8, ">"),
               ("  SOURCE", 20, "<")], rows)

    def cmd_BRIEF(self, args):
        """BRIEF                 plain-English family brief: the analysis with no math, ready to paste"""
        s, M, st = self.sess, self.model, self.sess.student()
        ids = M.usable(self.ids(args))
        if not ids:
            return note("no modellable schools on the list")
        p = M.chances(st, ids, s.decisions or None)
        dist = M.count_distribution(st, ids, s.decisions or None)
        p_none = dist[0]
        p_ind_none = float(np.prod(1 - p))
        likely = [i for i, x in zip(ids, p) if x >= 0.6]
        lines = []
        one_in = lambda q: f"about 1 in {max(2, round(1 / q))}" if q > 0.005 else "under 1 in 200"  # noqa: E731
        lines.append(f"With this list of {len(ids)} schools, the chance of no admission anywhere is {one_in(p_none)} "
                     f"({100 * p_none:.0f}%). Treating the schools as independent would suggest {one_in(p_ind_none)}: "
                     f"the real risk is higher because the same application is read everywhere.")
        if len(likely) < 2:
            # what single addition from the catalog most reduces P(no admits)?
            best = None
            for c in M.usable():
                if c in ids:
                    continue
                q = M.count_distribution(st, ids + [c])[0]
                if best is None or q < best[1]:
                    best = (c, q)
            if best is None or best[1] > 0.8 * p_none:
                lines.append(f"Only {len(likely)} school(s) are likely admits (60%+), and nothing in the current catalog "
                             f"meaningfully lowers the no-admit risk: add a true safety (e.g. a rolling-admission or in-state school).")
            else:
                lines.append(f"Only {len(likely)} school(s) are likely admits (60%+). Adding {self.name(best[0])} would cut the "
                             f"no-admit risk to {one_in(best[1])}.")
        order = np.argsort(-p)
        top = ", ".join(f"{self.name(ids[i])} ({100 * p[i]:.0f}%)" for i in order[:3])
        lines.append(f"Strongest odds: {top}.")
        reach = [ids[i] for i in order if p[i] < 0.15]
        if len(reach) >= 2:
            X = M.cross_matrix(st, reach[:2], "accepted")
            a, b = reach[0], reach[1]
            lines.append(f"Reach schools move together: an admission at {self.name(a)} would raise {self.name(b)} from "
                         f"{100 * X[1, 1]:.0f}% to about {100 * X[0, 1]:.0f}%, so several reaches add less safety than they seem.")
        opt = [i for i in ids if M.cal[i].test_optional]
        withhold = [i for i in opt if not M.submit_policy(st, i)]
        if opt:
            lines.append("Test-optional schools: submit scores to " + (", ".join(self.name(i) for i in opt if i not in withhold) or "none")
                         + (("; consider withholding at " + ", ".join(self.name(i) for i in withhold)) if withhold else "") + ".")
        words = self.sim.list_effort(ids)
        alone = sum(self.sim.standalone_effort(i) for i in ids)
        lines.append(f"Supplemental writing: about {words:,.0f} words if essays are reused well, versus {alone:,.0f} written from "
                     f"scratch. Write the longest supplements first; later ones can borrow from them.")
        if self.out({"brief": lines}):
            return
        header("BRIEF", "FAMILY BRIEF", f"{st.ebrw:.0f}/{st.math:.0f}")
        import textwrap
        for ln in lines:
            print(AMB(textwrap.fill(ln, 94, initial_indent="  • ", subsequent_indent="    ")))
        note("  estimates, not guarantees; based on published admissions data and a statistical model (see PCTL/CHNC/XADM).")

    def cmd_LEDGER(self, args):
        """LEDGER <file.jsonl> [label]  freeze today's forecasts in an append-only, hash-chained ledger"""
        import datetime
        import hashlib
        if not args:
            return print(RED("usage: LEDGER forecasts.jsonl student-label"))
        path, label = args[0], (args[1] if len(args) > 1 else "student")
        M, st = self.model, self.sess.student()
        ids = M.usable(self.ids())
        p = M.chances(st, ids)
        prev = "0" * 64
        if os.path.exists(path):
            lines = [ln for ln in open(path, encoding="utf-8").read().splitlines() if ln.strip()]
            if lines:
                prev = json.loads(lines[-1])["hash"]
        with open(path, "a", encoding="utf-8") as f:
            for sid, pi in zip(ids, p):
                rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "student": label,
                       "school": sid, "p_admit": round(float(pi), 4), "ebrw": st.ebrw, "math": st.math, "prev": prev}
                rec["hash"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
                prev = rec["hash"]
                f.write(json.dumps(rec) + "\n")
        print(AMB(f"  froze {len(ids)} forecasts for {label} → {path}  (head {prev[:12]}…; publish the head hash to timestamp it)"))

    def cmd_SCORE(self, args):
        """SCORE <ledger.jsonl> <outcomes.csv>  verify the ledger's hash chain, then grade it (Brier/logloss/calibration)"""
        import csv as _csv
        import hashlib
        from .fit import score_all
        if len(args) < 2:
            return print(RED("usage: SCORE forecasts.jsonl outcomes.csv   (csv: student,school,decision)"))
        recs = [json.loads(ln) for ln in open(args[0], encoding="utf-8") if ln.strip()]
        prev, ok = "0" * 64, True
        for r in recs:
            body = {k: v for k, v in r.items() if k != "hash"}
            ok &= r["prev"] == prev and hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() == r["hash"]
            prev = r["hash"]
        out = {(row["student"], row["school"]): row["decision"].strip().lower() == "accepted"
               for row in _csv.DictReader(open(args[1], newline="", encoding="utf-8"))}
        pairs = [(r["p_admit"], float(out[(r["student"], r["school"])])) for r in recs if (r["student"], r["school"]) in out]
        header("SCORE", "FORECAST LEDGER GRADE", "chain " + ("VERIFIED" if ok else "TAMPERED"))
        if not pairs:
            return note("  no matching outcomes yet")
        pp, yy = np.array([a for a, _ in pairs]), np.array([b for _, b in pairs])
        sc = score_all(pp, yy)
        base = score_all(np.full_like(pp, yy.mean()), yy)
        for k in sc:
            print(WHT(f"  {k:<10}") + AMB(f"{sc[k]:.4f}") + DIM(f"   (constant-rate forecast: {base[k]:.4f})"))
        print(AMB(f"  graded {len(pairs)} of {len(recs)} frozen forecasts"))

    def cmd_HELP(self, args):
        """HELP                  this screen"""
        header("HELP", "UNIMATH FUNCTIONS", "<CMD> [args]  then <GO>/Enter")
        for name in sorted(n for n in dir(self) if n.startswith("cmd_")):
            doc = getattr(self, name).__doc__.strip().splitlines()[0]
            code, _, rest = doc.partition(" ")
            print(WHT(f"  {code:<6}") + AMB(rest.strip()))

    def run(self, line: str) -> bool:
        parts = shlex.split(line)
        if not parts:
            return True
        cmd, args = parts[0].upper(), parts[1:]
        if cmd in ("Q", "QUIT", "EXIT"):
            return False
        fn = getattr(self, f"cmd_{cmd}", None)
        if not fn:
            print(RED(f"  unknown function {cmd}; HELP for list"))
            return True
        try:
            fn(args)
        except Exception as exc:  # noqa: BLE001 - a terminal shouldn't die on one bad command
            print(RED(f"  error: {exc}"))
        return True


def main(argv=None):
    import signal
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # `unimath CHNC | head` shouldn't traceback
    ap = argparse.ArgumentParser(prog="unimath", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="*", help="mnemonic + args, e.g. CHNC mit stanford")
    ap.add_argument("-p", "--profile", help="TOML profile (see examples/)")
    ap.add_argument("--catalog", help="alternate catalog.json")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args(argv)
    sess = Session(json=a.json)
    if a.profile:
        load_profile(a.profile, sess)
    term = Terminal(sess, a.catalog)
    if a.command:
        term.run(" ".join(shlex.quote(x) for x in a.command))
        return
    header("UNIMATH", "ADMISSIONS ANALYTICS TERMINAL", "HELP for functions · Q to quit")
    while True:
        try:
            line = input(AMB("UNIMATH> ") if COLOR else "UNIMATH> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not term.run(line):
            break


if __name__ == "__main__":
    main()
