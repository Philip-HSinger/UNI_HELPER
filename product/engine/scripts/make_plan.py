"""Build product/reports/calliper-product-plan-v1.pdf: one page per feature (how it works, benefit, build, test, sell)."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "reports" / "calliper-product-plan-v1.pdf"
F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", F + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

INK, BLUE = colors.HexColor("#0b0b0b"), colors.HexColor("#2a78d6")
H1 = ParagraphStyle("H1", fontName="DVB", fontSize=15, leading=19, spaceAfter=4, textColor=INK)
LEAD = ParagraphStyle("L", fontName="DV", fontSize=9.5, leading=13.5, spaceAfter=8, textColor=colors.HexColor("#52514e"))
H2 = ParagraphStyle("H2", fontName="DVB", fontSize=10.5, leading=14, spaceBefore=7, spaceAfter=3, textColor=BLUE)
B = ParagraphStyle("B", fontName="DV", fontSize=8.8, leading=12.4, spaceAfter=3)
BUL = ParagraphStyle("BUL", parent=B, leftIndent=11, bulletIndent=2)
M = ParagraphStyle("M", parent=B, backColor=colors.HexColor("#f4f4f2"), borderPadding=4, spaceBefore=2, spaceAfter=6)
T = ParagraphStyle("T", parent=B, fontSize=7.9, leading=10.4, spaceAfter=0)
TH = ParagraphStyle("TH", parent=T, fontName="DVB", textColor=colors.white)
story = []


def P(t, s=B):
    story.append(Paragraph(t, s))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, BUL, bulletText="•"))


def table(rows, widths):
    t = Table([[Paragraph(c, TH if i == 0 else T) for c in r] for i, r in enumerate(rows)],
              colWidths=[w * inch for w in widths])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cfcfcb")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), INK), ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
    story.extend([t, Spacer(1, 4)])


def feature(title, one_liner, how, formula, benefit, build, test, sell):
    P(title, H1)
    P(one_liner, LEAD)
    P("How it works", H2)
    bullets(how)
    if formula:
        P(formula, M)
    P("Benefit", H2)
    bullets(benefit)
    P("How to build", H2)
    table([["#", "Work", "Size"]] + build, [0.42, 5.38, 1.2])
    P("How to test", H2)
    bullets(test)
    P("How to sell", H2)
    bullets(sell)


# ------------------------------------------------------------------------------------------------ 1. Essay map
feature(
    "1. Essay map",
    "Shows which essays a student has already written cover which other schools' prompts, and how many new words each "
    "school really needs, measured from real essays rather than guessed.",
    ["<b>Level 1, prompt vs prompt (before writing):</b> an LLM compares every pair of this cycle's prompts and "
     "estimates the share of content they have in common. It gives a rough plan for the list and a writing order.",
     "<b>Level 2, the student's own essay (after writing):</b> a pipeline adapts the student's actual essay to the new "
     "prompt with minimal edits and counts the words that survive; a grader checks it still answers the prompt. Output: \"62% of your Stanford essay carries over; paragraphs 2-3 "
     "fit, paragraph 1 doesn't.\"",
     "<b>Level 3, what students actually submitted (from next cycle):</b> the text overlap between a student's final "
     "essays across schools, computed on the counselor's computer, with only the numbers shared. It calibrates levels "
     "1 and 2."],
    "New words for school k given list L:  W(k | L) = Σ<sub>p∈k</sub> w<sub>p</sub>·(1 − max<sub>q∈L</sub> R(p, q)),  "
    "R(p, q) = share of words kept (level 2 or 3; level 1 until measured)",
    ["Saves counselor and student hours every August-November, the busiest stretch of the year.",
     "Concrete and easy to check: a counselor can read the mapping and agree with it, with no statistics to trust.",
     "Doesn't depend on outcome data, where the big platforms will always beat us; the measured reuse data is ours alone."],
    [["1", "Collect this cycle's prompts and word limits for ~100 schools (CSV + import script)", "4-5 days, each Aug"],
     ["2", "Level 1: Claude scores all prompt pairs via the Batch API, 3 runs averaged; load into SimilarityEngine", "2-3 days, ~$100"],
     ["3", "Level 2: adapt-and-measure pipeline (adapt → word-level diff → quality grader); EMAP command and one-page plan",
      "1-2 weeks"],
     ["4", "Level 3: OVLP command (local overlap of final essays; exports numbers only) + data terms", "3-4 days"]],
    ["<b>Level 1 vs measured reuse:</b> on pairs with level-3 data, report the error (target: within ±15 points) and "
     "that it beats a constant guess.",
     "<b>Level 2 vs what students did:</b> predicted words kept vs actual overlap in final essays, on 50+ student pairs.",
     "<b>Quality grader:</b> 2-3 counselors blind-rate 50 adapted essays; the grader must agree with them about as "
     "well as they agree with each other.",
     "<b>Demand:</b> pilot counselors log hours per student's supplements with vs without the map."],
    ["<b>Who:</b> independent counselors with 15-60 seniors; later, small counseling firms.",
     "<b>When:</b> August to October, while supplements are being written. This is the lead feature.",
     "<b>Pitch:</b> \"Your seniors are writing the same essay five times. Send me one student's list and I'll show "
     "you which essays cover which schools.\" A demo on their own student does the selling.",
     "<b>Offer:</b> free this cycle for the first 5-10 counselors, in exchange for level-3 reuse numbers; paid "
     "subscription from next August.",
     "<b>Watch out:</b> essays go to an LLM provider, so get consent; output a plan and a diff, never an essay to submit."])
story.append(PageBreak())

# ------------------------------------------------------------------------------------------------ 2. List check
feature(
    "2. List check",
    "Gives the real chance of getting in nowhere, which most tools understate, and names which extra schools would "
    "cost the fewest new words for the biggest gain.",
    ["<b>Real risk:</b> the same application is read at every school, so rejections cluster. The model has one shared "
     "unknown application strength and integrates over it, instead of multiplying each school's odds.",
     "<b>Inputs are facts only:</b> SAT and GPA, each placed against the school's published distribution (College "
     "Scorecard, Common Data Set). No counselor rating. Everything else is an unknown range.",
     "<b>What to add:</b> for each candidate school, the gain in expected value of the best admit (using the family's "
     "own ranking: dream / like / fine), divided by the new words it needs (from Essay map)."],
    "P(no admits) = ∫ Π<sub>j</sub> (1 − P<sub>j</sub>(s)) dF(s), not Π<sub>j</sub> (1 − P<sub>j</sub>);  "
    "rank additions by ΔE[value of best admit] / W(k | L)",
    ["Prevents the worst outcome for a counselor's reputation: a student with zero admits. Example list: 9.7% "
     "(plausible range 3-11%) vs 1.6% when odds are multiplied.",
     "Answers \"should we add one more?\" with \"yes: 300 words, and a real chance\" instead of a gut feeling.",
     "Works on a whole caseload at once, flagging the students at risk."],
    [["1", "Add GPA: Common Data Set C11-C12 per school, fitted like the SAT bands; remove the counselor rating", "1 week"],
     ["2", "ADD command: rank candidate schools by value per new word; preference tiers in the profile", "1-2 days"],
     ["3", "Show risk and gains as ranges; ROSTER column 'best cheap addition'", "1-2 days"],
     ["4", "Family-facing brief in words (low / moderate / high), no percentages", "exists (BRIEF family)"]],
    ["<b>This cycle:</b> freeze every pilot student's forecast in the tamper-evident ledger (LEDGER) before results; "
     "grade it in spring (SCORE).",
     "<b>Risk range:</b> across pooled students, the share with zero admits should fall inside the predicted ranges; "
     "multiplied odds should be shown to understate it.",
     "<b>GPA:</b> backtest on partner data that scores + GPA beats scores only.",
     "<b>Additions:</b> track how many suggested additions were applied to, and how many were admitted."],
    ["<b>Who:</b> the same counselors, plus school counselors with large caseloads (the caseload screen).",
     "<b>When:</b> September to November, when lists are finalized.",
     "<b>Pitch:</b> \"Most tools multiply odds, which hides how often strong students get in nowhere. This shows the "
     "real risk and the cheapest fix.\" Show their own student's list, both numbers side by side.",
     "<b>Sold as:</b> part of the same subscription as Essay map, not separately; it's where both engines meet."])
story.append(PageBreak())

# ------------------------------------------------------------------------------------------------ 3. Decision updates
feature(
    "3. Decision updates",
    "Recalculates the odds at every pending school each time an admit, deferral or reject arrives, using only "
    "verifiable facts (SAT, GPA) plus the real decisions.",
    ["Before results, the model doesn't know how strong the rest of the application is. Each decision is evidence: an "
     "admit says it's reading well, a reject says less so, a deferral says \"in between\".",
     "Bayes' rule combines all results into one updated belief about the application, and every pending school is "
     "re-priced from it. Output is always a range.",
     "Example: a CMU admit takes Stanford from 18% to about 50%. The direction is reliable; the size depends on two "
     "settings that real outcomes must calibrate."],
    "f(s | results) ∝ f(s) · Π<sub>k</sub> P(result<sub>k</sub> | s);   P(admit<sub>j</sub> | results) = "
    "∫ P<sub>j</sub>(s) f(s | results) ds",
    ["Mid-December decisions are urgent: after an early admit, are six more reach applications worth writing? After an "
     "early reject, add two safer schools before 1 January? Where to use Early Decision II?",
     "Keeps the product in use after essays are done, through to deposit day in May.",
     "Easy to explain to a family: \"getting into CMU tells us your application is reading well\"."],
    [["1", "Ranges on every updated number (sweep the two unmeasured settings)", "1 day"],
     ["2", "Early rounds modelled properly: early admit rates (Common Data Set) and what a deferral means", "1 week"],
     ["3", "Outcome CSV with round and year; data terms for partners (draft exists)", "2-3 days"],
     ["4", "Calibrate the two settings on pooled partner outcomes (FIT exists)", "2-3 days once data arrives"]],
    ["<b>Already done (simulated students):</b> using a student's other decisions cut prediction error by 18-24%.",
     "<b>Real test:</b> on pooled partner outcomes, held-out students' odds with updates must beat odds without, and "
     "80% ranges must contain about 80% of results.",
     "<b>Sample size:</b> simulate first to find how many students pin down the two settings; recruit partners to "
     "that number (likely a few hundred students)."],
    ["<b>Who:</b> existing subscribers (it's the retention feature), and families of pilot students via the counselor.",
     "<b>When:</b> mid-December to April; send a short note the day early results come out.",
     "<b>Pitch:</b> \"Early results just came in. Here's what they mean for every school still pending, before the 1 "
     "January deadlines.\"",
     "<b>Data loop:</b> each partner who shares outcomes makes the updates more accurate for everyone; that pooled data "
     "is the long-term moat."])

SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.5 * inch,
                  bottomMargin=0.45 * inch, title="Calliper product plan").build(story)
print(f"wrote {OUT}")
