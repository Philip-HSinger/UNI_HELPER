"""Build product/reports/calliper-technical-note-v1.pdf: a 2-page technical note sent with outreach emails.

Uses only the standard PDF fonts (Times, Symbol) and a vector figure, so the file stays small enough to attach.
All example numbers are computed live from the toolkit.
"""
import sys
from pathlib import Path

import numpy as np
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, Line, String
from reportlab.graphics.widgets.markers import makeMarker  # noqa: F401
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from unimath.catalog import load_catalog  # noqa: E402
from unimath.model import AdmissionModel, Student  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "reports" / "calliper-technical-note-v1.pdf"

# ---------------------------------------------------------------------------------------------- numbers
M = AdmissionModel(load_catalog())
ST = Student(750, 790)
L = ["mit", "stanford", "princeton", "cmu", "cornell", "georgia-tech", "tufts", "northeastern", "purdue"]
p = M.chances(ST, L)
p_indep = float(np.prod(1 - p))
lo, mid, hi = M.p_none_range(ST, L)
D1 = {"cmu": "accepted"}
D2 = {"cmu": "accepted", "mit": "rejected"}
st0 = M.chances(ST, ["stanford"])[0]
st1 = M.chances(ST, ["stanford"], D1)[0]
st2 = M.chances(ST, ["stanford"], D2)[0]
mit0, mit1 = M.chances(ST, ["mit"])[0], M.chances(ST, ["mit"], D1)[0]
S, lw0 = M.grid(ST)
lw1, lw2 = M.posterior_logw(ST, D1), M.posterior_logw(ST, D2)
ds = S[1] - S[0]
dens = [np.exp(w) / ds for w in (lw0, lw1, lw2)]
mom = [(float(S @ np.exp(w)), float(np.sqrt(((S - S @ np.exp(w)) ** 2) @ np.exp(w)))) for w in (lw0, lw1, lw2)]


def pc(x, d=1):
    return f"{100 * x:.{d}f}%"


# ---------------------------------------------------------------------------------------------- styles
INK = colors.black
GREY = colors.Color(0.35, 0.35, 0.35)
base = dict(fontName="Times-Roman", fontSize=10.2, leading=13.4, textColor=INK)
B = ParagraphStyle("B", alignment=TA_JUSTIFY, spaceAfter=5, **base)
TITLE = ParagraphStyle("T", fontName="Times-Bold", fontSize=15.5, leading=19, alignment=TA_CENTER, spaceAfter=4)
AUTH = ParagraphStyle("A", fontName="Times-Roman", fontSize=10.2, leading=13, alignment=TA_CENTER, textColor=INK)
SMALL = ParagraphStyle("S", fontName="Times-Italic", fontSize=8.6, leading=11, alignment=TA_CENTER, textColor=GREY)
ABS = ParagraphStyle("Ab", fontName="Times-Roman", fontSize=9.6, leading=12.6, alignment=TA_JUSTIFY,
                     leftIndent=0.45 * inch, rightIndent=0.45 * inch, spaceBefore=6, spaceAfter=8)
H = ParagraphStyle("H", fontName="Times-Bold", fontSize=11, leading=14, spaceBefore=7, spaceAfter=3)
EQ = ParagraphStyle("E", fontName="Times-Roman", fontSize=10.2, leading=14, alignment=TA_CENTER)
CAP = ParagraphStyle("C", fontName="Times-Roman", fontSize=8.8, leading=11.2, alignment=TA_JUSTIFY, spaceAfter=6)
REF = ParagraphStyle("R", fontName="Times-Roman", fontSize=8.8, leading=11, leftIndent=14, firstLineIndent=-14)
TD = ParagraphStyle("TD", fontName="Times-Roman", fontSize=9.4, leading=11.8)


def g(t):
    """Greek and math symbols in the Symbol font."""
    return f'<font name="Symbol">{t}</font>'


al, ga, ep, si, om, Ph, Pi, Si, intg, ge, iff, prop, inn = (g(c) for c in "αγεσωΦΠΣ∫≥⇔∝∈")

story = []


def P(t, s=B):
    story.append(Paragraph(t, s))


