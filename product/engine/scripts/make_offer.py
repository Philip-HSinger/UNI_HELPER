"""Build product/reports/calliper-feature-build-spec-v1.pdf (internal, for the developer): the three features being sold, how
each is calculated, what exists in the code, and the build spec for what's missing.

    python scripts/make_offer.py

All example numbers are computed live from the toolkit on the example student (examples/profile.toml).
"""
import sys
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import inch  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,  # noqa: E402
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from unimath.catalog import SIMILARITY, load_catalog  # noqa: E402
from unimath.model import AdmissionModel, Student  # noqa: E402
from unimath.similarity import SimilarityEngine  # noqa: E402

FIG = ROOT / "results" / "figures" / "offer"
FIG.mkdir(parents=True, exist_ok=True)
OUT = ROOT.parent / "reports" / "calliper-feature-build-spec-v1.pdf"

# ------------------------------------------------------------------------------------------------ numbers
CAT = load_catalog()
M = AdmissionModel(CAT)
E = SimilarityEngine(CAT, SIMILARITY)
ST = Student(750, 790)
LIST = ["mit", "stanford", "princeton", "cmu", "cornell", "georgia-tech", "tufts", "northeastern", "purdue"]
UTIL = {"mit": 100, "stanford": 98, "princeton": 95, "cmu": 90, "cornell": 85, "georgia-tech": 80, "tufts": 72,
        "northeastern": 70, "purdue": 60}
FALLBACK = 40
NAME = {"mit": "MIT", "stanford": "Stanford", "princeton": "Princeton", "cmu": "CMU", "cornell": "Cornell",
        "georgia-tech": "Georgia Tech", "tufts": "Tufts", "northeastern": "Northeastern", "purdue": "Purdue",
        "harvard": "Harvard", "yale": "Yale", "columbia": "Columbia", "upenn": "Penn", "brown": "Brown",
        "north-western": "Northwestern", "john": "Johns Hopkins", "usc": "USC", "boston-university": "Boston U"}
CANDS = {"harvard": 99, "yale": 96, "columbia": 92, "upenn": 92, "brown": 88, "north-western": 88, "john": 87,
         "usc": 75, "boston-university": 65}

p_none = M.count_distribution(ST, LIST)[0]
p_lo, _, p_hi = M.p_none_range(ST, LIST)
p_indep = float(np.prod(1 - M.chances(ST, LIST)))
words_list = E.list_effort(LIST)
words_alone = sum(E.standalone_effort(s) for s in LIST)
best0 = M.expected_best(ST, LIST, UTIL, FALLBACK)

cand_rows = []
for c, u in CANDS.items():
    alone = E.standalone_effort(c)
    marg, det = E.marginal_effort(c, LIST)
    gain = M.expected_best(ST, LIST + [c], {**UTIL, c: u}, FALLBACK) - best0
    src = max(det, key=lambda d: d[1])
    cand_rows.append(dict(id=c, util=u, alone=alone, marg=marg, covered=1 - marg / alone, p=M.chances(ST, [c])[0],
                          gain=gain, per100=100 * gain / marg, src=E.prompts[src[2]].school if src[2] is not None else None))
cand_rows.sort(key=lambda r: -r["per100"])

UPD = [s for s in LIST if s != "cmu"]
before = M.chances(ST, UPD)
after1 = M.chances(ST, UPD, {"cmu": "accepted"})
after2 = M.chances(ST, UPD, {"cmu": "accepted", "mit": "rejected"})

hm, hs = M.holistic_prior(ST)
gammas = np.linspace(0.02, 0.6, 15)
sens = {}
for label, sd in (("unknown", hs), ("rated", 0.5 * hs)):
    s2 = replace(ST, holistic_mean=hm, holistic_sd=sd)
    lift = []
    for g in gammas:
        m = M.with_params(shared_fit=float(g))
        lift.append(100 * (m.chances(s2, ["stanford"], {"cmu": "accepted"})[0] - m.chances(s2, ["stanford"])[0]))
    sens[label] = np.array(lift)

ESSAY_IDS = [s for s in LIST if E.standalone_effort(s) > 0]
COV = E.coverage_matrix(ESSAY_IDS)
REAL = [x["id"] for x in CAT if x["prompts"] and not any(p.get("placeholder") for p in x["prompts"])]
N_REAL_PROMPTS = sum(len(E.by_school[s]) for s in REAL)
N_CURATED = len(E.curated)


def writing_plan(eng, sids):
    """Greedy order used by SimilarityEngine.list_effort, but recording each step (to move into similarity.py)."""
    remaining, written, steps = list(sids), [], []
    while remaining:
        nxt = max(remaining, key=eng.standalone_effort) if not written else \
            min(remaining, key=lambda s: eng.marginal_effort(s, written)[0])
        cost, det = eng.marginal_effort(nxt, written) if written else (eng.standalone_effort(nxt), [
            (i, 0.0, None) for i in eng.by_school[nxt]])
        steps.append((nxt, cost, det))
        written.append(nxt)
        remaining.remove(nxt)
    return steps


PLAN_STEPS = writing_plan(E, LIST)
CMU_DET = E.marginal_effort("cmu", [s for s in LIST if s != "cmu"])[1]

# ------------------------------------------------------------------------------------------------ figures
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 10, "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlelocation": "left"})


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# 1. architecture: two engines -> three features
fig, ax = plt.subplots(figsize=(8.6, 3.7))
ax.set_xlim(-0.05, 10.25)
ax.set_ylim(-0.25, 4.7)
ax.axis("off")


def box(x, y, w, h, title, sub, edge, fill):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fill, ec=edge, lw=1.2))
    ax.text(x + w / 2, y + h - 0.2, title, ha="center", va="top", fontsize=8.6, fontweight="bold", color=INK)
    ax.text(x + w / 2, y + h - 0.55, sub, ha="center", va="top", fontsize=7, color=INK2, linespacing=1.3)


box(0.0, 2.45, 2.2, 2.0, "Inputs", "published SAT bands\nand admit rates\ncounselor's 0-100 read\nthis cycle's prompts",
    MUTED, "#f6f6f4")
box(2.9, 2.85, 3.3, 1.6, "Engine A: admissions model", "odds per school, linked\nby one shared hidden\n"
    "'application strength'", S1, "#eef4fc")
