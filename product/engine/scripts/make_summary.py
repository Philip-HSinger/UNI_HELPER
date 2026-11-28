"""Build product/reports/calliper-summary-v1.pdf: the one-page version of the feature build spec.
Run scripts/make_offer.py first (it draws the figures)."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "results" / "figures" / "offer"
OUT = ROOT.parent / "reports" / "calliper-summary-v1.pdf"
F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", F + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

INK, BLUE = colors.HexColor("#0b0b0b"), colors.HexColor("#2a78d6")
H1 = ParagraphStyle("H1", fontName="DVB", fontSize=15, leading=19, spaceAfter=6, textColor=INK)
H2 = ParagraphStyle("H2", fontName="DVB", fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=3, textColor=BLUE)
B = ParagraphStyle("B", fontName="DV", fontSize=8.8, leading=12.4, spaceAfter=4)
M = ParagraphStyle("M", parent=B, backColor=colors.HexColor("#f4f4f2"), borderPadding=4, spaceBefore=2, spaceAfter=6)
T = ParagraphStyle("T", parent=B, fontSize=7.8, leading=10.2, spaceAfter=0)
TH = ParagraphStyle("TH", parent=T, fontName="DVB", textColor=colors.white)
story = []


def P(t, s=B):
    story.append(Paragraph(t, s))


def table(rows, widths):
    t = Table([[Paragraph(c, TH if i == 0 else T) for c in r] for i, r in enumerate(rows)],
              colWidths=[w * inch for w in widths])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cfcfcb")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), INK), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
    story.extend([t, Spacer(1, 6)])


def fig(name, w):
    from PIL import Image as PImage
    iw, ih = PImage.open(FIG / f"{name}.png").size
    story.append(Image(str(FIG / f"{name}.png"), width=w * inch, height=w * inch * ih / iw))


OK, HALF, NO = ("<font color='#0a7d32'><b>built</b></font>", "<font color='#b86e00'><b>half</b></font>",
                "<font color='#c0392b'><b>not built</b></font>")

P("Calliper: what we sell", H1)
P("Three features on two engines. The essay matrix is the differentiator: it doesn't need outcome data, which the "
  "big platforms have and we don't. Full detail: <b>calliper-feature-build-spec-v1.pdf</b>.")
fig("o1_architecture", 5.9)
story.append(Spacer(1, 6))
table([["Feature", "Tells the counselor", "Status", "Next to build"],
       ["Essay map", "Which draft covers which prompt; words left per school; writing order", NO,
        "LLM-scored prompt matrix + counselor check, then an EMAP command"],
       ["List check", "Real risk of zero admits (as a range); which schools are cheap and worth adding", HALF,
        "Risk part works. 'What to add' needs the matrix + an ADD command"],
       ["Decision updates", "New odds for every pending school after each admit, deferral or reject", OK,
        "Show ranges; calibrate on real outcomes"]], [1.1, 2.75, 0.75, 2.4])

P("How each is calculated", H2)
P("<b>Engine A.</b> One hidden 'application strength' S is shared by every school; each school admits above a cut-off "
  "fitted to its published acceptance rate and SAT band.", B)
P("P(admit<sub>j</sub> | S) = (1 − ω)·Φ((a<sub>j</sub>T + S − c<sub>j</sub>)/σ) + ω·r<sub>j</sub>", M)
P("<b>Engine B.</b> An LLM scores R(p, q): the share of prompt p's work done by an essay for prompt q.", B)
P("New words to add school k to list L:  W(k | L) = Σ<sub>p∈k</sub> w<sub>p</sub>(1 − max<sub>q∈L</sub> R(p, q))", M)
P("<b>List check.</b> Rejections cluster because it's the same application, so zero-admit risk = "
  "∫ Π(1 − P<sub>j</sub>(s)) dF(s), not Π(1 − P<sub>j</sub>). Example list: 9.7% (range 3-11%) vs 1.6% naive. "
  "Worth adding = gain in expected value of the best admit ÷ W(k | L).", B)
P("<b>Decision updates.</b> Bayes' rule: f(s | results) ∝ f(s)·Π P(result | s), then re-price every pending school. "
  "Example: a CMU admit takes Stanford 18% → 50%. Direction is reliable; the size depends on two unmeasured settings, "
  "so show ranges.", B)

P("Build order", H2)
table([["#", "Step", "Size"],
       ["1", "Collect 2026-27 prompts for ~100 schools (CSV + import script); write the scoring rubric", "4-5 days"],
       ["2", "Score all pairs with Claude via the Batch API, 3 runs; load into SimilarityEngine (human > LLM > heuristic)",
        "2-3 days, ~$100"],
       ["3", "Gate: 2-3 counselors blind-score 200 pairs; LLM must beat a constant guess and agree with them about as "
        "well as they agree with each other", "2-3 weeks"],
       ["4", "EMAP (essay plan) and ADD (cheap additions); ranges on UPDT", "1-2 weeks"],
       ["5", "Pilot by hand with 2-3 counselors (send them PDFs), then a web front end", "this cycle"],
       ["6", "Pooled real outcomes → calibrate Decision updates and the risk range", "next cycle"]], [0.3, 5.4, 1.3])
P("<b>Main risk:</b> the matrix costs ~$100 to compute, so it's copyable. The moat is the counselor-checked rubric, "
  "the August refresh, and reuse logs nobody else has.")

SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.5 * inch,
                  bottomMargin=0.5 * inch, title="Calliper: what we sell").build(story)
print(f"wrote {OUT}")
