"""Shared paths and helpers for the 10-school demo pipeline."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW, VERIFY, SCORES, OUT = ROOT / "data" / "raw", ROOT / "data" / "verify", ROOT / "data" / "scores", ROOT / "outputs"
TOOLKIT = ROOT.parent / "toolkit"

SCHOOLS = [  # order used in every table
    ("tufts", "Tufts"),
    ("upenn", "Penn"),
    ("rice", "Rice"),
    ("emory", "Emory"),
    ("boston-college", "Boston College"),
    ("boston-university", "Boston University"),
    ("villanova", "Villanova"),
    ("fordham-university", "Fordham"),
    ("northeastern", "Northeastern"),
    ("wesleyan-university", "Wesleyan"),
    ("college-of-the-holy-cross", "Holy Cross"),
    ("fairfield-university", "Fairfield"),
    ("university-of-massachusetts-amherst", "UMass Amherst"),
    ("university-of-rhode-island", "URI"),
]
SHORT = dict(SCHOOLS)
IDS = [s for s, _ in SCHOOLS]
# The example student, John Smith (fictional): the eight schools he applies to, and six he has not considered.
LIST = ["tufts", "upenn", "rice", "emory", "boston-college", "boston-university", "villanova", "fordham-university"]
CANDIDATES = ["university-of-massachusetts-amherst", "university-of-rhode-island", "college-of-the-holy-cross",
              "fairfield-university", "northeastern", "wesleyan-university"]
SUBMITTED = {"tufts", "fordham-university"}  # Early Decision / Early Action essays already sent (deadlines Nov 1-8)
# The example student: a domestic, arts-and-sciences applicant, not applying to an honors college or a
# specialised program. Prompts that apply only to other applicants are left out (listed in the annotated report).
NOT_ELIGIBLE = {
    "tufts-3": "Tufts School of Engineering only", "tufts-4": "Tufts BFA only", "tufts-5": "Tufts combined BFA degree only",
    "boston-college-5": "BC Human-Centered Engineering only",
    "boston-university-2": "BU Kilachand Honors College only", "boston-university-3": "BU Kilachand Honors College only",
    "university-of-massachusetts-amherst-3": "UMass Commonwealth Honors College applicants only",
    "university-of-rhode-island-1": "URI Nursing only", "university-of-rhode-island-2": "URI PharmD only",
    "university-of-rhode-island-3": "URI Honors only", "university-of-rhode-island-4": "URI Talent Development only",
    "wesleyan-university-1": "Wesleyan international applicants only",
}
# Optional essays the student writes anyway (most counselors advise it); key = (school_id, choose group)
WRITE_OPTIONAL = {("fordham-university", "A")}
DEFAULT_LIMIT = 250  # words assumed when a prompt states no limit (flagged in the annotated report)


def load(path):
    return json.loads(Path(path).read_text())


def save(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False))


def limit_words(p):
    """Word budget of a prompt: stated word limit, else characters / 6, else the default."""
    if p.get("word_limit"):
        return int(p["word_limit"])
    if p.get("char_limit"):
        return max(25, round(int(p["char_limit"]) / 6))
    return DEFAULT_LIMIT


def length_factor(lq, lp):
    """Share of prompt p's words an essay written for q (limit lq) can supply: min(1, lq / lp)."""
    return min(1.0, lq / lp)