box(2.9, 0.2, 3.3, 2.05, "Engine B: essay matrix", "every prompt scored against\nevery other prompt:\n"
    "how much of an essay for q\ncan be reused for p", S2, "#fdf0ea")
box(7.0, 3.35, 3.2, 1.1, "Decision updates", "re-price the list after\neach real decision", S1, "white")
box(7.0, 1.9, 3.2, 1.15, "List check", "zero-admit risk + which\nschools are cheap to add", INK2, "white")
box(7.0, 0.2, 3.2, 1.4, "Essay map", "write-once plan: what covers\nwhat, words left, order", S2, "white")
for (x0, y0, x1, y1, c) in [(2.2, 3.6, 2.9, 3.65, MUTED), (2.2, 2.75, 2.9, 1.5, MUTED), (6.2, 3.85, 7.0, 3.9, S1),
                            (6.2, 3.2, 7.0, 2.6, S1), (6.2, 1.55, 7.0, 2.25, S2), (6.2, 0.95, 7.0, 0.9, S2)]:
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=10, color=c, lw=1.1))
ax.text(0.0, -0.2, "Built: Engine A, Decision updates, the risk half of List check.  Not built: Engine B, so Essay map "
        "and the 'cheap to add' half of List check run on a placeholder.", fontsize=6.8, color=INK2)
save(fig, "o1_architecture")

# 2. coverage heatmap (illustrative)
fig, ax = plt.subplots(figsize=(6.4, 4.3))
lab = [NAME[s] for s in ESSAY_IDS]
show = COV.copy()
np.fill_diagonal(show, np.nan)
cmap = matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#f4f8fd", "#9ec5f4", "#2a78d6", "#104281"])
cmap.set_bad("#efefec")
im = ax.imshow(100 * show, cmap=cmap, vmin=0, vmax=60)
for i in range(len(lab)):
    for j in range(len(lab)):
        if i == j:
            ax.text(j, i, "-", ha="center", va="center", fontsize=7, color=MUTED)
        else:
            v = 100 * COV[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7.2, color="white" if v > 35 else INK)
ax.set_xticks(range(len(lab)), lab, rotation=35, ha="right")
ax.set_yticks(range(len(lab)), lab)
ax.set_xlabel("...by essays already written for this school")
ax.set_ylabel("Share of this school's supplement (%)...")
for s in ax.spines.values():
    s.set_visible(False)
ax.tick_params(length=0)
cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cb.outline.set_visible(False)
cb.set_label("% covered", color=INK2)
ax.set_title("Essay map, one student: how much of each row is already written by each column")
save(fig, "o2_coverage")

# 3. list check: words vs value
fig, ax = plt.subplots(figsize=(6.6, 3.9))
xs = [r["marg"] for r in cand_rows]
ys = [r["gain"] for r in cand_rows]
ax.grid(True, color=GRID, lw=0.6)
ax.set_axisbelow(True)
# hand-placed label offsets (points) so neighbouring schools don't collide
OFF = {"usc": (8, -3), "north-western": (-8, 6), "brown": (-6, 7), "columbia": (6, 6), "yale": (6, -3),
       "upenn": (6, -10), "harvard": (6, 4), "john": (-6, 7), "boston-university": (6, -11)}
for r in cand_rows:
    top = r is cand_rows[0]
    ax.scatter(r["marg"], r["gain"], s=46, color=S2 if top else S1, edgecolor="white", lw=1.5, zorder=3)
    dx, dy = OFF.get(r["id"], (7, -3))
    ax.annotate(NAME[r["id"]], (r["marg"], r["gain"]), xytext=(dx, dy), textcoords="offset points", fontsize=7.6,
                ha="left" if dx > 0 else "right", color=INK if top else INK2)
ax.set_xlim(0, max(xs) * 1.2)
ax.set_ylim(0, max(ys) * 1.15)
ax.set_xlabel("New words still to write if added to this list")
ax.set_ylabel("Gain in value of best admit (points)")
ax.set_title("List check: what each extra school costs in writing vs what it adds")
save(fig, "o3_listcheck")

# 4. decision updates dumbbell
fig, ax = plt.subplots(figsize=(6.6, 3.8))
order = np.argsort(before)
yl = [NAME[UPD[i]] for i in order]
for k, i in enumerate(order):
    ax.plot([100 * before[i], 100 * after1[i]], [k, k], color=GRID, lw=2, zorder=1)
    ax.scatter(100 * before[i], k, s=40, color=MUTED, zorder=3, edgecolor="white", lw=1.5)
    ax.scatter(100 * after1[i], k, s=40, color=S1, zorder=3, edgecolor="white", lw=1.5)
    if UPD[i] != "mit":
        ax.scatter(100 * after2[i], k, s=40, color=S2, zorder=4, edgecolor="white", lw=1.5, marker="D")
ax.set_yticks(range(len(yl)), yl)
ax.set_xlim(0, 100)
ax.set_xlabel("Chance of admission (%)")
ax.grid(True, axis="x", color=GRID, lw=0.6)
ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0)
ax.scatter([], [], color=MUTED, s=40, label="before any decision")
ax.scatter([], [], color=S1, s=40, label="after CMU admits")
ax.scatter([], [], color=S2, s=40, marker="D", label="after CMU admits and MIT rejects")
ax.legend(loc="lower right", frameon=False, fontsize=7.6)
ax.set_title("Decision updates: one student's list re-priced as results arrive")
save(fig, "o4_updates")

# 5. sensitivity of the jump
fig, ax = plt.subplots(figsize=(6.4, 3.3))
ax.grid(True, color=GRID, lw=0.6)
ax.set_axisbelow(True)
ax.plot(gammas, sens["unknown"], color=S1, lw=2)
ax.plot(gammas, sens["rated"], color=S2, lw=2)
ax.text(gammas[-1] + 0.01, sens["unknown"][-1], "counselor gives\nno rating", color=INK2, fontsize=7.4, va="center")
ax.text(gammas[-1] + 0.01, sens["rated"][-1], "counselor rates\nthe student", color=INK2, fontsize=7.4, va="center")
ax.axvline(0.3, color=MUTED, lw=0.8, ls="--")
ax.text(0.305, ax.get_ylim()[1] * 0.04 + 1, "today's default", fontsize=7, color=MUTED)
ax.set_xlim(0, 0.75)
ax.set_ylim(0, None)
ax.set_xlabel("How strongly schools agree about the same application (link strength, unmeasured)")
ax.set_ylabel("Rise in Stanford odds after a\nCMU admit (percentage points)")
ax.set_title("The size of an update depends on two numbers we haven't measured yet")
save(fig, "o5_sensitivity")

