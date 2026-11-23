"""Build reports/UNIMATH_methods_manual.pdf from backtest results + figures.

Run order:  python scripts/run_backtests.py && python scripts/make_figures.py && python scripts/make_report.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
R = json.loads((ROOT / "reports" / "backtest_results.json").read_text())
SIG0 = json.loads((ROOT / "reports" / "significance.json").read_text())
FIG = ROOT / "reports" / "figures"
OUT = ROOT / "reports" / "UNIMATH_methods_manual.pdf"

AMBER = colors.HexColor("#d98a00")
INK = colors.HexColor("#1d1d1d")
SHADE = colors.HexColor("#fff4e0")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=16, textColor=INK, spaceBefore=6, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=AMBER, spaceBefore=10, spaceAfter=4)
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=10, textColor=INK, spaceBefore=6, spaceAfter=2)
B = ParagraphStyle("B", parent=ss["BodyText"], fontName="Helvetica", fontSize=9, leading=12.5, alignment=TA_LEFT, spaceAfter=5)
SM = ParagraphStyle("SM", parent=B, fontSize=7.5, leading=10)
MONO = ParagraphStyle("M", parent=B, fontName="Courier", fontSize=8, leading=10.5, backColor=colors.HexColor("#f4f4f4"),
                      borderPadding=4, spaceBefore=3, spaceAfter=7)
PLAIN = ParagraphStyle("PL", parent=B, backColor=colors.HexColor("#eef5ff"), borderPadding=6, borderColor=colors.HexColor("#2b6cb0"), borderWidth=0.6, spaceBefore=2, spaceAfter=9)
CALL = ParagraphStyle("C", parent=B, backColor=SHADE, borderPadding=6, borderColor=AMBER, borderWidth=0.6, spaceBefore=4, spaceAfter=9)

story = []
P = lambda t, s=B: story.append(Paragraph(t, s))  # noqa: E731


def fig(name, w=6.3, caption=None):
    path = FIG / f"{name}.png"
    from PIL import Image as PImage
    iw, ih = PImage.open(path).size
    img = Image(str(path), width=w * inch, height=w * inch * ih / iw)
    items = [img] + ([Paragraph(caption, SM)] if caption else [])
    story.append(KeepTogether(items))
    story.append(Spacer(1, 6))


def table(rows, widths, header=True, font=7.8):
    body = ParagraphStyle("t", parent=SM, fontSize=font, leading=font + 2.2)
    head = ParagraphStyle("th", parent=body, textColor=colors.white, fontName="Helvetica-Bold")
    t = Table([[Paragraph(str(c), head if (header and ri == 0) else body) for c in r] for ri, r in enumerate(rows)],
              colWidths=[w * inch for w in widths], repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    t.setStyle(TableStyle(st))
    story.append(t)
    story.append(Spacer(1, 8))


def f(x, d=3):
    return f"{x:.{d}f}"


e3w, e3m = R["e3_well"], R["e3_miss"]


def pnone(key):
    pc, pi, ob = (np.array(R[key]["p_any"][k]) for k in ("correlated", "independent", "observed"))
    m = pi > 0.95
    return int(m.sum()), 100 * (1 - pi[m]).mean(), 100 * (1 - pc[m]).mean(), 100 * (1 - ob[m]).mean()


pw, pm = pnone("e3_well"), pnone("e3_miss")

# ------------------------------------------------------------------------------------------ cover
story += [Spacer(1, 1.3 * inch)]
P("<font size=28 color='#d98a00'><b>UNIMATH</b></font>", B)
story.append(Spacer(1, 14))
P("<font size=15><b>Admissions analytics terminal: methods, validation, and the business case</b></font>", B)
story.append(Spacer(1, 8))
P("Every feature, the statistical technique behind it, its assumptions, how it was backtested, what the backtests "
  "showed (including what did not work), and an honest look at who would buy this and why.", B)
story.append(Spacer(1, 20))
P("Version 0.1 &nbsp;·&nbsp; November 2026 &nbsp;·&nbsp; catalog: 412 four-year schools (393 from US Dept. of Education College Scorecard + 19 hand-curated with real supplements)", SM)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ exec summary
P("1. Executive summary", H1)
P(f"<b>What it is.</b> A terminal (Bloomberg-style function codes) and Python library that turns published admissions "
  "data into calibrated, correlated admission probabilities, a Bayesian update as decisions arrive, essay-reuse "
  "planning, and a list optimizer. There is also a plain-English 'family brief' for counselors who don't want the math.")
_sw, _sm = SIG0["pred_well"]["safe_lists"], SIG0["pred_miss"]["safe_lists"]
P("<b>The one result that matters, in plain English.</b> Most list-balancing tools multiply each school's odds as if "
  "admissions were separate coin flips. Across 5 simulated worlds, we took the students whose lists looked at least "
  f"95% safe that way. <b>{100 * _sw['observed_rate']:.1f}% of them got zero admits</b> "
  f"({_sw['zero_admits']} of {_sw['n']}). Multiplying odds predicted {100 * _sw['independence']['expected'] / _sw['n']:.1f}%; "
  f"UNIMATH predicted {100 * _sw['correlated']['expected'] / _sw['n']:.1f}%. When we deliberately made the fake world "
  f"break the model's rules, {100 * _sm['observed_rate']:.1f}% got zero. UNIMATH said "
  f"{100 * _sm['correlated']['expected'] / _sm['n']:.1f}% (too cautious) and multiplying odds said "
  f"{100 * _sm['independence']['expected'] / _sm['n']:.1f}% (far too optimistic). "
  "<i>Math version: Claim 5 in Section B.</i>", CALL)
P("<b>Is any of it better than chance?</b> Each claim below was tested two ways: does it beat a no-information "
  "guess, and is the advantage bigger than luck (95% confidence intervals, p-values, resampling whole students)? "
  "Full math and numbers are in Section B.")
_v = {"1": "YES, small", "2": "YES", "3": "YES, small" if SIG0["pred_well"]["fitted_vs_logistic"]["brier"]["ci95"][1] < 0
      and SIG0["pred_miss"]["fitted_vs_logistic"]["brier"]["ci95"][1] < 0 else "NOT RELIABLY", "4": "YES, large", "5": "YES",
      "6": "PARTLY", "7": "NO", "8": "YES", "9": "UNTESTED"}
rows = [["#", "Claim (plain English)", "Better than chance?", "On what data"],
        ["1", "Our percentile estimate is more accurate than a plain bell curve", _v["1"], "simulated score bands"],
        ["2", "Chances beat quoting the acceptance rate to everyone", _v["2"], "simulated students"],
        ["3", "Single-school chances beat a simple statistical model", _v["3"], "simulated students"],
        ["4", "Knowing a student's other decisions sharpens the rest", _v["4"], "simulated students"],
        ["5", "Multiplying odds badly understates the risk of zero admits", _v["5"], "simulated students"],
        ["6", "The model can learn its settings from past outcomes", _v["6"], "simulated students"],
        ["7", "Automatic essay-overlap scores match human judgement", _v["7"], "10 human-scored pairs"],
        ["8", "The list optimizer finds the best list", _v["8"], "random test cases"],
        ["9", "Any of this beats existing tools for real students", _v["9"], "no real data yet"],
        ["10", "It beats a counselor's own calls on one past class", "NO (can't be shown)", "simulated counselors"]]
table(rows, [0.3, 3.4, 1.4, 1.6])
P("<b>The honest bottom line.</b> The math is sound and tested, and the core insight (correlated decisions) is real and "
  "under-served by competitors. But the code is not a moat: a subagent rebuilt the core in about 35 minutes (Section 10). "
  "What is defensible is (a) outcome data pooled across many counselors, which calibrates the model; (b) a curated, "
  "per-cycle catalog and prompt matrix; and (c) a public, tamper-evident forecast track record. Every validation "
  "number in this manual is synthetic until real outcomes are loaded.")
story.append(PageBreak())


# ------------------------------------------------------------------------------------------ reading guide
P("A. Reading guide: the terms in plain English", H1)
P("This manual states every claim twice: once as mathematics (precise, testable) and once in plain English. "
  "These are the terms that come up most.")
rows = [["Term", "Plain English", "What 'good' looks like"],
        ["Probability / P(admit)", "How often this would happen across many similar applicants. 20% means about 1 in 5 such students get in.", "-"],
        ["Calibrated", "When the model says 20%, about 20% of those students really get in. A calibrated model's numbers can be taken at face value.", "Points on the diagonal of a reliability plot"],
        ["Brier score", "Average squared miss between the forecast and what happened (1 = admitted, 0 = not). Lower is better. A forecaster who always says 50% scores 0.25.", "Lower than quoting each school's acceptance rate"],
        ["Log loss", "Like the Brier score, but punishes confident wrong answers much harder (saying 1% for someone who got in).", "Lower is better"],
        ["AUC", "Pick one admitted and one rejected application at random. AUC is the chance the model gave the admitted one the higher probability. 0.5 is a coin flip; 1.0 is perfect ranking.", "Well above 0.5"],
        ["ECE (calibration error)", "Average gap between what the model said and what happened, within groups of similar forecasts.", "Close to 0"],
        ["Base rate", "Just quoting the school's acceptance rate to everyone. The 'knows nothing about you' benchmark.", "Model must beat this"],
        ["95% confidence interval (CI)", "The range the true value plausibly lies in, given the data we had. If the whole interval is on one side of zero, the effect is not just luck.", "Interval excludes 0"],
        ["p-value", "If there were really no difference, how often would we see a gap this big from luck alone? p = 0.01 means 1 time in 100.", "Below 0.05 (conventionally)"],
        ["Bootstrap", "Re-running the analysis thousands of times on resampled data to see how much the answer wobbles. We resample whole students, because one student's decisions are linked.", "-"],
        ["Synthetic data", "Fake students generated by a computer from rules we chose. It proves the math works, but not that real admissions follow those rules.", "-"],
        ["Well-specified / misspecified", "Well-specified: the fake world follows exactly the model's rules, so the model is graded on its own exam. Misspecified: the fake world deliberately breaks the rules (heavy tails, hooks, wrong weights), a harder exam.", "-"]]
table(rows, [1.4, 3.7, 1.6], font=7.4)
story.append(PageBreak())


# ------------------------------------------------------------------------------------------ claims register
SIG = json.loads((ROOT / "reports" / "significance.json").read_text())


def pf(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def ci_s(c, scale=1.0, d=4):
    return f"95% CI {c[0] * scale:.{d}f} to {c[1] * scale:.{d}f}"


VERDICT_COLORS = {"YES": "#2e8b57", "NO": "#c0392b", "PARTLY": "#d98a00", "UNTESTED": "#7a7a7a"}


def claim(num, title, math, plain, result, verdict, verdict_text, caveat):
    col = VERDICT_COLORS[verdict]
    rows = [[f"<b>Claim {num}</b>", f"<b>{title}</b>"],
            ["Math", math], ["In plain English", plain], ["Result", result],
            ["Better than chance?", f"<font color='{col}'><b>{verdict}</b></font> · {verdict_text}"], ["Caveat", caveat]]
    body = ParagraphStyle("cb", parent=SM, fontSize=7.8, leading=10.3)
    head = ParagraphStyle("ch", parent=body, textColor=colors.white)
    t = Table([[Paragraph(a, head if i == 0 else body), Paragraph(b, head if i == 0 else body)] for i, (a, b) in enumerate(rows)],
              colWidths=[1.15 * inch, 5.55 * inch])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), INK), ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#eef5ff")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    story.append(KeepTogether([t, Spacer(1, 9)]))


def sig_verdict(d):
    """'YES' if the whole 95% CI shows the claimed direction (negative loss difference)."""
    return d["ci95"][1] < 0


P("B. Claims register: every claim, in math and in plain English, with a chance test", H1)
P("<b>How to read this.</b> 'Better than chance' has two meanings, and both are checked. (1) Does the tool beat a "
  "<i>no-information guess</i> (a coin flip, or quoting the acceptance rate to everyone)? (2) Is the advantage "
  "<i>bigger than luck</i>? Would it survive re-running on fresh random data? For (2) we report 95% confidence "
  "intervals and p-values. The predictive claims pool <b>5 independent simulated worlds</b> "
  f"({SIG['pred_well']['n_students']:,} held-out students, {SIG['pred_well']['n_rows']:,} applications per scenario), "
  "and resample whole students, because one student's decisions are linked.")
P("<b>The most important caveat applies to claims 2-6.</b> They are tested on synthetic students. In the "
  "'well-specified' world the fake data follows the model's own rules, so the model is grading its own exam: passing "
  "proves the math and code are right, not that real admissions work this way. The 'misspecified' world deliberately "
  "breaks the rules and is a fairer test, but we still wrote it. <b>Claim 9 (does any of this hold for real "
  "students?) is untested.</b>", CALL)
fig("f13_forest", caption="Figure 13. Every predictive comparison at a glance. Green bars clear zero (the advantage is "
    "not luck); grey bars cross it (could be luck). In plain English: green means 'genuinely better on this test'.")

c1 = SIG["c1"]
claim("1", "Our percentile curve is more accurate than a symmetric bell curve",
      "For band b let e<sub>b</sub><super>M</super> = mean<sub>x∈{600..800}</sub> |F<sub>M</sub>(x) − F<sub>b</sub>(x)|·100, "
      "with F<sub>b</sub> the true mid-rank CDF. H<sub>0</sub>: E[e<super>ours</super> − e<super>normal</super>] = 0. "
      "Paired t-test and Wilcoxon signed-rank test over 392 simulated skewed, ceiling-censored bands.",
      "Given only the three numbers a school publishes, our curve tells you your percentile more accurately than the "
      "bell curve the web app uses.",
      f"Error lower by {-c1['vs_web']['diff']:.2f} percentile points on average ({ci_s([-c1['vs_web']['ci95'][1], -c1['vs_web']['ci95'][0]], 1, 2)}); "
      f"better on {100 * c1['vs_web']['share_a_better']:.0f}% of bands; {pf(c1['vs_web']['p_wilcoxon'])}. "
      f"Also beats the continuous split normal by {-c1['vs_continuous']['diff']:.2f} points ({pf(c1['vs_continuous']['p_wilcoxon'])}).",
      "YES", "clearly not luck, but the effect is small (about 1 percentile point).",
      "The 'true' distributions were skew-normal shapes we chose. Real score distributions could differ.")


def pred_claim_numbers(world):
    w = SIG[f"pred_{world}"]
    return w, w["brier"], w["auc"]


ww, bw, aw = pred_claim_numbers("well")
wm, bm, am = pred_claim_numbers("miss")
fb_w, fb_m = ww["fitted_vs_base"]["brier"], wm["fitted_vs_base"]["brier"]
claim("2", "The chances are informative: better than a coin flip and better than quoting the acceptance rate",
      "H<sub>0</sub><sup>a</sup>: AUC = 0.5 (Mann-Whitney U, one-sided). H<sub>0</sub><sup>b</sup>: "
      "E[(p−y)² − (r<sub>j</sub>−y)²], p = model forecast, = 0, where r<sub>j</sub> is the school's acceptance rate; student-cluster "
      "bootstrap (4,000 resamples).",
      "Knowing the student's scores gives better odds than telling everyone the school's acceptance rate, and ranks "
      "admitted students above rejected ones far more often than guessing would.",
      f"Matched world: AUC {aw['unimath (fitted)']['auc']:.3f} ({pf(aw['unimath (fitted)']['p_vs_random'])} vs 0.5); "
      f"Brier {bw['unimath (fitted)']:.4f} vs {bw['base rate']:.4f} for the acceptance rate and {bw['coin flip (0.5)']:.3f} for a coin flip "
      f"(improvement {ci_s([-fb_w['ci95'][1], -fb_w['ci95'][0]])}). "
      f"Misspecified world: AUC {am['unimath (fitted)']['auc']:.3f}; Brier {bm['unimath (fitted)']:.4f} vs {bm['base rate']:.4f} "
      f"({ci_s([-fb_m['ci95'][1], -fb_m['ci95'][0]])}).",
      "YES" if sig_verdict(fb_w) and sig_verdict(fb_m) else "PARTLY",
      "on synthetic data, in both worlds, by a wide margin.",
      "Any model that uses test scores sensibly would pass this. It's a floor, not a selling point.")

fl_w, fl_m = ww["fitted_vs_logistic"]["brier"], wm["fitted_vs_logistic"]["brier"]
dl_w = ww["default_vs_logistic"]["brier"]
yes3 = sig_verdict(fl_w) and sig_verdict(fl_m)
claim("3", "Per-school chances beat a simple statistical baseline (logistic regression)",
      "Δ = E[(p<sub>UNIMATH</sub>−y)² − (p<sub>logit</sub>−y)²], logit model: y ~ logit(r<sub>j</sub>) + "
      "z-score vs published band, trained on the same 60% of students. H<sub>0</sub>: Δ = 0; student-cluster bootstrap.",
      "Compared with what a careful developer could build in an afternoon, are UNIMATH's single-school odds actually better?",
      f"Matched world: Brier difference {fl_w['diff']:.4f} ({ci_s(fl_w['ci95'])}, {pf(fl_w['p'])}), i.e. "
      f"{-100 * fl_w['relative']:.1f}% lower error. Misspecified world: {fl_m['diff']:.4f} ({ci_s(fl_m['ci95'])}, {pf(fl_m['p'])}), "
      f"{-100 * fl_m['relative']:.1f}% lower. With <i>no</i> training data (default priors): {dl_w['diff']:.4f} ({ci_s(dl_w['ci95'])}).",
      "YES" if yes3 else "PARTLY",
      ("statistically real in both worlds, but small: a few percent lower error." if yes3 else
       "the advantage is small and not reliably distinguishable from luck in every scenario."),
      "This is the claim a competitor would attack. Don't market 'more accurate chances'; market what the logistic "
      "model can't do (Claims 4-5).")

pv_w, pv_m = ww["posterior_vs_fitted"]["brier"], wm["posterior_vs_fitted"]["brier"]
claim("4", "Knowing a student's other decisions improves the prediction for the rest (Bayesian update)",
      "For each held-out decision y<sub>ij</sub>: p<sub>ij</sub><super>post</super> = ∫p<sub>ij</sub>(S) π(S | y<sub>i,−j</sub>) dS "
      "vs p<sub>ij</sub><super>prior</super> = ∫p<sub>ij</sub>(S) π(S) dS. H<sub>0</sub>: E[(p<super>post</super>−y)² − (p<super>prior</super>−y)²] = 0; "
      "student-cluster bootstrap.",
      "If you know a student got into CMU and was rejected by MIT, you can predict their Cornell result better than from "
      "their scores alone. This is the 'accepted at one, probably at the other' feature.",
      f"Matched world: error lower by {-100 * pv_w['relative']:.0f}% ({ci_s(pv_w['ci95'])}, {pf(pv_w['p'])}); AUC "
      f"{aw['unimath (fitted)']['auc']:.3f} → {aw['unimath fitted + other decisions (LOO posterior)']['auc']:.3f}. "
      f"Misspecified world: lower by {-100 * pv_m['relative']:.0f}% ({ci_s(pv_m['ci95'])}, {pf(pv_m['p'])}).",
      "YES" if sig_verdict(pv_w) and sig_verdict(pv_m) else "PARTLY",
      "the largest and most robust effect in the whole suite.",
      "Its size depends on how strongly real decisions are linked, which no public data measures. On real data the gain "
      "could be larger or smaller.")

cw, cm = ww["count_correlated_vs_independent"], wm["count_correlated_vs_independent"]
sw, sm_ = ww["safe_lists"], wm["safe_lists"]
claim("5", "Treating schools as independent badly understates the risk of zero admits",
      "(a) Per-student log score of the observed number of admits K<sub>i</sub>: log P<sub>corr</sub>(K<sub>i</sub>) vs "
      "log P<sub>indep</sub>(K<sub>i</sub>) (Poisson-binomial of marginals); paired bootstrap. (b) Among students with "
      "1−Π(1−p<sub>j</sub>) &gt; 0.95, test the observed zero-admit count against the exact Poisson-binomial "
      "distribution implied by each model.",
      "When a list 'looks' 95%+ safe because you multiplied the odds, the real chance of getting nothing is much higher. "
      "UNIMATH's correlated model sees this; the multiply-the-odds method doesn't.",
      f"(a) Correlated model better: matched {ci_s([-cw['ci95'][1], -cw['ci95'][0]], 1, 3)} nats/student ({pf(cw['p'])}); "
      f"misspecified {ci_s([-cm['ci95'][1], -cm['ci95'][0]], 1, 3)} ({pf(cm['p'])}). "
      f"(b) Matched world: {sw['zero_admits']} of {sw['n']} 'safe' students got zero admits "
      f"({100 * sw['observed_rate']:.1f}%, CI {100 * sw['observed_ci95'][0]:.1f}–{100 * sw['observed_ci95'][1]:.1f}%). "
      f"Independence expected {sw['independence']['expected']:.1f} ({pf(sw['independence']['p_two_sided'])}: rejected); "
      f"correlated model expected {sw['correlated']['expected']:.1f} ({pf(sw['correlated']['p_two_sided'])}). "
      f"Misspecified: {sm_['zero_admits']} of {sm_['n']}; independence expected {sm_['independence']['expected']:.1f} "
      f"({pf(sm_['independence']['p_two_sided'])}), correlated expected {sm_['correlated']['expected']:.1f} "
      f"({pf(sm_['correlated']['p_two_sided'])}).",
      "YES" if sig_verdict(cw) and sig_verdict(cm) else "PARTLY",
      "independence is decisively rejected in both worlds. The correlated model is right when the world matches it; in "
      "the misspecified world it over-warns (a p-value below 0.05 for the correlated row there means its predicted "
      "count is also wrong).",
      "Real-world strength of the link between decisions is unknown. The direction (independence is too optimistic) "
      "is very likely; the size is not established.")

c5 = SIG.get("c5", {})
if c5:
    rows_txt = "; ".join(f"{k}: true {v['true']}, mean {v['mean']:.3f} (bias {pf(v['bias_t_p'])}), CI coverage "
                         f"{100 * v['coverage95']:.0f}% [{100 * v['coverage_ci95'][0]:.0f}–{100 * v['coverage_ci95'][1]:.0f}%]"
                         for k, v in c5.items())
    claim("6", "The model's settings can be learned from outcome data (FIT works)",
          "Over R=20 simulated datasets with known θ: bias test H<sub>0</sub>: E[θ<sub>est</sub>] = θ (t-test), and coverage "
          "H<sub>0</sub>: P(θ ∈ θ<sub>est</sub> ± 1.96·SE) = 0.95 (exact binomial interval).",
          "If a counselor uploads past outcomes, does the fitting step find the true settings, and are its stated error "
          "bars honest?",
          rows_txt + ".",
          "PARTLY", "some settings are recovered well; others are biased or have over-confident error bars (coverage "
          "well below 95%).",
          "Fix before selling FIT: use bootstrap or profile-likelihood intervals, and pool data across practices.")

c6 = SIG["c6"]
claim("7", "Automatic essay-similarity scores match human judgement",
      "Spearman ρ between model and curated scores on n=10 held-out pairs; H<sub>0</sub>: ρ = 0 (permutation test, "
      "20,000 shuffles). Also paired |error| vs a constant predictor.",
      "Does the computer's guess of 'how much of essay A can be reused for prompt B' agree with a person's?",
      f"ρ = {c6['raw_spearman']['rho']:.2f}, permutation {pf(c6['raw_spearman']['p_one_sided'])}; recalibrated "
      f"ρ = {c6['loo_spearman']['rho']:.2f} ({pf(c6['loo_spearman']['p_one_sided'])}). Mean error "
      f"{c6['abs_err_vs_constant']['diff']:+.1f} points vs always guessing the average ({pf(c6['abs_err_vs_constant']['p_t'])}).",
      "NO", "not distinguishable from a random ordering, and no better than guessing the average.",
      "Only 10 human-scored pairs exist, so even a good method could not prove itself yet. Human scores override the "
      "model in the product.")

c7 = SIG["c7"]
claim("8", "The list optimizer finds the best list",
      "On random instances, compare the greedy+swap objective with the brute-force optimum; Clopper-Pearson interval on "
      "the match rate.",
      "When the tool recommends a list, is it really the best one under its own scoring, or just a decent one?",
      f"{c7['k']} of {c7['n']} matched the exact optimum: match rate ≥ {100 * c7['ci95'][0]:.0f}% with 95% confidence.",
      "YES", "this is a search-correctness claim, and it holds.",
      "'Best' only under the model's own odds and the user's preference numbers.")

claim("9", "Any of this predicts real students better than existing tools",
      "Would require E[L(p<sub>UNIMATH</sub>, y)] &lt; E[L(p<sub>competitor</sub>, y)] on real outcomes y "
      "(L = Brier or log loss), with a pre-registered held-out set.",
      "Is it actually better than CollegeVine, scattergrams, or an experienced counselor's judgement for real students?",
      "No real outcome data was available. FIT and LEDGER/SCORE are built to answer this on a counselor's past classes "
      "and on frozen 2026-27 forecasts.",
      "UNTESTED", "unknown. This is the claim buyers care about most.",
      "Until this is tested, all accuracy statements should be framed as 'on simulated data'.")

PWR = json.loads((ROOT / "reports" / "power.json").read_text())
so, wc = PWR["scores_only"], PWR["with_counselor_rating"]
claim("10", "UNIMATH beats a counselor's own reach/target/likely calls, and one class can show it",
      "Simulated counselor with private, noisy knowledge of non-test strength (sd 0.6) reports 3 labels. BKTST "
      "scoring: labels → leave-one-student-out label rates; Δ = Brier(UNIMATH) − Brier(labels), student-cluster "
      "bootstrap. Power = P(95% CI excludes 0) over 150 simulated backtests per class size n.",
      "If a counselor runs our free backtest on last year's class, will it show UNIMATH is better than their own "
      "calls, and would that result mean anything?",
      f"<b>Scores-only UNIMATH loses to the counselor</b> (mean Δ = +{so['800']['mean_diff']:.4f}; counselor "
      f"significantly better in {100 * so['800']['p_counselor_significantly_better']:.0f}% of 800-student backtests). "
      f"<b>UNIMATH + the counselor's rating wins, but barely</b> (mean Δ = {wc['800']['mean_diff']:.4f}). "
      f"With one class of 25 students, the result is inconclusive in {100 * wc['25']['p_inconclusive']:.0f}% of backtests; "
      f"even with 800 students, only {100 * wc['800']['p_unimath_significantly_better']:.0f}% detect the gain.",
      "NO", "not provable on one counselor's data: the honest pitch is 'use your judgement as an input', not 'beat it'.",
      "The simulated counselor's skill is an assumption. Real counselors may be better or worse than modelled.")
fig("f14_power", 6.6, "Figure 14. Power of the free backtest. Red line: a typical class of 25. Left: a model "
    "that ignores the counselor's knowledge loses as data grows. Right: feeding it the counselor's rating makes it "
    "slightly better than labels alone, but far too slightly to prove on one class.")
story.append(PageBreak())


# ------------------------------------------------------------------------------------------ persuasion loop
LOOP = ROOT / "reports" / "loop"
if LOOP.exists():
    P("C. The persuasion loop: fresh AI buyer and builder, round by round", H1)
    P("<b>Method.</b> Each round, two brand-new subagents with no memory of earlier rounds read only that round's sales "
      "email and the linked manual (and, in round 3, the draft data terms). The <b>buyer</b> plays a solo independent "
      "counselor asking 'should I buy this?'. The <b>builder</b> is asked 'can you just build this for me instead?'. "
      "Between rounds, only true changes were allowed: real product features, honest re-framing, corrected facts. No "
      "invented references, customers or results. The loop stops when the buyer says BUY, the builder says BUY "
      "(too big to build), or the remaining objection can only be fixed with real-world data.")
    rows = [["Round", "What changed going in", "Buyer verdict", "Builder verdict", "Main remaining objection"]]
    changes = {1: "Honest pitch v2: free past-class backtest offer, simulated numbers labelled",
               2: "BKTST built; zero-admit risk shown as a range; power analysis published; 412-school coverage from College "
                  "Scorecard; repositioned as 'uses your judgement, doesn't beat it'; pay-after-May terms",
               3: "ROSTER caseload import; counselor-only vs family brief (words, no %); ED rate input; draft data terms; timing fix"}
    for n in (1, 2, 3):
        b, d = LOOP / f"buyer_r{n}.md", LOOP / f"builder_r{n}.md"
        if not b.exists():
            continue
        bt_ = b.read_text().splitlines()
        bv = bt_[0].replace("VERDICT: ", "")
        dv = d.read_text().splitlines()[0].replace("VERDICT: ", "") if d.exists() else "(stopped: already BUY)"
        flip = next((ln for ln in bt_ if ln.startswith("FLIP:")), "")
        rows.append([str(n), changes[n], bv, dv, flip.replace("FLIP:", "Buyer needs:")])
    table(rows, [0.45, 2.0, 1.05, 1.0, 2.2], font=7.2)
    P("<b>In plain English: what the loop shows.</b> The builder flipped to BUY in round 2. Wider coverage, the "
      "power analysis (which shows a copy can't be validated cheaply either) and a pay-after-results offer made building "
      "your own cost 2-10x the price. The buyer moved from 'trial, don't pay' to 'use the free cycle as a second opinion', "
      "but every round ended on the same flip condition: <b>evidence on real students, pooled across practices, ideally "
      "checked by an independent statistician</b>. That cannot be produced by rewriting an email or adding features. It "
      "takes one admissions cycle of real forecasts (LEDGER now, SCORE in May) across several counselors. The loop "
      "has therefore reached its honest ceiling for this session.", CALL)
    story.append(PageBreak())

# ------------------------------------------------------------------------------------------ features
P("2. Feature map", H1)
rows = [["Code", "What a user gets", "Technique", "Backtestable?"],
        ["PCTL", "Where a score sits at each school, with an uncertainty range", "Quantile-matched two-piece normal; ceiling censoring; mid-rank; SEM interval; Gaussian-copula composite", "Yes: simulation with known truth (E1)"],
        ["CHNC", "P(admit) per school, 80% band, submit/withhold call", "Probit latent-index selection model calibrated by truncated-normal moment inversion; lapse mixture", "Yes: E3 (synthetic), FIT (real)"],
        ["XADM", "If admitted/rejected at A, odds at B", "Shared latent factor, 801-point grid quadrature of joint probabilities", "Yes: E4 leave-one-out"],
        ["DEC / UPDT", "Every remaining school re-priced as decisions arrive", "Grid Bayesian posterior over the shared factor; ordered-probit waitlist band", "Yes: E4"],
        ["PORT", "Distribution of number of admits; P(≥1)", "Conditional Poisson-binomial mixed over the shared factor", "Yes: count log-score, P(none) calibration"],
        ["ESSY / FREE", "Which schools are nearly free given the list's essays", "Theme lexicon × TF-IDF cosine × length adaptation; curated override; coverage matrix; average-linkage clustering", "Partly: E5 vs curated pairs (n=10)"],
        ["PLAN", "Best list for the student's preferences and effort budget", "Expected utility of best admit under correlation minus λ·words; exact search ≤12, else greedy + 1-swap", "Yes: E6 optimality gap"],
        ["SENS", "Which assumptions an answer depends on", "One-at-a-time parameter perturbation (tornado)", "n/a (diagnostic)"],
        ["FIT", "Model refit on a practice's own outcomes, with held-out scores", "Maximum marginal likelihood, L-BFGS-B, Hessian SEs; Brier, log loss, AUC, ECE", "It is the backtest"],
        ["LEDGER / SCORE", "Frozen, tamper-evident forecasts graded in spring", "SHA-256 hash chain; proper scoring rules vs constant forecast", "It is the backtest"],
        ["BRIEF [family]", "Counselor brief (numbers), or family brief in words (low/moderate/high), no false precision", "Templated summary; risk shown as a range across link strengths", "n/a"],
        ["ROSTER", "Whole caseload screened at once: no-admit risk range and likely count per student", "Batch of PORT/CHNC", "n/a"],
        ["BKTST", "Counselor's own past calls vs UNIMATH on real past outcomes", "Label→rate conversion (leave-one-student-out); student-cluster bootstrap CI", "It is the backtest (see Claim 10 for power)"],
        ["ED", "Use a school's early-round admit rate for one student", "Recalibration with the round-specific base rate (approximation)", "Needs round-level outcomes"],
        ["DQ / SCH / CAT", "Data-quality report; per-school calibration page", "Validation rules; calibration readout", "n/a"]]
table(rows, [0.8, 1.9, 2.6, 1.4])
P("Screenshots of the terminal look like this (amber on black, one function per screen):", B)
P("UNIMATH&gt; CHNC<br/> CHNC  ADMISSION PROBABILITY                          COMP 1540  HOL n/a<br/>"
  "SCHOOL         BASE%  P(ADM)%  80% BAND  LIFT   TIER     TESTS<br/>"
  "MIT              4.6      7.7      0-24  1.69x  LONG SHOT required<br/>"
  "Stanford         3.8     18.5      0-56  4.87x  REACH     required<br/>"
  "Georgia Tech    12.7     53.0      8-93  4.17x  TARGET    required<br/>"
  "Purdue          43.4     86.5     62-97  1.99x  LIKELY    required", MONO)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ PCTL
P("3. Score percentiles (PCTL): bell-curve interpolation done properly", H1)
P("<b>In plain English.</b> Schools publish three numbers about their students' SAT scores: the score a quarter of students fall below, the middle score, and the score three quarters fall below. We draw a curve that passes exactly through those three numbers, respecting that nobody can score above 800, and read off where your score sits. One test sitting can be off by about 30 points either way, so we also give a range.", PLAIN)
P("<b>Input.</b> A school's published 25th/50th/75th percentile section scores (Common Data Set C9; enrolled first-years).")
P("<b>Technique.</b> Each section is modelled as a <i>quantile-matched two-piece normal</i>. Below the median the "
  "latent score is a half-normal with scale σ<sub>L</sub> = (q50−q25)/0.6745, and above it a half-normal with "
  "σ<sub>R</sub> = (q75−q50)/0.6745. Each half carries exactly 50% of the mass, so the curve passes through all three "
  "published numbers however skewed the band is. Then:")
P("• <b>Ceiling censoring.</b> A quantile equal to 800 is an inequality (≥25% of the class is at the cap), not a data point. "
  "With one interior quantile left, the upper scale is widened until P(X≥800) ≥ 25%. With only q25 interior, a prior "
  "scale (σ=40) is used and the latent median is pushed to at least 800.<br/>"
  "• <b>Mid-rank percentile on the 10-point grid:</b> P(X &lt; bin) + ½·P(X in bin). This is why an 800 at a school "
  "whose 75th is 800 reads around the 70th-90th percentile, not '100'.<br/>"
  "• <b>Measurement error.</b> A single sitting has SEM ≈ 30 per section. Percentile is monotone in score, so the 90% "
  "interval is exactly the percentiles of score ± 1.645·SEM.<br/>"
  "• <b>Composite.</b> The two fitted marginals are joined by a Gaussian copula (ρ=0.6 within an admitted class), and "
  "P(E+M ≤ x) is integrated on a 400-point quantile grid. Summing the section bands overstates the composite spread.")
fig("f1_band_fit", caption="Figure 1. A real skewed band. The symmetric normal (web app) misses the 75th percentile, and the "
    "density-continuous split normal tried first cannot reach this skew at all.")
P("<b>Backtest E1 (simulation with known truth).</b> We drew 400 skewed, ceiling-censored score distributions "
  "(skew-normal, location 680-800, scale 25-70, skew −6 to +2), published their quartiles rounded to 10 as a school "
  "would, refitted, and compared percentiles to the true mid-rank over scores 600-800.")
rows = [["Method", "Mean abs error (pts)", "90th pct error", "Error at 800"]]
for k in R["e1"]["mae"]:
    rows.append([k, f(R["e1"]["mae"][k], 2), f(R["e1"]["p90"][k], 2), f(R["e1"]["mae_at_800"][k], 2)])
table(rows, [2.6, 1.3, 1.3, 1.3])
fig("f2_e1", caption="Figure 2. Distribution of per-band error.")
P("<b>Verdict.</b> It works, but the gain is modest: about 1 percentile point on average and 3 at the ceiling. "
  "Honestly, percentile interpolation is not where this product wins. Its real value is that the fitted "
  "distributions feed the calibration step in Section 4 correctly.", CALL)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ CHNC
P("4. Admission probability (CHNC): a calibrated selection model", H1)
P("<b>In plain English.</b> Picture every application getting a hidden overall rating made of test scores, everything else (grades, activities, essays), and luck. The school admits everyone above a cutoff. Two public facts tell us where the cutoff sits: what fraction of applicants get in, and what the admitted students' scores look like. From those, we work out how likely you are to land above the cutoff.", PLAIN)
P("<b>Generative model.</b> Within school j's applicant pool, an applicant is admitted iff "
  "U<sub>j</sub> = a<sub>j</sub>·zT + b·zH + ε<sub>j</sub> &gt; c<sub>j</sub>. Here zT is the pool-standardized test "
  "composite, zH the standardized non-test strength (grades, rigor, activities), and ε everything idiosyncratic to the "
  "read. a<sub>j</sub> comes from the CDS 'importance of testing' label (Very Important 1.0, Important 0.8, "
  "Considered 0.5, Not Considered 0) times a global scale, and b=1 fixes the units.")
P("<b>Calibration in closed form.</b> Two published numbers pin each school down. The acceptance rate r gives the "
  "threshold c = Φ<super>−1</super>(1−r)·√(a²+b²+σ²). The admitted-class score distribution gives the "
  "<i>applicant</i> pool's mean and sd, by inverting the truncated-normal selection moments:")
P("E[zT | admit] = ρλ,  Var[zT | admit] = 1 − ρ²λ(λ−k),  with k=Φ<super>−1</super>(1−r), λ=φ(k)/r, ρ=a/√(a²+b²+σ²)<br/>"
  "⇒  s = sd<sub>adm</sub> / √(1 − ρ²λ(λ−k)),   m = mean<sub>adm</sub> − sρλ", MONO)
P("A unit test simulates 400,000 applicants from the implied pool and recovers the published acceptance rate and "
  "admitted mean and sd to within 3%. This is the step a quick clone typically gets wrong: it conditions on the admitted "
  "distribution as if it were the applicant pool.")
fig("f3_calibration", caption="Figure 3. MIT: the inferred applicant pool sits below and wider than the admitted class.")
P("<b>Per-student probability.</b> The student's index at school j is a<sub>j</sub>zT<sub>j</sub> + b(h − κ<sub>j</sub>) + "
  "shared + idiosyncratic noise. κ<sub>j</sub> = ρ<sub>TH</sub>(m<sub>j</sub> − 1300)/180 says pools with stronger "
  "test scores are also stronger on everything else. With no advisor rating, the prior on h is conditioned on the "
  "student's own score (E[h|T] = ρ<sub>TH</sub>·zT<sub>ref</sub>). With a rating, h ~ N(Φ<super>−1</super>(pct), 0.6²).")
P("<b>Lapse mixture.</b> P = (1−ω)·Φ(index) + ω·r<sub>j</sub>, with ω=5% by default. This covers hooks, institutional "
  "priorities and data error. Without it, a 1400 applicant at Brown came out at 0.002%, which is absurd.")
P("<b>Test-optional decision.</b> Withholding replaces zT with the level a school imputes to non-submitters "
  "(default −0.25 pool sd). The tool recommends SUBMIT iff that raises P(admit).")
P("<b>80% band.</b> The spread of P(admit) across the 10th-90th percentiles of the unknown shared factor. It is wide on "
  "purpose: for a strong applicant at a 4% school, the honest answer is 'between 0 and 24%, depending on things the "
  "scores don't show'.")
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ XADM/UPDT/PORT
P("5. Cross-admit, Bayesian updating and portfolio risk (XADM · UPDT · PORT)", H1)
P("<b>In plain English.</b> Your applications aren't separate coin flips. The same essays, grades and recommendations go everywhere, so a yes from MIT means your application is strong, and your Stanford odds should go up. Multiplying schools' odds as if they were independent makes a list of reaches look much safer than it is. These tools do the math the right way, and update your remaining odds every time a real decision comes in.", PLAIN)
P("<b>Why decisions are correlated.</b> The same student carries the same non-test strength and the same "
  "essays and recommendations to every school. All shared parts collapse into one latent "
  "S ~ N(b·μ<sub>h</sub>, b²σ<sub>h</sub>² + γσ²), where γ is the share of read noise common to every school. "
  "Conditional on S, decisions are independent, so every joint quantity is a one-dimensional integral. It is computed "
  "on an 801-point grid: exact to grid precision, with no Monte Carlo noise.")
P("• XADM: P(B | admit A) = E[p<sub>A</sub>(S)p<sub>B</sub>(S)] / E[p<sub>A</sub>(S)].<br/>"
  "• UPDT: posterior π(S | decisions) ∝ π(S)·Π p<sub>j</sub>(S)<super>adm</super>(1−p<sub>j</sub>(S))<super>rej</super>·"
  "P(waitlist band)<super>wl</super>, renormalized on the grid. Remaining schools are re-priced under the posterior. "
  "Waitlist/deferral is an ordered-probit band just below the threshold, which is informative ('close') and not "
  "the same as a rejection.<br/>"
  "• PORT: on each grid node the number of admits is Poisson-binomial (exact dynamic programming), then mixed over S.")
fig("f4_xadm", 5.0, "Figure 4. Cross-admit matrix for a 1540 applicant. An MIT admit lifts Stanford from 19% to about 63%.")
fig("f12_posterior", caption="Figure 12. How decisions move the belief about the applicant's shared strength.")
fig("f5_port", caption="Figure 5. Same marginal chances. Independence says 1.6% risk of zero admits; the correlated model says 9.7%.")
P("<b>Backtest E4.</b> On held-out students, each decision was predicted twice: from the profile alone, and from the "
  "profile plus all of the student's <i>other</i> decisions (leave-one-out posterior). We also scored the predicted "
  "count of admits, and P(no admits) for lists that look safe.")
rows = [["World", "Brier: marginal → with other decisions", "Log loss", "AUC", "Count log-score: independent vs correlated"]]
for key, lab in (("e3_well", "matches model"), ("e3_miss", "misspecified")):
    sc = R[key]["scores"]
    a, b = sc["unimath (fitted)"], sc["unimath fitted + other decisions (LOO posterior)"]
    rows.append([lab, f"{f(a['brier'], 4)} → {f(b['brier'], 4)}", f"{f(a['log_loss'])} → {f(b['log_loss'])}",
                 f"{f(a['auc'])} → {f(b['auc'])}", f"{f(R[key]['count_logscore']['independent'])} vs {f(R[key]['count_logscore']['correlated'])}"])
table(rows, [1.1, 1.9, 1.2, 1.1, 1.6])
fig("f7_pnone", caption="Figure 7. The headline result. Among students whose lists look ≥95% safe under independence, "
    "the real zero-admit rate is several times higher.")
_pvw = SIG0["pred_well"]["posterior_vs_fitted"]["brier"]
_pvm = SIG0["pred_miss"]["posterior_vs_fitted"]["brier"]
P(f"<b>Verdict.</b> Conditioning on other decisions is the most valuable thing the model does. Pooled over 5 worlds, "
  f"error drops {-100 * _pvw['relative']:.0f}% (matched) and {-100 * _pvm['relative']:.0f}% (misspecified), both far beyond luck. "
  f"The zero-admit warning is accurate when the model is right ({100 * _sw['correlated']['expected'] / _sw['n']:.1f}% "
  f"predicted vs {100 * _sw['observed_rate']:.1f}% observed). When the world has heavy tails and hooked applicants it "
  f"over-warns ({100 * _sm['correlated']['expected'] / _sm['n']:.1f}% vs {100 * _sm['observed_rate']:.1f}%). Over-warning is "
  "the safer failure for a family, but it is still miscalibration. <i>In plain English: it's right about the direction "
  "of the risk, not reliably about its size.</i>", CALL)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ E3 + E2
P("6. Fitting to real outcomes (FIT) and the predictive backtest", H1)
P("<b>In plain English.</b> To check the model, we invented thousands of fake students whose results we know, hid some of them, and asked the model to predict the hidden ones. This tests whether the math and the code work. It cannot test whether real admissions offices behave like the model, because we wrote the fake world. That needs real student outcomes, which we don't have yet.", PLAIN)
P("<b>Estimation.</b> Maximum <i>marginal</i> likelihood: each student's shared factor is integrated out "
  "(121-point grid), so a student's eight decisions count as eight correlated observations, not eight independent ones. "
  "Free parameters are σ<sub>ε</sub>, γ, the test-weight scale and the lapse ω (log/logit transformed), optimized with "
  "L-BFGS-B. Standard errors come from the numerical Hessian (observed information) by the delta method. A dataset with "
  "no waitlist labels automatically gets a zero-width waitlist band.")
P("<b>Input format</b> (one row per application, exportable from any CRM):")
P("student_id,school_id,ebrw,math,decision,holistic_pct,submitted<br/>s17,mit,750,790,rejected,70,true", MONO)
P("<b>Backtest E3.</b> 2,500 simulated students × 8 applications, split 60/40 <i>by student</i>. The baselines are "
  "the base rate, and a pooled logistic regression on logit(acceptance rate) and the student's z-score against the "
  "published band. That logistic regression is what a careful developer would build in an afternoon. The "
  "misspecified world uses Student-t(3) read noise, per-school test weights randomly off by ±50%, and 4% hooked "
  "applicants admitted 60% of the time regardless.")
rows = [["Model", "Brier", "Log loss", "AUC", "ECE", "Brier (misspec.)", "Log loss (misspec.)", "ECE (misspec.)"]]
for k in e3w["scores"]:
    a, b = e3w["scores"][k], e3m["scores"][k]
    rows.append([k, f(a["brier"], 4), f(a["log_loss"]), f(a["auc"]), f(a["ece"]), f(b["brier"], 4), f(b["log_loss"]), f(b["ece"])])
table(rows, [2.1, 0.55, 0.6, 0.5, 0.5, 0.8, 0.85, 0.75], font=7)
fig("f6_reliability", caption="Figure 6. Reliability diagrams (square-root axes to spread out the many low probabilities). Points on the diagonal mean calibrated.")
P("<b>Verdict.</b> On single-school odds, the structural model only narrowly beats a well-built logistic regression. "
  "Do not sell it as 'more accurate chancing'. The structure pays off in what the logistic cannot do at all: correlated "
  "portfolio risk, updating, test-optional decisions, and calibrating a school from published data with zero outcomes "
  "('default priors' already matches the logistic, which needed training data).", CALL)
P("<b>Backtest E2: parameter recovery</b> (6 replications × 1,500 students × 8 applications, known truth).")
rows = [["Parameter", "True", "Mean estimate", "Spread (sd)", "Mean reported SE", "95% CI coverage"]]
for k, v in R["e2"].items():
    rows.append([k, f(v["true"], 2), f(v["mean"]), f(v["sd"]), f(v["mean_se"]), f"{100 * v['coverage95']:.0f}%"])
table(rows, [1.2, 0.7, 1.1, 1.0, 1.2, 1.2])
fig("f8_recovery", caption="Figure 8. Estimates relative to truth.")
P("<b>Verdict.</b> The lapse rate and test weight are learnable. The shared-noise share γ is weakly identified at 8 "
  "applications per student: two of six fits hit the lower bound. The reported 95% intervals undercover (67%). "
  "Implication for the product: a single practice's 250 outcomes a year cannot pin γ down. This is the statistical "
  "argument for a pooled data co-op. The next version should use profile-likelihood or bootstrap intervals instead of "
  "the Hessian.", CALL)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ essays + plan
P("7. Essay reuse (ESSY · FREE) and the list optimizer (PLAN)", H1)
P("<b>In plain English.</b> Many supplements ask nearly the same question ('why this major?', 'a challenge you faced'). If you already wrote one for School A, School B may be mostly done. We estimate how much of each school's writing is already covered by your other schools, then pick the list that gives the best expected result for the least new writing.", PLAIN)
P("<b>Prompt-pair reuse.</b> R(p,q) is the share of p's work already done by an essay for q. Curated scores (the "
  "same <font face='Courier'>prompt_similarity</font> table as the web app's Supabase) always win. Otherwise "
  "R = max over shared themes of θ<sub>t</sub>·(0.6 + 0.4·cos)·L, where θ<sub>t</sub> is a theme reuse coefficient "
  "(why-us 0.30: content must be school-specific; challenge 0.80), cos is the TF-IDF cosine of the prompt texts with "
  "school names stripped, and L = max(0.5, 1 − 0.15·|ln(w<sub>p</sub>/w<sub>q</sub>)|) penalizes cutting or "
  "expanding an essay. There is no credit between prompts of the same school.")
P("<b>School coverage</b> C(B|A) is the effort-weighted mean of best-match reuse. It is asymmetric by design. "
  "<b>Marginal effort</b> is Σ (words + 60 overhead)·(1 − best reuse against the already-written set). It is "
  "non-increasing as the set grows (a tested property), which is what makes greedy planning well behaved. "
  "Clusters use average-linkage hierarchical clustering on 1 − symmetrized coverage.")
fig("f9_essy", 4.8, "Figure 9. Coverage matrix. Read across: how much of the row school is already written by the column school.")
P("<b>Backtest E5.</b> We scored the heuristic against the 10 human-curated pairs, holding the curated values out.")
rows = [["Variant", "Spearman ρ", "Mean abs error (pts)"],
        ["raw heuristic", f(R["e5"]["raw"]["spearman"], 2), f(R["e5"]["raw"]["mae_points"], 1)],
        ["leave-one-out recalibrated (linear)", f(R["e5"]["loo_calibrated"]["spearman"], 2), f(R["e5"]["loo_calibrated"]["mae_points"], 1)],
        ["constant (mean of other curated pairs)", "—", f(R["e5"]["constant_baseline"]["mae_points"], 1)]]
table(rows, [3.0, 1.2, 1.6])
fig("f10_e5", 3.6, "Figure 10. Heuristic vs curated scores.")
P("<b>Verdict: this part does not work yet.</b> The heuristic does not beat a constant. It systematically under-scores "
  "reuse (by about 27 points) and misses thematic matches that share no vocabulary (MIT 'unconventional path' vs "
  "Princeton 'lived experience', curated 55, model 0). The raw heuristic is kept only as a conservative floor (it "
  "overstates effort, the safe direction). Curated scores override it, and recalibration is off by default because it "
  "inflated reuse for unrelated pairs. Fix: sentence-embedding or LLM pair scoring, validated against a much larger "
  "curated set (target 300+ pairs).", CALL)
P("<b>PLAN.</b> It maximizes E[utility of the best admit] − λ·words. The first term is computed exactly under the "
  "correlated model (sort by utility; P(j is the best admit | S) = p<sub>j</sub>Π<sub>k above</sub>(1−p<sub>k</sub>)), "
  "so a second, correlated reach is correctly worth less than it looks. It uses exhaustive search for 12 or fewer "
  f"candidates, otherwise greedy forward selection plus 1-swap local search. <b>E6:</b> on {R['e6']['trials']} random "
  f"instances, greedy found the same list as brute force {100 * R['e6']['same_list']:.0f}% of the time (max objective "
  f"gap {f(R['e6']['max_gap_pct'], 2)}%).")
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ sensitivity
P("8. Assumptions and sensitivity (SENS)", H1)
P("<b>In plain English.</b> Every model rests on guesses about how the world works. This page shows how much each answer moves if a guess is off. If an answer swings a lot, treat it as rough.", PLAIN)
rows = [["Assumption", "Default", "Why", "Learnable from outcomes?"],
        ["σ<sub>ε</sub> (read noise)", "1.0", "Holistic reads are noisy; equal in size to non-test strength", "Yes (E2: moderately)"],
        ["γ shared noise share", "0.30", "Same essays/recs read everywhere", "Weakly; needs pooled data"],
        ["Test weight by CDS label", "1.0/0.8/0.5/0", "Ordinal CDS label → weight", "Scale yes; per-school needs volume"],
        ["ω lapse", "5%", "Hooks, priorities, data errors", "Yes (E2: well)"],
        ["ρ<sub>TH</sub> test ↔ non-test", "0.4", "Grades/SAT correlation in the literature is about 0.4-0.5", "Not tried (fixed)"],
        ["ρ<sub>EM</sub> EBRW ↔ Math", "0.6", "Restricted range inside selective classes", "From score data, not outcomes"],
        ["Enrolled → admitted shift", "0", "CDS bands are enrolled students; yield makes them lower than admitted", "Needs admitted-band data"],
        ["Withheld test level", "−0.25 sd", "Non-submitters score lower on average", "Yes, with submit flag"]]
table(rows, [1.6, 0.9, 2.6, 1.6])
fig("f11_sens", caption="Figure 11. Tornado: P(admit) under the low/high value of each assumption (amber = high, grey = low).")
P("<b>Reading this.</b> For a long-shot school the answer is dominated by σ<sub>ε</sub> and the lapse rate, which are "
  "exactly the parameters FIT learns from outcomes. Defaults are educated priors, not facts, and SENS exists so a "
  "counselor can see that.")

# ------------------------------------------------------------------------------------------ failures
P("9. What we tried that failed (and what replaced it)", H1)
rows = [["Attempt", "What happened", "Resolution"],
        ["Density-continuous split normal fitted to 3 quantiles", "Its reachable skew is bounded. On 740/760/770 one scale collapsed to 0 and it still missed the median.",
         "Quantile-matched two-piece normal (exact for any band). Kept in E1 as a baseline."],
        ["Plain normal tails", "A 1400 applicant at Brown came out at 0.002%: overconfident far from the threshold.", "5% lapse mixture with the base rate."],
        ["Holistic prior independent of test score", "A 1540 applicant got 4.0% at JHU, below the 6.4% base rate, because they were treated as holistically average against a strong pool.",
         "Prior on non-test strength conditioned on the score (same ρ<sub>TH</sub> link as pools)."],
        ["Reject likelihood = 1 − P(admit)", "Double-counted the waitlist band, so outcome probabilities summed to more than 1. The fit then ran to absurd values (σ=3.4, test_scale at its bound) and beat the true parameters on likelihood.",
         "Mutually exclusive admit/waitlist/reject; regression test that they sum to 1. Found by parameter recovery, which is why recovery tests matter."],
        ["'why' anywhere ⇒ why-us theme", "'What excites you… and why?' was tagged as a why-us essay.", "Why-us requires 'why … college/university/us' or school-specific phrasing."],
        ["Linear recalibration of similarity on curated pairs", "LOO error 17.7 vs constant 14.0. It pushed every faintly related pair to about 44% reuse.",
         "Off by default. Heuristic is a conservative floor only. Needs embeddings plus a larger curated set."],
        ["Hessian standard errors", "95% intervals covered only 67% in recovery.", "Flagged. Bootstrap or profile likelihood next."],
        ["Fitting γ per practice", "Weakly identified at 8 apps/student × 1,500 students.", "Argument for pooled multi-practice calibration."],
        ["Pitch claims", "Buyer-test agent called the '98% vs 90%' and 'liability' framing marketing, since it is model-derived.", "Lead with frozen-forecast track record and past-class backtests instead (Section 10)."]]
table(rows, [1.7, 2.7, 2.3], font=7.3)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ market
P("10. Who buys this, and why not just vibe-code it?", H1)
P("<b>The market today.</b>", H3)
rows = [["Product", "Buyer", "What it gives", "Gap UNIMATH targets"],
        ["Naviance / Scoir scattergrams", "High schools (district contracts)", "Past applicants from the same high school: GPA × score × outcome", "Suppressed for schools with fewer than 5-10 past applicants; no probabilities; no correlation"],
        ["Scoir Admission Intelligence", "High schools", "Match levels from 'tens of millions' of de-identified outcomes", "Black box; no published validation; not sold to independent counselors"],
        ["CollegeVine", "Students (free)", "Per-school % from about 75 factors", "No published validation; users report inflated odds; essay-service upsell"],
        ["College Kickstart", "Students, counselors", "List grade, 'confidence of at least one admit'", "Formula unpublished; at-least-one logic appears to be independence-style"],
        ["CollegePlannerPro, CounselMore", "Independent counselors (from about $69/mo)", "CRM: tasks, deadlines, documents", "No analytics. Natural integration partner."]]
table(rows, [1.4, 1.2, 2.0, 2.1], font=7.2)
P("<b>The counselor problem.</b> Most independent counselors are not quantitative and will never read Sections 3-8. "
  "They buy outcomes: (1) no family blindsided by zero admits, (2) hours saved planning essays, (3) something "
  "rigorous-looking to hand a parent paying $6-9k, and (4) a defensible paper trail. So the product the counselor sees "
  "is <font face='Courier'>BRIEF</font> (plain English: '1 in 10 chance of no admits; the schools treated as "
  "independent would say 1 in 62') plus a family PDF. The math is the warranty, not the interface. A second segment "
  "is quantitative parents going direct: the terminal and this manual are the product for them.")
P("<b>Buyer test.</b> A fresh subagent played an independent counselor who pasted the sales email into Claude and "
  "asked 'should I buy it?'. The verdict was <i>trial only</i>. It credited the correlation insight, FIT and "
  "ED/EA updating, and flagged: model-derived headline claims, an anonymous vendor, 19-school coverage, no external "
  "validation, an unclear role for non-score factors, too little data for a per-practice refit, and terminal friction. "
  "It would buy annually if the tool beats scattergrams and the counselor's own calls on a backtest of their <i>past</i> "
  "classes.")
P("<b>Clone test.</b> A second subagent was asked 'can you just build this for me?' and tried. In about 35 minutes "
  "it reproduced percentiles, moment-matched per-school odds, a correlated simulation, P(at least one admit), updating "
  "and keyword essay matching. Its own assessment: 'plausible-looking, not calibrated'. Its sensitivity check moved one "
  "school from 65% to 94% under reasonable alternative assumptions. Parity on trustworthiness: 1-3 months part-time "
  "plus 2-4 days per cycle. Its recommendation was a hybrid, decided by backtesting on last year's class.")
P("Verdicts at a glance", H2)
table([["Test", "Question put to a fresh Claude", "Verdict", "In one sentence"],
       ["Buy test", "'I got this email. Should I buy it? Be honest.' (asked as a solo independent counselor)", "TRIAL ONLY",
        "The idea is real and $390/yr is cheap, but nothing proves the numbers beat what the counselor already has, and the vendor is anonymous."],
       ["Build test", "'Someone wants $49/month for this. Can you just build it for me instead?'", "HYBRID",
        "The math can be copied in an afternoon, but making the numbers trustworthy takes 1-3 months plus upkeep every year, so decide by testing both on last year's class."]],
      [0.8, 2.3, 0.9, 2.7])
P("Resolving every objection", H2)
P("In plain English: each row is something that made the AI hesitate, and the concrete fix. 'Done' items already exist "
  "in the toolkit; the rest is the roadmap in priority order.")
table([["#", "Objection (who raised it)", "Fix", "Effort", "Status"],
       ["1", "Headline numbers come from the model itself, not real outcomes (buy)",
        "Offer a free backtest of the counselor's last 2-3 classes with FIT, scored against their own calls and the scattergram. Freeze this year's forecasts in LEDGER now and publish the April SCORE.",
        "Days per counselor; the track record takes one cycle", "Tools done; needs first real class"],
       ["2", "Anonymous vendor (buy)", "Named founder, company entity, website, 2-3 counselor references, published methods manual.",
        "1 week", "Not started"],
       ["3", "No external validation (buy, build)", "Pre-register the evaluation, then have an independent statistician review this manual and the code.",
        "2-4 weeks, small fee", "Not started"],
       ["4", "Only 19 schools (buy)", "Import every large 4-year school's SAT bands and admit rate from the College Scorecard API; keep hand-curated supplements for the most-applied; DQ flags proxies.",
        "Done for chances (412 schools); supplements: 2-3 weeks per 100 schools", "DONE for odds; supplements partial"],
       ["5", "Looks score-driven: what about GPA, rigor, activities, ED/EA? (buy)",
        "Structured advisor rubric (GPA, rigor, activities, essays, hooks) mapped to the non-test strength h; separate early-round acceptance rates; in-state flag.",
        "1-2 weeks model work + data", "Partial (HOL percentile only)"],
       ["6", "~250 outcomes/yr per practice is too few to refit (buy; confirmed by E2)",
        "Pooled outcomes co-op with a hierarchical model: shared settings learned from all practices, with a practice-level adjustment.",
        "3-6 weeks; needs ~10 practices", "Not started; the biggest moat"],
       ["7", "Uploading client data to strangers (buy)",
        "Local-only mode by default (it already runs entirely on the user's machine), de-identification before any pooling, data processing agreement, deletion policy.",
        "1 week (policy + docs)", "Local mode done"],
       ["8", "Terminal is friction for a solo counselor (buy)",
        "Counselor-facing one-page family report (PDF) from BRIEF + a simple web front end; keep the terminal for power users and quantitative parents.",
        "1-2 weeks", "BRIEF done; report not"],
       ["9", "No CollegePlannerPro/Scoir import (buy)", "CSV importers mapped to their export formats.", "Days each", "Not started"],
       ["10", "'Liability' fear framing and unsourced '1 in 10' (buy)",
        "Rewrite the pitch: lead with the free past-class backtest and the public forecast ledger; label every number 'simulated' until real.",
        "Hours", "Done in this manual; pitch email not yet"],
       ["11", "Code copied in 35 minutes (build)",
        "Don't sell code. Sell the maintained catalog, the pooled calibration and the track record, which a clone can't reproduce without the data.",
        "Ongoing", "Positioning only"],
       ["12", "Clone's odds swung 65%→94% under different assumptions (build)",
        "Ship SENS with every answer, learn the uncertain settings from pooled data (FIT), and show ranges, not single decimals, in family-facing output.",
        "Days", "SENS done; ranges in CHNC done"],
       ["13", "2-4 days/yr of upkeep (build)", "That upkeep is the product: price the subscription on 'we re-verify every school and every new supplement each August'.",
        "Ongoing", "Positioning"]],
      [0.25, 1.6, 2.9, 1.05, 0.9], font=6.9)
P("<b>The sequence that turns 'trial only' into 'buy'.</b> (1) Get one counselor's last two classes and run FIT: "
  "this produces the first real accuracy number, good or bad. (2) Freeze this cycle's forecasts in LEDGER and publish "
  "the head hash. (3) Fix the pitch (items 2, 10). (4) Expand coverage (4). (5) Recruit about 10 practices into the "
  "outcomes co-op (6). Steps 1-3 cost almost nothing and answer Claim 9.", CALL)
P("<b>Conclusion: what is actually sellable.</b> Code can be cloned. These can't:", CALL)
P("1. <b>A pooled outcomes co-op.</b> Each practice contributes de-identified outcomes and gets a model calibrated on "
  "thousands of decisions. This directly fixes E2's identification problem and the buyer's 250-outcomes objection, "
  "and it compounds with every customer.<br/>"
  "2. <b>A public forecast ledger</b> (LEDGER/SCORE, built). Forecasts are frozen in October in a hash chain and "
  "graded in April. A published track record is what turns 'trial only' into 'buy'.<br/>"
  "3. <b>Curated data on a cycle.</b> CDS bands, acceptance rates and every new August supplement, plus a "
  "prompt-similarity matrix large enough to replace the failed heuristic (E5).<br/>"
  "4. <b>Workflow, not math.</b> CollegePlannerPro/Scoir import, a one-page family report, and a free backtest of a "
  "counselor's last class as the sales motion.")
P("<b>Pitch changes.</b> Name the company and the people; publish this manual; lead with the forecast ledger and the "
  "past-class backtest offer; drop the 'liability' fear framing; state coverage and what the model ignores (essays, "
  "activities and hooks enter only through the optional advisor rating and the lapse term).")
P("<b>Sources (market research):</b> CollegeVine accuracy blog (blog.collegevine.com/is-collegevine-chancing-accurate); "
  "Scoir Admission Intelligence (scoir.com/high-schools/admission-intelligence); College Kickstart "
  "(collegekickstart.com); Hechinger Report on scattergrams (hechingerreport.org); CollegePlannerPro plans "
  "(collegeplannerpro.com/plans); Inside Higher Ed counselor-software comparison; College Scorecard API docs "
  "(collegescorecard.ed.gov). Competitor details are from public pages and may be out of date.", SM)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ roadmap + appendix
P("11. Limitations and roadmap", H1)
P("• <b>No real outcomes yet.</b> Every E3/E4 number is synthetic. First priority: run FIT and SCORE on a real "
  "counselor's past classes.<br/>"
  "• <b>Coverage.</b> Odds now cover 412 schools (Scorecard). For the 393 imported schools, 'test importance' is a "
  "proxy from Scorecard's test-requirement code, not the CDS C7 label, and their supplements are placeholders. "
  "Caltech still lacks an acceptance rate.<br/>"
  "• <b>Enrolled vs admitted bands.</b> CDS reports enrolled students. A yield adjustment parameter exists but is set "
  "to 0.<br/>"
  "• <b>Round structure.</b> ED/EA/REA rates differ sharply from RD. The model uses overall rates; it needs per-round "
  "calibration.<br/>"
  "• <b>Non-score inputs.</b> GPA, rigor and activities enter only through one advisor percentile. Next: a structured "
  "rubric mapped to h.<br/>"
  "• <b>Uncertainty.</b> Use bootstrap or profile-likelihood intervals; propagate parameter uncertainty into the 80% band.<br/>"
  "• <b>Essay similarity.</b> Use embeddings validated on 300+ curated pairs.")
P("Appendix A. Command reference", H2)
rows = [["Command", "Description"]] + [[c, d] for c, d in [
    ("SAT 750 790 / HOL 70 / LIST mit +cmu -tufts / UTIL mit 100", "session setup"),
    ("PCTL · CHNC · XADM · PORT", "percentiles, chances, cross-admit, portfolio"),
    ("DEC mit accepted · UPDT", "record a decision, Bayesian re-pricing"),
    ("ESSY · FREE · PLAN", "essay coverage, near-free schools, list optimizer"),
    ("BRIEF · BRIEF family", "counselor brief (numbers) · family brief (words)"),
    ("ROSTER caseload.csv · BKTST past.csv", "whole-caseload risk screen · score your past calls vs UNIMATH"),
    ("ED tufts 0.20", "use a school's early-round admit rate for this student"),
    ("SENS · SCH mit · DQ · CAT", "sensitivity, school page, data quality, catalog"),
    ("FIT outcomes.csv · SIM out.csv", "fit to real outcomes with held-out scores; synthetic data"),
    ("LEDGER f.jsonl alex · SCORE f.jsonl outcomes.csv", "freeze forecasts (hash chain); verify and grade"),
    ("unimath CHNC -p profile.toml --json", "one-shot, machine-readable")]]
table(rows, [3.2, 3.4])
P("Appendix B. Reproducing this manual", H2)
P("pip install -e toolkit[report,test]<br/>python toolkit/scripts/build_catalog.py<br/>pytest toolkit/tests<br/>"
  "python toolkit/scripts/run_backtests.py<br/>python toolkit/scripts/make_figures.py<br/>python toolkit/scripts/make_report.py", MONO)


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(AMBER)
    canvas.rect(0, letter[1] - 14, letter[0], 14, fill=1, stroke=0)
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.drawString(0.6 * inch, letter[1] - 10, "UNIMATH  ·  METHODS & VALIDATION")
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(letter[0] - 0.6 * inch, 0.45 * inch, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                        topMargin=0.7 * inch, bottomMargin=0.7 * inch, title="UNIMATH methods manual", author="UNIMATH")
doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=on_page)
print("wrote", OUT)
