"""Build the two documents for the pitch simulation:
  reports/UNIMATH_market_analysis.pdf  - would this sell, to whom, for what, at what price
  reports/UNIMATH_offer.pdf            - the offer a prospect receives (truthful about what exists today)
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
F = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", F + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", F + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")
INK, BLUE, GREY = colors.HexColor("#0b0b0b"), colors.HexColor("#2a78d6"), colors.HexColor("#52514e")
H1 = ParagraphStyle("H1", fontName="DVB", fontSize=15, leading=19, spaceAfter=4, textColor=INK)
LEAD = ParagraphStyle("L", fontName="DV", fontSize=9.5, leading=13.5, spaceAfter=6, textColor=GREY)
H2 = ParagraphStyle("H2", fontName="DVB", fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=3, textColor=BLUE)
B = ParagraphStyle("B", fontName="DV", fontSize=8.8, leading=12.4, spaceAfter=3)
BUL = ParagraphStyle("BUL", parent=B, leftIndent=11, bulletIndent=2)
BOX = ParagraphStyle("BOX", parent=B, backColor=colors.HexColor("#eef4fc"), borderColor=BLUE, borderWidth=0.6,
                     borderPadding=6, spaceBefore=4, spaceAfter=8)
SM = ParagraphStyle("SM", parent=B, fontSize=7, leading=9.2, textColor=GREY)
T = ParagraphStyle("T", parent=B, fontSize=7.8, leading=10.3, spaceAfter=0)
TH = ParagraphStyle("TH", parent=T, fontName="DVB", textColor=colors.white)


class Doc:
    def __init__(self):
        self.s = []

    def p(self, t, st=B):
        self.s.append(Paragraph(t, st))

    def bullets(self, items):
        for it in items:
            self.s.append(Paragraph(it, BUL, bulletText="•"))

    def table(self, rows, widths):
        t = Table([[Paragraph(c, TH if i == 0 else T) for c in r] for i, r in enumerate(rows)],
                  colWidths=[w * inch for w in widths], repeatRows=1)
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cfcfcb")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, 0), INK),
                               ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]))
        self.s.extend([t, Spacer(1, 5)])

    def build(self, path, title):
        SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                          topMargin=0.55 * inch, bottomMargin=0.55 * inch, title=title).build(self.s)
        print(f"wrote {path}")


# ================================================================================================ market analysis
m = Doc()
m.p("UNIMATH: market analysis", H1)
m.p("Would this sell, to whom, for what, and for how much. Internal; figures are cited at the end and some are "
    "estimates or old. November 2026.", LEAD)
m.p("<b>Verdict:</b> sellable as a low-price tool to independent counselors, mainly for Essay map, but that market "
    "alone is small (roughly $0.1-0.6M a year). A real business needs either a platform licence (counselor CRMs, "
    "essay-coaching companies) or the pooled data becoming the product. Essay reuse planning already has early "
    "competitors, so the edge must be <i>measured</i> reuse, not the idea of reuse.", BOX)

m.p("The market in numbers", H2)
m.table([["Fact", "Number", "Why it matters"],
         ["Full-time independent counselors (US)", "~6,000-10,000, plus 10-15k part-time", "Core buyer pool"],
         ["Typical comprehensive package", "mean $6,450 (range $4,000-7,500), 2022", "$390/yr is ~6% of one client"],
         ["Mean hourly rate", "$230 (2022)", "Value of hours saved"],
         ["Common App first-year applicants, 2025-26", "1.53 million", "Ceiling for families-direct"],
         ["Applications per applicant", "7.06 (up from 6.79)", "More supplements each year: the pain grows"],
         ["Public school student-to-counselor ratio", "372 : 1 (2024-25)", "School counselors have no time for a new tool"],
         ["Counselor CRM pricing (e.g. CollegePlannerPro)", "from ~$69/month", "Anchor for what counselors pay for software"]],
        [2.4, 2.1, 2.5])

m.p("Who would buy, and for what", H2)
m.table([["Segment", "Cares most about", "Feature that sells", "Likely to pay?", "Price they'd accept"],
         ["Solo independent counselor (15-60 seniors)", "Hours in Aug-Nov; families blindsided by zero admits",
          "Essay map, then List check", "<b>Yes, if</b> the demo on their own student is convincing", "$200-500/yr"],
         ["Counseling firm (5-50 counselors)", "Consistency across staff; something to show parents",
          "All three + caseload screen", "Maybe; slower, wants references", "$1-5k/yr"],
         ["Private school counselor", "Long lists, demanding parents", "List check, Decision updates",
          "Maybe; school budget cycle", "$500-1,500/yr"],
         ["Public school counselor", "Hundreds of students, little time", "Caseload risk screen",
          "Unlikely; district already pays for Naviance/Scoir", "Near zero"],
         ["Counselor CRM / essay-coaching company", "Differentiating features, retention",
          "Essay map engine (licence/API)", "Possible; biggest upside, longest sales cycle", "$10-50k/yr"],
         ["Families direct (quantitative parents)", "Their own child's odds and workload", "Essay map, Decision updates",
          "Some, but crowded with free AI tools", "$20-100 one-off"]],
        [1.35, 1.6, 1.25, 1.55, 1.05])

m.p("Competition", H2)
m.table([["Who", "What they offer", "Our difference"],
         ["Naviance / Scoir scattergrams", "Past applicants from the same high school", "No probabilities, no linked "
          "risk, no essays; schools only"],
         ["CollegeVine, College Kickstart", "Free per-school chances; list grades", "Unpublished, independent-style "
          "odds that understate zero-admit risk"],
         ["Admittedly Essay Stack Planner", "Students group prompts by topic to reuse essays", "Manual grouping; no "
          "measured words-left or school-by-school coverage"],
         ["CollegeApply AI and other AI essay tools", "Drafting/feedback; some suggest reuse", "No published "
          "method; we measure carry-over from the student's own essay"],
         ["Counselor's own memory + spreadsheets", "Free, trusted", "Slow, redone every August, not measured"]],
        [1.8, 2.3, 2.9])

m.p("Why someone would buy", H2)
m.bullets(["<b>Time:</b> if Essay map saves 1-2 hours per student, a counselor with 20 seniors at $230/hour saves "
           "$4,600-9,200 a season for a $390 tool. <i>The hours saved are an assumption; the pilot must measure them.</i>",
           "<b>Risk:</b> a student with zero admits is the worst outcome for a counselor's reputation, and multiplied "
           "odds hide it.",
           "<b>December:</b> early results force decisions within two weeks; nothing on the market re-prices a list.",
           "<b>Facts-only inputs:</b> SAT, GPA and real decisions; no opaque scores."])
m.p("Why they might not", H2)
m.bullets(["Experienced counselors may feel they already know the overlaps for the top 20 schools.",
           "Free AI tools are 'good enough' for many; reuse planning already exists in competitors.",
           "No track record yet: all accuracy evidence is from simulated students; solo founder; no references.",
           "Wariness of AI near student essays (schools' AI policies).",
           "Seasonal: buying decisions cluster in summer; outside Aug-Dec there's little urgency.",
           "Not built yet: Essay map and GPA input are in development; a command-line tool won't sell to counselors."])

m.p("Market size (rough, bottom-up)", H2)
m.table([["Scenario", "Customers", "Revenue / year"],
         ["Solo counselors, 5% of ~8,000 at $390", "400", "~$156k"],
         ["Solo counselors, 20% at $390", "1,600", "~$624k"],
         ["Plus 20 firms at $3k and 3 platform licences at $25k", "23", "+ ~$135k"],
         ["Families direct, 0.1% of 1.53M applicants at $49", "~1,500", "~$75k"]],
        [3.6, 1.2, 2.2])
m.p("What would make it a bigger business: a platform licence, or the pooled measured-reuse and outcome data "
    "becoming something nobody else has.")

m.p("What the pitch simulation should test", H2)
m.bullets(["Do solo counselors reply to an essay-first pitch more than a risk-first or a December-updates pitch?",
           "Is $390/yr questioned? At what price does the objection change from 'price' to 'proof'?",
           "Do counselors agree to share reuse numbers and outcomes in exchange for a free year?",
           "Which objection is fatal: no track record, AI wariness, or 'I already know this'?"])
m.p("Sources: IECA State of the Profession 2022 (iecaonline.com) and IECA profession FAQ; Common App End of Season "
    "Report 2025-26 (commonapp.org); ASCA student-to-counselor ratios 2024-25 (schoolcounselor.org); Admittedly help "
    "centre, Essay Stack Planner; CollegeApply AI on Product Hunt; CollegePlannerPro plans page; Applerouth, citing IECA "
    "(lower count: 6,000+ full-time). Counselor numbers differ between IECA sources; fee data is from 2022. Segment "
    "prices and adoption rates are estimates, not survey results.", SM)
m.build(ROOT / "reports" / "UNIMATH_market_analysis.pdf", "UNIMATH market analysis")

# ================================================================================================ offer
o = Doc()
o.p("Calliper", H1)
o.p("Admissions analytics for college counselors, built by Philip, an electrical engineering student at Brown. "
    "Facts in, measured answers out.", LEAD)
o.p("Three things for each student's list:", B)
o.table([["", "What you get", "Available"],
         ["<b>Decision updates</b>", "When an early result arrives, new odds for every school still pending, as a "
          "range. Built for mid-December, when you have two weeks before 1 January deadlines.", "<b>Now</b>"],
         ["<b>List check</b>", "The real chance of no admits. Most tools multiply odds as if schools decided "
          "independently, which understates it. In one example list: about 10% with the default "
          "assumptions (3-11% across all plausible ones), against 1.6% when odds are multiplied. Plus which schools are "
          "cheap and worth adding.", "Risk check <b>now</b>; 'what to add' with Essay map"],
         ["<b>Essay map</b>", "Which essays your student has already written cover which other schools' prompts, and "
          "how many new words each school really needs, measured from the student's own essays.",
          "<b>Pilot from August 2027</b>, for your juniors"]],
        [1.2, 4.5, 1.3])

o.p("How it works", H2)
o.bullets(["<b>Facts only:</b> SAT (GPA being added), the schools' published data, and real decisions. No made-up "
           "ratings of your students.",
           "<b>Linked odds:</b> the same application is read at every school, so the model treats decisions as linked. "
           "That's why it shows a higher risk of no admits, and why one early result changes the other odds.",
           "<b>Measured essay reuse:</b> the share of a student's essay that actually carries over to another prompt, "
           "checked by a separate grader, not a guess.",
           "<b>Private:</b> no student names needed. Essays are only used with the family's consent, and you get a plan, "
           "never a rewritten essay to submit."])

o.p("Where it stands", H2)
o.bullets(["New this cycle, so it's free for the first counselors while it's checked against real results. A detailed "
           "methods write-up is available on request.",
           "During the pilot I run it for you and send a one-page PDF per student. No software to install."])

o.p("The founding-counselor pilot", H2)
o.table([["You get", "In return"],
         ["Decision updates and the list risk check for your current seniors, this December, free",
          "Your students' decisions this spring, without names, so the odds can be checked against real results"],
         ["Essay map for your juniors from August 2027, free for the 2027-28 cycle",
          "With consent: which essays each student reused for which school (numbers only), to measure reuse"],
         ["A say in what gets built; your name on the track record if you want it", "Two short feedback calls"]],
        [3.5, 3.5])
o.p("After the pilot (introductory prices): <b>$390 per counselor per year</b>, or <b>$1,500 per school or firm</b> (up to 10 counselors). "
    "Founding counselors keep these prices. Platforms wanting the engine: let's talk.")

o.p("What to do next", H2)
o.p("Send one current senior's list (scores and schools, no name) and any early results you already have. You'll get "
    "back their updated odds and the list's real risk of no admits within two days.", BOX)
o.build(ROOT / "reports" / "Calliper_overview.pdf", "Calliper overview")