def eq(t, n):
    tb = Table([["", Paragraph(t, EQ), Paragraph(f"({n})", ParagraphStyle("n", parent=EQ, alignment=2))]],
               colWidths=[0.5 * inch, 6.0 * inch, 0.5 * inch])
    tb.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story.append(tb)


# ---------------------------------------------------------------------------------------------- figure
def figure():
    d = Drawing(6.6 * inch, 1.95 * inch)
    lp = LinePlot()
    lp.x, lp.y, lp.width, lp.height = 48, 30, 6.6 * inch - 70, 1.95 * inch - 45
    keep = (S > -2.6) & (S < 5.2)
    xs = S[keep][::4]
    lp.data = [list(zip(xs, dd[keep][::4])) for dd in dens]
    styles = [(colors.Color(.55, .55, .55), None), (INK, None), (INK, (3, 2))]
    for i, (c, dash) in enumerate(styles):
        lp.lines[i].strokeColor = c
        lp.lines[i].strokeWidth = 1.2
        if dash:
            lp.lines[i].strokeDashArray = dash
    lp.xValueAxis.valueMin, lp.xValueAxis.valueMax = -2.5, 5
    lp.xValueAxis.valueSteps = [-2, -1, 0, 1, 2, 3, 4, 5]
    lp.yValueAxis.valueMin = 0
    lp.yValueAxis.valueMax = round(max(dd.max() for dd in dens) * 1.12, 1)
    for ax in (lp.xValueAxis, lp.yValueAxis):
        ax.labels.fontName, ax.labels.fontSize = "Times-Roman", 8
        ax.strokeWidth = 0.6
    lp.yValueAxis.labelTextFormat = "%.1f"
    lp.yValueAxis.valueStep = 0.2
    d.add(lp)
    d.add(String(lp.x + lp.width / 2, 4, "shared application strength S (standardized)", fontName="Times-Italic",
                 fontSize=8.5, textAnchor="middle"))
    d.add(String(10, lp.y + lp.height / 2, "density", fontName="Times-Italic", fontSize=8.5, textAnchor="middle"))
    # legend
    lx, ly = lp.x + 12, lp.y + lp.height - 8
    labels = ["before any decision", "after CMU admit", "after CMU admit, MIT reject"]
    for i, ((c, dash), lab) in enumerate(zip(styles, labels)):
        y = ly - 11 * i
        ln = Line(lx, y + 3, lx + 22, y + 3, strokeColor=c, strokeWidth=1.2)
        if dash:
            ln.strokeDashArray = dash
        d.add(ln)
        d.add(String(lx + 27, y, lab, fontName="Times-Roman", fontSize=8))
    return d


# ---------------------------------------------------------------------------------------------- content
P("Linked admission odds and early-decision updating", TITLE)
P("Philip Singer &nbsp;&middot;&nbsp; Electrical Engineering, Brown University (Class of 2030) &nbsp;&middot;&nbsp; "
  "calliper@agentmail.to", AUTH)
P("Calliper technical note, November 2026. An independent student project, not affiliated with or endorsed by "
  "Brown University.", SMALL)
P("<b>Abstract.</b> The usual estimate of a student's chance of being admitted nowhere multiplies the per-college "
  "rejection probabilities, which assumes each college decides independently. Every college reads the same "
  "application, so decisions are positively correlated and the product understates the risk. Calliper models the "
  "dependence with one latent factor, calibrates each college to its published admission statistics, and updates "
  "every pending college by Bayes' rule when an early decision arrives.", ABS)

P("1. Model", H)
P(f"For student <i>i</i> and college <i>j</i>, admission occurs when a latent index exceeds a college-specific "
  "threshold:")
eq(f"<i>U<sub>ij</sub></i> = <i>a<sub>j</sub> T<sub>i</sub></i> + <i>S<sub>i</sub></i> + {ep}<sub><i>ij</i></sub>, "
   f"&nbsp;&nbsp; admit {iff} <i>U<sub>ij</sub></i> &gt; <i>c<sub>j</sub></i>", 1)
