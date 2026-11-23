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
P("Version 0.1 &nbsp;·&nbsp; November 2026 &nbsp;·&nbsp; catalog: 19 schools (13 fully modellable), 71 supplement prompts", SM)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ exec summary
P("1. Executive summary", H1)
P(f"<b>What it is.</b> A terminal (Bloomberg-style function codes) and Python library that turns published admissions "
  "data into calibrated, correlated admission probabilities, a Bayesian update as decisions arrive, essay-reuse "
  "planning, and a list optimizer. There is also a plain-English 'family brief' for counselors who don't want the math.")
P("<b>The one result that matters.</b> Every mainstream list-balancing tool treats schools as independent and multiplies "
  f"probabilities. In the backtest, take students whose lists looked at least 95% safe under that formula. "
  f"<b>{pw[3]:.1f}% of them actually got zero admits</b>. The independence formula predicted {pw[1]:.1f}%; "
  f"UNIMATH's correlated model predicted {pw[2]:.1f}% (Figure 7). Under a deliberately misspecified world, "
  f"the zero-admit rate was {pm[3]:.1f}%. UNIMATH predicted {pm[2]:.1f}% (too pessimistic) and independence "
  f"predicted {pm[1]:.1f}% (far too optimistic).", CALL)
rows = [["Claim", "Verdict", "Evidence"],
        ["Score percentiles beat the bell curve through the IQR", "Yes, modestly",
         f"E1: {f(R['e1']['mae']['two-piece quantile-matched'], 2)} vs {f(R['e1']['mae']['normal-IQR (web app)'], 2)} "
         "percentile-point mean error on known truth"],
        ["Per-school chances beat a sensible logistic baseline", "Slightly",
         f"E3: Brier {f(e3w['scores']['unimath (fitted)']['brier'], 4)} vs {f(e3w['scores']['logistic on z-score']['brier'], 4)} "
         f"(matched world); {f(e3m['scores']['unimath (fitted)']['brier'], 4)} vs {f(e3m['scores']['logistic on z-score']['brier'], 4)} (misspecified)"],
        ["Bayesian update from other decisions adds real information", "Yes, clearly",
         f"E4: Brier {f(e3w['scores']['unimath (fitted)']['brier'], 4)} → "
         f"{f(e3w['scores']['unimath fitted + other decisions (LOO posterior)']['brier'], 4)}; AUC "
         f"{f(e3w['scores']['unimath (fitted)']['auc'])} → {f(e3w['scores']['unimath fitted + other decisions (LOO posterior)']['auc'])}"],
        ["Risk of zero admits is calibrated", "Yes if model is right; overstated if not", "Figure 7"],
        ["Model parameters can be learned from outcomes", "Partly",
         "E2: lapse and test weight recovered; shared-noise share weakly identified; 95% CIs cover only "
         f"{100 * R['e2']['sigma_eps']['coverage95']:.0f}%"],
        ["Essay similarity heuristic matches human curation", "No",
         f"E5: MAE {f(R['e5']['raw']['mae_points'], 1)} pts, worse than a constant ({f(R['e5']['constant_baseline']['mae_points'], 1)})"],
        ["List optimizer finds the best list", "Yes", f"E6: greedy = brute-force optimum in {100 * R['e6']['same_list']:.0f}% of {R['e6']['trials']} trials"],
        ["Validated on real student outcomes", "NOT YET", "No outcome data was available. The harness (FIT, LEDGER/SCORE) is ready."]]
table(rows, [2.2, 1.25, 3.25])
P("<b>The honest bottom line.</b> The math is sound and tested, and the core insight (correlated decisions) is real and "
  "under-served by competitors. But the code is not a moat: a subagent rebuilt the core in about 35 minutes (Section 10). "
  "What is defensible is (a) outcome data pooled across many counselors, which calibrates the model; (b) a curated, "
  "per-cycle catalog and prompt matrix; and (c) a public, tamper-evident forecast track record. Every validation "
  "number in this manual is synthetic until real outcomes are loaded.")
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
        ["BRIEF", "Plain-English paragraph for a family email", "Templated summary of the above", "n/a"],
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
P(f"<b>Verdict.</b> Conditioning on other decisions is the most valuable thing the model does: about a 20% Brier "
  f"improvement in both worlds. The zero-admit warning is accurate when the model is right ({pw[2]:.1f}% predicted vs "
  f"{pw[3]:.1f}% observed). When the world has heavy tails and hooked applicants, it over-warns ({pm[2]:.1f}% vs "
  f"{pm[3]:.1f}%): the fit absorbed the hooked students by inflating shared variance. Over-warning is the safer failure "
  "for a family, but it is still miscalibration, and real outcome data is needed to settle γ.", CALL)
story.append(PageBreak())

# ------------------------------------------------------------------------------------------ E3 + E2
P("6. Fitting to real outcomes (FIT) and the predictive backtest", H1)
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
  "• <b>Coverage.</b> 19 schools, 6 missing acceptance rates (DQ flags them). Target the 150-300 most-applied schools "
  "from CDS and IPEDS/College Scorecard.<br/>"
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
    ("BRIEF", "plain-English family brief"),
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