# ------------------------------------------------------------------------------------------------ PDF
from reportlab.lib.fonts import addMapping  # noqa: E402
from reportlab.platypus import Preformatted  # noqa: E402

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVM", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
addMapping("DV", 0, 0, "DV")
addMapping("DV", 1, 0, "DVB")
addMapping("DV", 0, 1, "DV")
addMapping("DV", 1, 1, "DVB")

C_INK = colors.HexColor(INK)
C_BLUE = colors.HexColor(S1)
C_ORANGE = colors.HexColor(S2)
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="DVB", fontSize=15, textColor=C_INK, spaceBefore=4, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="DVB", fontSize=11.5, textColor=C_BLUE, spaceBefore=10, spaceAfter=4)
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontName="DVB", fontSize=9.5, textColor=C_INK, spaceBefore=7, spaceAfter=3)
B = ParagraphStyle("B", parent=ss["BodyText"], fontName="DV", fontSize=8.7, leading=12.4, spaceAfter=5)
SM = ParagraphStyle("SM", parent=B, fontSize=7.4, leading=10, textColor=colors.HexColor(INK2))
BUL = ParagraphStyle("BUL", parent=B, leftIndent=12, bulletIndent=3, spaceAfter=2.5)
MATH = ParagraphStyle("MATH", parent=B, backColor=colors.HexColor("#f4f4f2"), borderPadding=6, spaceBefore=3,
                      spaceAfter=9, fontSize=8.3, leading=12.4)
PLAIN = ParagraphStyle("PL", parent=B, backColor=colors.HexColor("#eef4fc"), borderPadding=6, borderColor=C_BLUE,
                       borderWidth=0.6, spaceBefore=2, spaceAfter=9)
WARN = ParagraphStyle("W", parent=B, backColor=colors.HexColor("#fdf0ea"), borderPadding=6, borderColor=C_ORANGE,
                      borderWidth=0.6, spaceBefore=2, spaceAfter=9)
CODE = ParagraphStyle("CODE", fontName="DVM", fontSize=6.9, leading=8.6, backColor=colors.HexColor("#f4f4f2"),
                      borderPadding=5, spaceBefore=3, spaceAfter=9, textColor=C_INK)

story = []


def P(t, s=B):
    story.append(Paragraph(t, s))


def code(t):
    story.append(Preformatted(t.strip("\n"), CODE))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, BUL, bulletText="•"))
    story.append(Spacer(1, 4))


def fig(name, w=6.3, caption=None):
    from PIL import Image as PImage
    path = FIG / f"{name}.png"
    iw, ih = PImage.open(path).size
    items = [Image(str(path), width=w * inch, height=w * inch * ih / iw)]
    if caption:
        items.append(Paragraph(caption, SM))
    story.append(KeepTogether(items))
    story.append(Spacer(1, 6))


