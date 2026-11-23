"""Catalog loading + data-quality validation."""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
CATALOG = DATA / "catalog.json"
SIMILARITY = DATA / "similarity.csv"
IMPORTANCE = {"Very Important", "Important", "Considered", "Not Considered"}


def load_catalog(path: str | Path | None = None, overrides: dict | None = None) -> list[dict]:
    schools = json.loads(Path(path or CATALOG).read_text(encoding="utf-8"))
    for s in schools:
        s.update((overrides or {}).get(s["id"], {}))
    return schools


def validate(schools: list[dict]) -> list[tuple[str, str, str]]:
    """(severity, school, message). ERROR = model can't use it; WARN = result less reliable."""
    issues = []
    for s in schools:
        sid = s["id"]
        for sec in ("english", "math"):
            q = [s.get(f"{sec}P{k}") for k in (25, 50, 75)]
            if None in q:
                issues.append(("ERROR", sid, f"{sec} band missing"))
            elif not (200 <= q[0] <= q[1] <= q[2] <= 800):
                issues.append(("ERROR", sid, f"{sec} band invalid {q}"))
            elif q[2] == 800:
                issues.append(("WARN", sid, f"{sec} band censored at 800 ({q}); upper tail from prior"))
        r = s.get("acceptanceRate")
        if r is None:
            issues.append(("ERROR", sid, "acceptance rate missing: chances not computable"))
        elif not 0 < r < 1:
            issues.append(("ERROR", sid, f"acceptance rate {r} out of (0,1)"))
        if s.get("importance") not in IMPORTANCE:
            issues.append(("ERROR", sid, f"importance '{s.get('importance')}' not a CDS label"))
        for p in s.get("prompts", []):
            wl = p.get("wordLimit")
            if wl is None and "optional" not in p["text"].lower() and "graded" not in p["text"].lower():
                issues.append(("WARN", sid, f"prompt '{p['id']}' has no word limit (assumed 250)"))
            elif wl is not None and wl < 25:
                issues.append(("WARN", sid, f"prompt '{p['id']}' word limit {wl} looks mis-parsed"))
        if s.get("provenance") != "researched-2026-27":
            issues.append(("WARN", sid, "data not re-verified for the 2026-27 cycle"))
    return issues