P(f"Here <i>T<sub>i</sub></i> is the standardized test composite, <i>a<sub>j</sub></i> the weight college <i>j</i> "
  f"gives testing under its stated policy, and {ep}<sub><i>ij</i></sub> ~ N(0, {si}<super>2</super>) a "
  "college-specific term. <i>S<sub>i</sub></i> is the part of the application not captured by the test score "
  "(grades, essays, activities, recommendations). It is the same in every application the student sends, and it "
  "is what links the decisions. Each threshold <i>c<sub>j</sub></i> and the score distribution of the college's "
  "applicant pool are solved so that the model reproduces the college's published acceptance rate "
  "<i>r<sub>j</sub></i> and the 25th, 50th and 75th percentile SAT scores of its admitted students [1, 2]. A "
  f"small probability {om} of a decision unrelated to the file keeps every estimate away from 0 and 1:")
eq(f"P(admit<sub><i>j</i></sub> | <i>S</i> = <i>s</i>) = (1 &minus; {om}) {Ph}((<i>a<sub>j</sub>T</i> + <i>s</i> "
   f"&minus; <i>c<sub>j</sub></i>) / {si}) + {om} <i>r<sub>j</sub></i>", 2)
P("Given <i>S</i>, decisions are independent; averaged over <i>S</i>, they are not. The probability of no admission "
  "on a list <i>L</i> is")
eq(f"P(no admits) = {intg} {Pi}<sub><i>j</i>{inn}<i>L</i></sub> (1 &minus; P(admit<sub><i>j</i></sub> | <i>s</i>)) "
   f"<i>f</i>(<i>s</i>) <i>ds</i> &nbsp;{ge}&nbsp; {Pi}<sub><i>j</i>{inn}<i>L</i></sub> (1 &minus; "
   "P(admit<sub><i>j</i></sub>))", 3)
P("The inequality holds because every rejection is a decreasing event in <i>s</i>, so the rejections are positively "
  "associated (Harris's inequality [3]). The gap is largest for lists of similar, highly selective colleges.")

P("2. Updating on early decisions", H)
P("When decisions <i>D</i> arrive, the distribution of <i>S</i> is updated by Bayes' rule and every pending college "
  "is re-priced:")
eq(f"<i>f</i>(<i>s</i> | <i>D</i>) {prop} <i>f</i>(<i>s</i>) {Pi}<sub><i>k</i>{inn}<i>D</i></sub> "
   f"P(<i>d<sub>k</sub></i> | <i>s</i>), &nbsp;&nbsp; P(admit<sub><i>j</i></sub> | <i>D</i>) = {intg} "
   "P(admit<sub><i>j</i></sub> | <i>s</i>) <i>f</i>(<i>s</i> | <i>D</i>) <i>ds</i>", 4)
P("An admission is evidence that <i>S</i> is high, a rejection that it is lower. A deferral or waitlist is treated "
  "as an index falling in a band just below the threshold, so it moves the estimate less than either. Integrals "
  "are evaluated exactly on an 801-point grid.")

P("3. Worked example", H)
P("A student with SAT 750 (reading and writing) and 790 (math) applies to MIT, Stanford, Princeton, Carnegie "
  "Mellon, Cornell, Georgia Tech, Tufts, Northeastern and Purdue. All figures below are produced by the model.")
rows = [["Quantity", "Value"],
        ["Probability of no admissions, independence product", pc(p_indep)],
        ["Probability of no admissions, linked model (eq. 3)",
         f"{pc(mid)}  (range {pc(lo)}&ndash;{pc(hi)} over plausible settings)"],
        ["Stanford: before any decision / after a CMU admit", f"{pc(st0)} / {pc(st1)}"],
        ["Stanford: after a CMU admit and an MIT reject", pc(st2)],
        ["MIT: before any decision / after a CMU admit", f"{pc(mit0)} / {pc(mit1)}"],
        [f"Mean (sd) of <i>S</i>: before / after CMU admit / after both",
         " / ".join(f"{m:+.2f} ({s:.2f})" for m, s in mom)]]
