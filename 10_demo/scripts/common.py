"""Shared paths and helpers for the 10-school demo pipeline."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW, VERIFY, SCORES, OUT = ROOT / "data" / "raw", ROOT / "data" / "verify", ROOT / "data" / "scores", ROOT / "outputs"
TOOLKIT = ROOT.parent / "toolkit"

SCHOOLS = [  # order used in every table
    ("tufts", "Tufts"),
    ("boston-college", "Boston College"),
    ("boston-university", "Boston University"),
    ("northeastern", "Northeastern"),
    ("wesleyan-university", "Wesleyan"),
    ("college-of-the-holy-cross", "Holy Cross"),
    ("fordham-university", "Fordham"),
    ("fairfield-university", "Fairfield"),
    ("university-of-massachusetts-amherst", "UMass Amherst"),
    ("university-of-rhode-island", "URI"),
]
SHORT = dict(SCHOOLS)
IDS = [s for s, _ in SCHOOLS]
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