def table(rows, widths, font=7.5):
    body = ParagraphStyle("t", parent=B, fontSize=font, leading=font + 2.4, spaceAfter=0)
    head = ParagraphStyle("th", parent=body, textColor=colors.white, fontName="DVB")
    t = Table([[Paragraph(str(c), head if ri == 0 else body) for c in r] for ri, r in enumerate(rows)],
              colWidths=[w * inch for w in widths], repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cfcfcb")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), C_INK), ("LEFTPADDING", (0, 0), (-1, -1), 4),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story.append(t)
    story.append(Spacer(1, 8))


def pct(x, d=0):
    return f"{100 * x:.{d}f}%"


def short(t, n=70):
    t = " ".join(t.split())
    return t if len(t) <= n else t[:n - 1] + "…"


GREEN = "<font color='#0a7d32'><b>BUILT</b></font>"
AMB = "<font color='#b86e00'><b>HALF BUILT</b></font>"
RED = "<font color='#c0392b'><b>NOT BUILT</b></font>"
iS = UPD.index("stanford")
iM = UPD.index("mit")

# ================================================================================================ 0. overview
P("UNIMATH build spec: the three features", H1)
P("Internal developer document. It says what is being sold, how each piece is calculated (in maths, then in plain "
  "English), what already exists in the code, and exactly what to build next: files, data schemas, functions, CLI "
  "commands, tests and the checks each piece must pass before it's sold. Example numbers are computed live by "
  "<font face='DVM'>scripts/make_offer.py</font> on the example student in <font face='DVM'>examples/profile.toml</font> "
  "(SAT 750/790; MIT, Stanford, Princeton, CMU, Cornell, Georgia Tech, Tufts, Northeastern, Purdue).")
P("<b>The pitch the code has to support:</b> \"Your student can add this school for a few hundred words because "
  "essays already on the list cover most of it. The list's real risk of zero admits is 3-11%, not 2%. And here's how every "
  "remaining school moved after that CMU admit.\"", PLAIN)
table([["Feature", "Customer gets", "Eng.", "Status", "Main missing piece"],
       ["1. Essay map", "Which draft covers which prompt, new words left per school, writing order", "B", RED,
        "LLM-scored prompt matrix for the ~100 most-applied schools, plus a check against counselors' scores"],
       ["2. List check", "Zero-admit risk as a range, and a ranked list of schools that are cheap and worth adding",
        "A + B", AMB, "Risk half works (PORT, ROSTER). The 'cheap to add' ranking needs Engine B plus a new ADD command"],
       ["3. Decision updates", "New odds for every pending school after each admit, deferral, waitlist or reject",
        "A", GREEN, "Ranges on the output; calibration of two settings on real outcomes; proper early-round model"]],
      [1.0, 2.0, 0.5, 0.8, 2.2])
fig("o1_architecture", 6.6, "Figure 1. Two engines feed three features. Engine A is built and tested on simulated "
    "students. Engine B is next, and it's the selling point because it doesn't need more outcome data than the big "
    "platforms have.")
P("<b>Priority order:</b> (1) Engine B and Essay map, the differentiator; (2) the ADD ranking, which turns both engines "
  "into one recommendation; (3) ranges on Decision updates, which is a small change; (4) a delivery surface; "
  "(5) real-outcome calibration, which depends on partners and runs in parallel.")
story.append(PageBreak())

# ================================================================================================ 1. engine A
P("1. Engine A: the admissions model (built)", H1)
P("Code map", H2)
table([["File", "What's there"],
       ["unimath/scores.py", "fit_band (two-piece normal matched to the 25/50/75; 800 ceiling), CompositeDist (Gaussian "
        "copula, ρ = 0.6 between sections)"],
       ["unimath/model.py", "ModelParams (defaults), calibrate() → Calibration per school, Student, AdmissionModel: "
        "prob_grid, decision_loglik, posterior_logw, chances, chances_interval, cross_matrix, count_distribution, "
        "expected_best, p_none_range"],
       ["unimath/fit.py", "Outcomes I/O, marginal_loglik, fit() (L-BFGS-B), scoring rules, simulate()"],
       ["unimath/backtest.py, significance.py", "Experiments E1-E7, cluster bootstrap, exact and permutation tests"],
       ["unimath/cli.py", "Terminal class; each command is a method cmd_XXX(self, args); --json supported"]],
      [1.9, 5.0])
P("How it calculates", H2)
P("Latent index at school j:  U<sub>j</sub> = a<sub>j</sub>·T + b·H + ε<sub>j</sub>, with T the standardized composite, "
  "H the non-test strength and ε<sub>j</sub> ~ N(0, σ²)<br/>"
  "Admit ⇔ U<sub>j</sub> > c<sub>j</sub>,  c<sub>j</sub> = Φ<super>−1</super>(1 − r<sub>j</sub>)·√(a<sub>j</sub>² + b² + σ²)<br/>"
  "Pool (m, s) recovered from the admitted-class SAT moments:  s = sd<sub>adm</sub> / √(1 − ρ²λ(λ − k)),  "
  "m = mean<sub>adm</sub> − sρλ,  λ = φ(k)/r<br/>"
  "Shared factor S ~ N(b·μ<sub>h</sub>, b²σ<sub>h</sub>² + γσ²) is common to all schools; P(admit<sub>j</sub> | S) = "
  "(1 − ω)·Φ((a<sub>j</sub>T + S − c<sub>j</sub>)/σ<sub>j</sub>) + ω·r<sub>j</sub>; integrals over S on an 801-point grid", MATH)
P("<b>In plain English:</b> every applicant gets one hidden score made of test score, non-test strength and luck. "
  "Each school admits above a cut-off chosen so its published acceptance rate and admitted SAT range come out right. "
  "The non-test part is the same application at every school, so it's one shared unknown (S). That shared number is "
  "what links schools (List check) and what each decision teaches us about (Decision updates). The lapse term ω "
  "means the model never says 0% or 100%.", PLAIN)
P("Known weak points (to fix or show honestly)", H2)
bullets(["<b>Two settings are guesses:</b> γ = shared_fit = 0.3 (how much schools agree about the same application) "
         "and the prior sd of non-test strength when no counselor rating is given. They control the size of every "
         "Decision update (Figure 5) and the zero-admit range.",
         "<b>Recovery of settings is only partly reliable:</b> in simulation the error bars covered 65-75% instead of "
         "95%, and one setting was biased (manual, claim 6). Report fits with that caveat.",
         "<b>Early rounds are approximated</b> by recalibrating with the early admit rate (ED command); deferral "
         "semantics aren't modelled.",
         "<b>Non-test strength enters only through one 0-100 rating.</b> That's acceptable: it's the counselor's job, "
         "and it keeps the input simple."])
story.append(PageBreak())

# ================================================================================================ 2. engine B
P("2. Engine B: the essay matrix (to build)", H1)
P("Target: every supplement prompt of the 2026-27 cycle at the ~100 most-applied selective schools, each scored by "
  "an LLM against every other school's prompts with a fixed rubric, checked against counselors, refreshed every August.")
P("R(p, q) ∈ [0, 1] = share of the writing effort for target prompt p saved by a finished essay for source prompt q "
  "(directed: R(p, q) ≠ R(q, p); R = 0 within the same school)<br/>"
  "Prompt cost:  w<sub>p</sub> = word limit + 60 (overhead for ideas and outline); optional prompts cost 0<br/>"
  "Coverage:  C(B | A) = Σ<sub>p∈B</sub> w<sub>p</sub>·max<sub>q∈A</sub> R(p, q) / Σ<sub>p∈B</sub> w<sub>p</sub><br/>"
  "New words to add school k to list L:  W(k | L) = Σ<sub>p∈k</sub> w<sub>p</sub>·(1 − max<sub>q∈L</sub> R(p, q))  "
  "(non-increasing as L grows, so greedy ordering behaves well)", MATH)
P("<b>In plain English:</b> for each pair of prompts the LLM says how much of one essay can be recycled into the other. "
  "Add up what a school asks for, take the best match from what's already written, and you get \"Harvard is 40% done\" "
  "or \"CMU needs 300 new words\". All of the aggregation already exists in <font face='DVM'>unimath/similarity.py</font>; "
  f"only the input R changes. Today R comes from {N_CURATED} hand-scored pairs plus a keyword heuristic that "
  "<b>failed its test</b> (Spearman 0.41 against the hand scores, p = 0.12).", PLAIN)

P("2.1 Collect the prompts", H2)
P(f"Today: {len(REAL)} schools have real prompts ({N_REAL_PROMPTS} prompts) in <font face='DVM'>data/catalog.json</font>; "
  "the other 393 have a placeholder. Target about 100 schools and 350 prompts. Choose schools by how often they're "
  "applied to (Common App application counts, US News top 100 national universities and top 30 liberal arts colleges, "
  "plus the big state flagships with their own portals).")
P("<b>New file</b> <font face='DVM'>data/prompts_2026_27.csv</font>, one row per prompt, maintained by hand:")
code("""
school_id,prompt_id,text,word_limit,required,kind,group,source_url,retrieved
stanford,stanford--significant-challenge,"What is the most significant challenge...",50,true,short,,https://...,2026-08-03
cmu,cmu--why-major,"...",300,true,essay,,https://...,2026-08-04
uc-berkeley,uc--piq-1,"...",350,choose,essay,uc-piq:4-of-8,https://...,2026-08-01
""")
bullets(["<b>kind</b> ∈ essay, short (under 100 words), list (\"five things\"), why_us, optional, existing_work "
         "(\"upload a graded paper\"). The LLM still scores every pair; kind is used for checks and the report wording.",
         "<b>required</b> ∈ true, false, choose. <b>group</b> handles \"choose 4 of 8\" (UC) and \"choose one of\": the "
         "planner picks the cheapest prompts in the group given the list.",
         "<b>Sources:</b> each school's admissions site and the Common App / Coalition / UC portals. Prompts appear "
         "around 1 August; some schools publish late. Keep source_url and the retrieval date for every row.",
         "<b>New script</b> <font face='DVM'>scripts/import_prompts.py</font>: validates the CSV (unique ids, word "
         "limit present unless optional, school exists in catalog, no empty text), then writes the prompts into "
         "catalog.json and drops placeholder flags. Also flags verbatim duplicates across schools (they should score ~100)."])

P("2.2 The rubric (draft v1)", H2)
P("Fixed text sent as the system prompt, versioned (<font face='DVM'>data/rubric_v1.md</font>). The same text is given "
  "to the human raters, so the LLM and the counselors are scored against the same question.")
code("""
You estimate essay reuse between college supplement prompts.
TARGET is a prompt the student still has to answer. SOURCE is a prompt from a different college for which the
student already has a strong, finished essay. Score 0-100: the share of the work for TARGET that is already done.

Anchors   0 nothing reusable | 25 same topic area, new essay needed | 50 same story or material, heavy rewrite
         75 same essay, moderate edits | 100 can be submitted nearly as-is
Rules
 1. Judge content transfer: could the same story, argument or material answer TARGET after editing?
 2. 'Why this school' content transfers poorly. If TARGET asks why this school, cap at 35, unless SOURCE is also a
    why-us essay for the same kind of program (cap 50: the school research must be redone).
 3. Length gaps cost effort. Cutting is cheaper than expanding (650 to 250 words: about -10; 650 to 50: about -25;
    50 to 300: about -40).
 4. Short-answer and list prompts transfer only to near-identical prompts.
 5. Identical or near-identical wording and length: 90-100.
 6. Assume a typical strong student, not one who wrote a deliberately multi-purpose essay.
Return one score and one reason code per SOURCE: SAME, ADAPT, CUT, EXPAND, TOPIC_ONLY, WHY_US, NONE.
""")
P("<b>Tuning:</b> tune the rubric only on a separate <i>dev set</i> of 50 pairs (scored by you plus one counselor). "
  "Never look at the 200 test pairs (2.5) while changing the rubric. Bump the version on every change and store it "
  "with every score.")

P("2.3 The scoring job", H2)
P("Design: put the rubric <i>and the full list of prompts</i> in the system prompt, which is identical for every "
  "request and so is cached. Each request names one target and asks for a score against every prompt from other "
  "schools. One request per target prompt gives one full row of R. Run 3 times with the candidate order shuffled "
  "(fixed seed per run) to average out position effects.")
code('''
# scripts/score_matrix.py  (sketch: Anthropic Python SDK, Message Batches API, structured output)
import anthropic, json, random
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["scores"],
          "properties": {"scores": {"type": "array", "items": {
              "type": "object", "additionalProperties": False, "required": ["q", "score", "reason"],
              "properties": {"q": {"type": "string"}, "score": {"type": "integer"},
                             "reason": {"type": "string", "enum": ["SAME", "ADAPT", "CUT", "EXPAND",
                                                                   "TOPIC_ONLY", "WHY_US", "NONE"]}}}}}}

def requests_for_run(prompts, rubric, run):
    rng = random.Random(run)
    order = prompts[:]; rng.shuffle(order)
    catalog = "\\n".join(f"[{p['prompt_id']}] ({p['word_limit']} words, {p['school_id']}) {p['text']}" for p in order)
    system = [{"type": "text", "text": rubric},
              {"type": "text", "text": "ALL PROMPTS:\\n" + catalog, "cache_control": {"type": "ephemeral"}}]
    for p in prompts:
        yield Request(custom_id=f"r{run}--{p['prompt_id']}", params=MessageCreateParamsNonStreaming(
            model="claude-opus-5-5", max_tokens=16000, system=system,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content":
                       f"TARGET: [{p['prompt_id']}]. Score every prompt from another school as SOURCE."}]))

client = anthropic.Anthropic()
batch = client.messages.batches.create(requests=list(requests_for_run(prompts, rubric, run=1)))
# poll client.messages.batches.retrieve(batch.id) until processing_status == "ended", then
# for r in client.messages.batches.results(batch.id): key by r.custom_id (results come in any order)
''')
bullets(["<b>Check every response:</b> each other-school prompt id appears exactly once, scores in 0-100, no "
         "same-school ids. Re-queue targets that fail, errored or expired. A batch returns within 24 hours (usually 1).",
         "<b>Output</b> <font face='DVM'>data/matrix_llm.csv</font>: <font face='DVM'>p_id, q_id, score_mean, score_sd, "
         "n_runs, reason_mode, rubric_version, model, scored_at</font>. About 120,000 directed rows for 350 prompts.",
         "<b>Flag for human review:</b> run-to-run sd above 15; verbatim duplicates scoring under 85; why-us targets "
         "scoring above 50; any pair where R(p, q) and R(q, p) differ by more than 50.",
         "<b>Effort setting:</b> start at medium; compare low and high on the dev set and keep the cheapest level that "
         "matches agreement with the dev scores."])
P("<b>Cost</b> (Claude Opus 5.5: $4 input / $20 output per million tokens; Batch API is half price; cached input "
  "reads cost much less). Each run is about 350 requests. Input is mostly the cached ~17k-token prompt list; output is "
  "about 350 scores plus thinking, around 5-8k tokens per request. Roughly <b>$30-40 per run, about $100 for three "
  "runs</b>. Scoring each pair in its own request instead (~120,000 requests) would cost several hundred to over a "
  "thousand dollars and has no accuracy benefit to justify it. The annual refresh only rescores rows and columns of "
  "prompts that changed.", WARN)

P("2.4 Wire it into SimilarityEngine", H2)
P("Change <font face='DVM'>SimilarityEngine.__init__</font> to take <font face='DVM'>llm_csv</font>, and "
  "<font face='DVM'>_build</font> to fill R in priority order: <b>human (curated) &gt; LLM &gt; heuristic</b>, setting "
  "<font face='DVM'>self.source[i, j]</font> to curated / llm / model. Note the existing curated table is "
  "<i>undirected</i> (keys are sorted pairs): keep that for human scores but store LLM scores directed.")
code("""
key_dir = (p.id, q.id)
if key_undirected in self.curated:  R[i, j] = self.curated[key_undirected];  self.source[i, j] = "curated"
elif key_dir in self.llm:           R[i, j] = self.llm[key_dir] / 100;       self.source[i, j] = "llm"
else:                               R[i, j] = heuristic(i, j);               self.source[i, j] = "model"
""")
P("Tests to add in <font face='DVM'>tests/test_unimath.py</font>: priority order (a pair in both tables takes the "
  "human value); R stays in [0, 1] and is 0 within a school; marginal effort still never increases as the written set "
  "grows; ESSY, FREE and PLAN run with the LLM table loaded; DQ reports what share of a list's pairs come from each source.")

P("2.5 Check it against counselors (the gate for selling Essay map)", H2)
bullets(["<b>Sample:</b> 200 test pairs, stratified by LLM score (40 from each 20-point band), at most 3 pairs per "
         f"target prompt, plus the {N_CURATED} existing hand-scored pairs as anchors. A separate 50-pair dev set is used "
         "for rubric tuning only.",
         "<b>Raters:</b> 2-3 counselors score all 200 blind, in a CSV (<font face='DVM'>pair_id, target_text, "
         "source_text, word limits, score, reason</font>), using the same rubric. That's about 3-4 hours each; pay them "
         "or give a free year.",
         "<b>New script</b> <font face='DVM'>scripts/validate_matrix.py</font> computes: human-human Spearman ρ<sub>HH</sub> "
         "and mean absolute difference; LLM vs rater-mean Spearman ρ<sub>LH</sub> and MAE<sub>LH</sub>; the same for a "
         "constant guess (the rater mean, leave-one-out) and for the old heuristic. It reuses "
         "<font face='DVM'>significance.cluster_bootstrap_diff</font> (cluster on target prompt, since pairs share "
         "prompts) and <font face='DVM'>permutation_spearman</font>. Results go in results/matrix_validation.json and a "
         "rerun of experiment E5."])
P("Gate G1:  MAE<sub>LH</sub> &lt; MAE<sub>constant</sub>, with the 95% cluster-bootstrap CI of the difference below 0<br/>"
  "Gate G2:  ρ<sub>LH</sub> ≥ ρ<sub>HH</sub> − 0.05 (the LLM agrees with counselors about as well as they agree with each other)<br/>"
  "Gate G3:  mean signed error within ±8 points overall and within each kind (essay, short, why_us)<br/>"
  "Rough power: with an sd of about 15 points in per-pair error differences and ~100 effective clusters, the SE of the "
  "MAE difference is about 1.5 points, so a 4-5 point improvement is detectable.", MATH)
P("<b>If it fails:</b> look at the disagreements by reason code, fix the rubric on the dev set, rescore, and "
  "re-check on a <i>fresh</i> 100-pair test set (the old one is now contaminated). If it still fails, sell the matrix "
  "only for the human-scored top 30 schools.")

P("2.6 Every August, and later: real reuse logs", H2)
bullets(["Diff the new prompts CSV against last year's. Rescore only changed or new prompts (their rows and columns). "
         "Re-run the gate on 50 fresh pairs that involve changed prompts. Target: refreshed map out within 2 weeks of "
         "the prompts being published.",
         "<b>Reuse logs</b> (the long-term moat): an optional counselor form, <font face='DVM'>student_hash, "
         "target_prompt_id, source_prompt_id, share_kept (0-100), year</font>. After one cycle these are real R values "
         "nobody else has, and they become the human layer."])
story.append(PageBreak())

# ================================================================================================ 3. essay map
P("3. Feature 1: Essay map", H1)
P("<b>What the customer sees:</b> for one student's list, (a) the coverage table, (b) \"write once, adapt\" clusters, "
  "(c) a writing order with new words per step, and (d) a per-prompt instruction: <i>\"CMU prompt 2: adapt your MIT "
  "field-of-study essay, cut 650 → 300 words\"</i>.")
fig("o2_coverage", 5.8, "Figure 2. <b>Illustrative only:</b> today's placeholder heuristic, so this shows the format, "
    "not real answers. Read across a row: the Cornell row says ~40% of Cornell's supplement is covered by the MIT, "
    "Stanford or Princeton essays. Georgia Tech and Northeastern are left out because their supplements cost 0 words.")
P("<b>Writing order</b>, computed by greedy ordering on W(k | L): start with the school whose own supplement is "
  "heaviest, then always take the one needing the fewest new words given what's written. Example (placeholder R):")
table([["Step", "School", "New words this step", "Reuses mostly from"]] +
      [[str(n + 1), NAME[sid], f"{cost:,.0f}",
        (NAME.get(E.prompts[max(det, key=lambda d: d[1])[2]].school, "-")
         if det and max(det, key=lambda d: d[1])[2] is not None else "-")]
       for n, (sid, cost, det) in enumerate([st_ for st_ in PLAN_STEPS if E.standalone_effort(st_[0]) > 0])],
      [0.5, 1.6, 1.6, 1.8])
P(f"Total about {words_list:,.0f} word-equivalents with reuse, against {words_alone:,.0f} written from scratch. "
  "Per-prompt mapping for one school (CMU, given the rest of the list), the raw material for instruction (d):")
table([["CMU prompt", "Words", "Best source prompt", "Reuse", "New words"]] +
      [[short(E.prompts[i].text, 62), str(E.prompts[i].words),
        short(E.prompts[j].id, 38) if j is not None else "-", pct(r), f"{E.prompt_cost(i) * (1 - r):.0f}"]
       for i, r, j in CMU_DET], [2.7, 0.5, 2.2, 0.55, 0.75], font=7)
P("Build spec", H3)
bullets(["<b>similarity.py:</b> add <font face='DVM'>plan_writing(sids) -> list[Step]</font>, with Step = (school, "
         "new_words, [(prompt_id, source_prompt_id, reuse, reason, words_to_write)]). This is "
         "<font face='DVM'>writing_plan()</font> in make_offer.py, moved and typed. Make "
         "<font face='DVM'>list_effort</font> call it so there's one implementation.",
         "<b>Choice groups:</b> for \"choose k of n\" prompts, pick the k cheapest given the written set (still greedy, "
         "still non-increasing).",
         "<b>Instruction text</b> from reason code plus the length change: SAME → \"reuse\", ADAPT → \"adapt\", CUT → "
         "\"cut 650 → 250\", EXPAND, TOPIC_ONLY → \"same topic, new essay\", WHY_US → \"school research needed\", NONE → "
         "\"write new\".",
         "<b>cli.py:</b> new <font face='DVM'>cmd_EMAP</font> printing (a)-(d), with --json. Mark every number from a "
         "non-validated source (llm before gate, model) with a ~ sign.",
         "<b>Report:</b> a one-page student plan (reportlab, reusing the BRIEF style) via <font face='DVM'>EMAP "
         "--pdf out.pdf</font>.",
         "<b>Tests:</b> the plan's order is a permutation of the list; the sum of step words equals list_effort; human "
         "scores override; each target maps to a source from a different school; JSON output parses."])
P("<b>Effort:</b> about 3-5 days after Engine B exists. <b>Sell when:</b> gates G1-G3 pass for the schools in the "
  "customer's lists.")

# ================================================================================================ 4. list check
P("4. Feature 2: List check", H1)
P("(a) The real risk of no admits (built: PORT, ROSTER, BRIEF)", H2)
P("P(no admits) = ∫ Π<sub>j∈L</sub> (1 − P<sub>j</sub>(s)) dF(s)    versus the naive    Π<sub>j∈L</sub> (1 − P<sub>j</sub>)<br/>"
  "Range (AdmissionModel.p_none_range): min and max over γ ∈ {0.05, 0.3, 0.5}, ω ∈ {0.02, 0.05, 0.10} and "
  "unknown-strength sd ∈ {0.5σ<sub>h</sub>, σ<sub>h</sub>}: 18 model runs", MATH)
P("<b>In plain English:</b> multiplying the chances of rejection assumes each school flips its own coin. But it's "
  "the same application everywhere, so rejections come in clumps, and getting nothing is more likely than the "
  f"product says. Example list: naive {pct(p_indep, 1)}; linked model {pct(p_none, 1)}, range {pct(p_lo, 1)} to "
  f"{pct(p_hi, 1)}. Families see low / moderate / high (BRIEF family).", PLAIN)
P("(b) What to add (to build: ADD command)", H2)
P("Value of adding k:  ΔV(k) = E[u(best admit) | L ∪ {k}] − E[u(best admit) | L]   (expected_best; always ≥ 0)<br/>"
  "Safety gain:  ΔP<sub>0</sub>(k) = P(no admits | L) − P(no admits | L ∪ {k})<br/>"
  "Cost:  W(k | L) new words (Engine B).   Rank by ΔV(k) / W(k | L); tag 'nearly free' if W(k | L) &lt; ¼ of k's "
  "standalone words", MATH)
P("<b>In plain English:</b> a school is worth adding if it raises the expected quality of where the student ends up: "
  "a likely school protects against getting nothing, a dream school adds a chance at the top. It's cheap if the "
  "essays already written cover most of it. Combining the two gives the pitch: \"Harvard is mostly written already, "
  "so apply\". Utilities come from the family's own ranking (here MIT 100 down to Purdue 60, fallback 40).", PLAIN)
fig("o3_listcheck", 6.0, "Figure 3. <b>Illustrative only</b> (x-axis from the placeholder heuristic). Each dot is a "
    "school that could be added to the example list; up and to the left is better. Orange marks the best value per word.")
table([["Add", "Chance alone", "Already written", "New words", "ΔV", "ΔV per 100 words", "Main reuse from"]] +
      [[NAME[r["id"]], pct(r["p"], 1), pct(r["covered"]), f"{r['marg']:,.0f}", f"{r['gain']:.2f}", f"{r['per100']:.3f}",
        NAME.get(r["src"], r["src"] or "-")] for r in cand_rows], [1.05, 0.85, 0.9, 0.8, 0.6, 1.05, 1.4], font=7.2)
P("Harvard is fairly cheap to add but its odds are low, so its value per word is modest; USC reuses Purdue's essay "
  "and has real odds, so it comes out on top. Neither engine alone gives this answer.")
P("Build spec", H3)
bullets(["<b>cli.py:</b> new <font face='DVM'>cmd_ADD [n]</font>. Candidates: every catalog school with a usable "
         "calibration and real prompts, not already on the list; optional filters (max acceptance rate, region later). "
         "For each: chance alone, ΔV, ΔP<sub>0</sub>, W(k | L), coverage, main source; sort by ΔV/W; print the top n.",
         "<b>Speed:</b> ~100 candidates × one expected_best call each (grid of 801 × |L|+1). Fine in one process. "
         "Cache prob_grid rows per school so they aren't recomputed.",
         "<b>Utilities:</b> add tiers to profile.toml (<font face='DVM'>tier = \"dream\" | \"like\" | \"fine\"</font> → "
         "100 / 80 / 60) so counselors never type numbers; candidates default to their tier by selectivity.",
         "<b>Ranges:</b> report ΔV over the same γ/ω grid as p_none_range; drop a candidate's 'nearly free' tag if any "
         "of its pairs are from the heuristic.",
         "<b>ROSTER:</b> add a column 'best cheap add' per student.",
         "<b>Tests:</b> ΔV ≥ 0; W(k | L) ≤ standalone; adding a school identical to one on the list gives W = 0 for "
         "identical prompts; the ranking is stable under candidate order; --json parses."])
P("<b>Effort:</b> 1-2 days for ADD and tiers once Engine B exists. The risk half can be sold now, as a range.")

# ================================================================================================ 5. decision updates
P("5. Feature 3: Decision updates (built: DEC, UPDT, XADM)", H1)
P("<b>What the customer sees:</b> record a real result and get new odds for every pending school. This is the "
  "mid-December feature: early results arrive about two weeks before most Regular Decision deadlines, when families "
  "decide whether to keep writing reach applications, add safer schools, or use Early Decision II.")
fig("o4_updates", 6.0, f"Figure 4. Computed by the toolkit for the example student. A CMU admit: MIT {pct(before[iM], 1)} → "
    f"{pct(after1[iM], 1)}, Stanford {pct(before[iS], 1)} → {pct(after1[iS], 1)}. Adding an MIT reject pulls them "
    f"partway back (Stanford → {pct(after2[iS], 1)}). Safe schools barely move.")
P("f(s | D) ∝ f(s) · Π<sub>k∈D</sub> P(d<sub>k</sub> | s)   (AdmissionModel.posterior_logw)<br/>"
  "P(admit | s) = P<sub>k</sub>(s);  P(reject | s) = 1 − P<sub>k</sub>(s + δ);  P(waitlist or defer | s) = "
  "P<sub>k</sub>(s + δ) − P<sub>k</sub>(s)  (δ = waitlist_width; outcomes mutually exclusive, regression-tested)<br/>"
  "P(admit<sub>j</sub> | D) = ∫ P<sub>j</sub>(s) f(s | D) ds  (chances(..., decisions=D))", MATH)
P("<b>In plain English:</b> before results, the model is unsure how strong the non-test part of the application is. "
  "A CMU admit says it's reading well; an MIT reject says it's not quite that strong. Bayes' rule combines all results "
  "into one updated belief, and every remaining school is re-priced from it. Deferrals and waitlists count as \"in "
  "between\", so they move the odds less.", PLAIN)
fig("o5_sensitivity", 5.7, "Figure 5. How much a CMU admit raises the Stanford odds, depending on the two unmeasured "
    "settings: link strength γ (x-axis), and whether the counselor rated the student, which removes some uncertainty "
    "so each decision teaches less.")
P("The direction is always right (admit raises, reject lowers), and in simulation using a student's other decisions "
  "cut prediction error by 18-24%, the biggest gain we measured. <b>The size of the jump isn't measured.</b> 18% → 50% "
  "for Stanford after one CMU admit may be too large. Until it's calibrated, show ranges.", WARN)
P("Build spec", H3)
table([["Step", "Work", "Size", "Done when"],
       ["1. Ranges", "AdmissionModel.chances_range(student, ids, decisions): min/central/max over the same γ, ω and sd "
        "grid as p_none_range. UPDT prints 'lo-hi (central)'; BRIEF uses the range.", "1 day",
        "Test: range brackets the central value; it collapses when γ and sd are fixed"],
       ["2. Data", "De-identified past results from 3-10 practices. Extend the FIT outcomes CSV with round (ED, EA, REA, "
        "RD, ED2) and year. Target 300+ students with full lists. Data terms draft: sales/DATA_TERMS_DRAFT.md.",
        "Depends on partners", "Files received; DQ passes"],
       ["3. How much data?", "scripts/power_shared.py: simulate N students from the default settings (fit.simulate), "
        "refit, record the SE of shared_fit and holistic sd for N = 100 ... 1000. Pick N where SE(γ) ≤ 0.08.",
        "0.5 day", "Plot of SE vs N; the partner target comes from it"],
       ["4. Calibrate", "FIT on pooled data with shared_fit and the holistic sd free; held-out students only.",
        "2-3 days once data exists", "Held-out log loss with updates beats without; 80% ranges cover 75-85%"],
       ["5. Early rounds", "Per-school early admit rate (Common Data Set C21-C22) and a separate cut-off for the early "
        "pool; a deferral is a 'not admitted early' observation plus a pending RD decision.", "1 week",
        "Early-round outcomes scored separately"]], [0.95, 3.25, 0.9, 1.8], font=7.2)
story.append(PageBreak())

# ================================================================================================ 6. delivery, order, risks
P("6. Delivery, build order and risks", H1)
P("Delivery: how a non-technical counselor gets this", H2)
bullets(["<b>Stage 1, concierge (no UI):</b> the counselor sends a CSV (student id, scores, rating, list); you run "
         "EMAP, ADD, PORT and BRIEF and send back a PDF per student. This tests demand before any UI is built. "
         "Needs --pdf output on EMAP and BRIEF.",
         "<b>Stage 2, web:</b> a small Python service (e.g. FastAPI) wrapping the existing --json command output, called "
         "from the existing Vite/React + Supabase app in the repo root. Keep the maths in Python; don't port it to "
         "TypeScript.",
         "<b>Never:</b> ask counselors to install the CLI."])
P("Build order", H2)
table([["#", "Milestone", "Unblocks", "Size"],
       ["1", "prompts_2026_27.csv for ~100 schools + import_prompts.py + rubric v1 + 50-pair dev set", "Engine B", "4-5 days"],
       ["2", "score_matrix.py, 3 runs, consistency flags, matrix_llm.csv; SimilarityEngine priority layers + tests",
        "Engine B", "2-3 days, ~$100"],
       ["3", "200-pair counselor check, validate_matrix.py, gates G1-G3", "Selling Essay map", "2-3 weeks elapsed"],
       ["4", "plan_writing + EMAP (+ --pdf)", "Essay map", "3-5 days"],
       ["5", "ADD + tiers + ROSTER column", "List check", "1-2 days"],
       ["6", "chances_range + UPDT/BRIEF ranges", "Decision updates", "1 day"],
       ["7", "Concierge pilot with 2-3 counselors", "Evidence of demand", "This cycle"],
       ["8", "power_shared.py, partner data, calibration, early rounds", "Real accuracy claims", "Next cycle"],
       ["9", "Web service + front end", "Self-serve sales", "1-3 weeks"]], [0.3, 3.7, 1.6, 1.3])
P("What is not sold separately", H2)
P("PCTL, CHNC, XADM, PLAN, SENS, SCH, DQ, LEDGER/SCORE and BKTST stay in the toolkit as plumbing or for building a "
  "track record (LEDGER freezes forecasts so they can be graded in spring). BKTST can't show anything on one class of "
  "25 students, so it isn't marketed.")
P("Risks", H2)
bullets(["<b>Easy to copy:</b> the matrix costs about $100 to compute, so anyone with a chatbot can make a rough one. "
         "The defence is the counselor-checked rubric, the August refresh delivered before students start, and reuse "
         "logs nobody else has.",
         "<b>Gate failure:</b> the LLM might not match counselors. Fallback: keep the LLM to pre-sort, and have humans "
         "confirm only the top 3 sources per target prompt (about 350 × 3 = 1,050 checks) instead of scoring every pair.",
         "<b>Demand:</b> experienced counselors may already know the overlaps for the top 20 schools. The concierge "
         "pilot is there to find out before stage 2.",
         "<b>Update sizes:</b> wrong until calibrated. Always show ranges.",
         "<b>Prompt timing:</b> some schools publish late in August; the map must handle 'prompt not yet released'."])


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("DV", 7)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(0.75 * inch, 0.5 * inch, "UNIMATH build spec: the three features (internal, November 2026)")
    canvas.drawRightString(7.75 * inch, 0.5 * inch, f"{doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                        topMargin=0.7 * inch, bottomMargin=0.75 * inch, title="UNIMATH build spec: the three features",
                        author="UNIMATH")
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"wrote {OUT}")