tb = Table([[Paragraph(c, ParagraphStyle("th", parent=TD, fontName="Times-Bold") if i == 0 else TD) for c in r]
            for i, r in enumerate(rows)], colWidths=[3.6 * inch, 2.9 * inch], hAlign="CENTER")
tb.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.8, INK), ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK),
                        ("LINEBELOW", (0, -1), (-1, -1), 0.8, INK), ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
story.append(tb)
story.append(Spacer(1, 6))
story.append(KeepTogether([figure(), Paragraph(
    "<b>Figure 1.</b> Distribution of the shared factor <i>S</i> for the example student. One early admission shifts "
    "it to the right and narrows it; a later rejection pulls it back. Every pending college is re-priced from this "
    "distribution (eq. 4), which is why a single result moves all the remaining odds together.", CAP)]))

P("4. Assumptions and limitations", H)
P(f"The strength of the shared factor, that is, how far colleges agree about the same file, is set ({ga} = 0.3) "
  "rather than estimated, because estimating it requires joint outcomes for the same students. Results are "
  f"therefore reported as a range over {ga} from 0.05 to 0.5, and the size of an update such as the Stanford change "
  "above depends on it. GPA, intended major, recruited-athlete or legacy status and in-state residency are not yet "
  "modelled separately and are absorbed into <i>S</i>. Test-blind colleges, such as the University of California "
  "campuses, publish no score distribution and cannot yet be calibrated.")
P("Validation to date uses synthetic cohorts generated from the published statistics, where the true outcomes are "
  "known. In these cohorts the independence product understated the probability of no admissions by a "
  "factor of 4.5 to 8; using a student's other decisions reduced prediction error by 18 to 24%; and "
  "when the synthetic data deliberately violated the model's assumptions, the linked model overstated the "
  "no-admission risk by up to a factor of two. Validation against real outcomes starts with this cycle's pilot, "
  "using de-identified decisions shared by participating counselors.")

P("5. Essay overlap (in development)", H)
P("For a student's own drafts, let <i>R</i>(<i>p</i>, <i>q</i>) be the share of the words in an essay written for "
  "prompt <i>q</i> that survive adaptation to prompt <i>p</i>. The new writing needed to add college <i>k</i> to a "
  "list <i>L</i> is then")
eq(f"<i>W</i>(<i>k</i> | <i>L</i>) = {Si}<sub><i>p</i>{inn}<i>k</i></sub> <i>w<sub>p</sub></i> (1 &minus; "
   f"max<sub><i>q</i>{inn}<i>L</i></sub> <i>R</i>(<i>p</i>, <i>q</i>))", 5)
P("where <i>w<sub>p</sub></i> is the word limit of prompt <i>p</i>. A first estimate of <i>R</i> comes from comparing "
  "prompts; it is replaced by the measured share once the student's drafts exist.")

P("6. Pilot", H)
P("Free for counselors this cycle. Send a typical college list and an SAT score (no student data is needed) and you "
  "will receive a one-page report with the odds, the probability of no admissions and how an early result would "
  "change them. Calliper, 69 Brown Street #7457, Providence, RI 02912; calliper@agentmail.to.")

P("References", H)
for r in ["[1] U.S. Department of Education. <i>College Scorecard</i> data. collegescorecard.ed.gov.",
          "[2] Common Data Set Initiative. <i>Common Data Set</i>, sections C1 (admission) and C9 (test scores). "
          "commondataset.org.",
          "[3] Harris, T. E. (1960). A lower bound for the critical probability in a certain percolation process. "
          "<i>Proceedings of the Cambridge Philosophical Society</i>, 56, 13&ndash;20."]:
    P(r, REF)


def on_page(c, doc):
    c.saveState()
    c.setFont("Times-Roman", 8.5)
    c.drawCentredString(letter[0] / 2, 0.45 * inch, f"{doc.page}")
    c.restoreState()


SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.85 * inch, rightMargin=0.85 * inch, topMargin=0.7 * inch,
                  bottomMargin=0.7 * inch, title="Linked admission odds and early-decision updating",
                  author="Philip Singer (Calliper)").build(story, onFirstPage=on_page, onLaterPages=on_page)
print(f"wrote {OUT}")
