"""Fetch admissions data for every large 4-year school from the US Dept. of Education's College Scorecard API
(api.data.gov; DEMO_KEY works for a handful of requests, or set SCORECARD_API_KEY) into data/scorecard_raw.json.

Scorecard's SAT fields are 25th/50th/75th percentiles of *enrolled* first-years (same population as CDS C9) and
the overall admission rate (IPEDS). It has no supplement prompts and no CDS "importance of testing" label; the
build step maps Scorecard's test-requirement code to an importance *proxy* and flags it in provenance.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "scorecard_raw.json"
BASE = "https://api.data.gov/ed/collegescorecard/v1/schools"
FIELDS = ["id", "school.name", "school.state", "latest.student.size", "latest.admissions.admission_rate.overall",
          "latest.admissions.test_requirements"] + [
    f"latest.admissions.sat_scores.{q}.{s}" for q in ("25th_percentile", "midpoint", "75th_percentile")
    for s in ("critical_reading", "math")]


def get(page: int, key: str) -> dict:
    q = {"api_key": key, "fields": ",".join(FIELDS), "per_page": 100, "page": page,
         "school.degrees_awarded.predominant": 3, "latest.student.size__range": "2500..",
         "latest.admissions.sat_scores.midpoint.math__range": "200..800", "sort": "latest.student.size:desc"}
    url = BASE + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read())


def main():
    """Resumable: pages already in OUT are kept; on HTTP 429 (DEMO_KEY allows ~10 requests/hour) it saves and stops."""
    import urllib.error
    key = os.environ.get("SCORECARD_API_KEY", "DEMO_KEY")
    state = json.loads(OUT.read_text()) if OUT.exists() else {"results": [], "pages_done": [], "total": None}
    state.setdefault("pages_done", [])
    page = max(state["pages_done"], default=-1) + 1
    while state["total"] is None or len(state["results"]) < state["total"]:
        try:
            d = get(page, key)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"rate-limited at page {page}; saved {len(state['results'])}. Re-run later (or set SCORECARD_API_KEY).")
                break
            raise
        if not d["results"]:
            break
        state["results"] += d["results"]
        state["total"] = d["metadata"]["total"]
        state["pages_done"].append(page)
        state.update(source="College Scorecard API (api.data.gov), latest release", fetched=time.strftime("%Y-%m-%d"))
        OUT.write_text(json.dumps(state, indent=0))
        print(f"page {page}: {len(state['results'])}/{state['total']}")
        page += 1
        time.sleep(1)
    print("have", len(state["results"]), "of", state["total"])


if __name__ == "__main__":
    main()
