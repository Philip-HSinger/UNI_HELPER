"""Build toolkit/data/catalog.json + toolkit/data/similarity.csv from the repo's curated sources.

Sources (both already in this repo):
  supabase/seed_source.schools.json   - the 19-school seed
  supabase/update_five_schools.sql    - researched 2026-27 corrections (MIT, Princeton, Stanford,
                                        Georgia Tech, Purdue) + the first curated similarity pairs

Prompt ids use the exact same slug scheme as scripts/generate_seed_sql.py, so a curated
prompt_similarity export from Supabase lines up with this catalog id-for-id.

Re-run after editing either source:  python toolkit/scripts/build_catalog.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from generate_seed_sql import parse_word_limit, slugify  # noqa: E402

SEED = ROOT / "supabase" / "seed_source.schools.json"
UPDATE_SQL = ROOT / "supabase" / "update_five_schools.sql"
OUT_DIR = ROOT / "toolkit" / "data"

SQL_STR = r"'((?:[^']|'')*)'"


def unquote(s: str) -> str:
    return s.replace("''", "'")


def parse_value(raw: str):
    raw = raw.strip()
    if raw.lower() == "null":
        return None
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    if raw.startswith("'"):
        return unquote(raw[1:-1])
    return float(raw) if "." in raw else int(raw)


def parse_updates(sql: str) -> dict[str, dict]:
    """`update schools set a = 1, b = 'x' where id = 'mit';` -> {'mit': {'a': 1, 'b': 'x'}}"""
    updates: dict[str, dict] = {}
    for body, sid in re.findall(r"update schools set(.*?)where id = '([^']+)';", sql, re.S | re.I):
        fields = updates.setdefault(sid, {})
        for key, val in re.findall(r"(\w+)\s*=\s*('(?:[^']|'')*'|[\w.]+)", body):
            fields[key] = parse_value(val)
    return updates


def parse_prompt_inserts(sql: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    row_re = re.compile(rf"\(\s*{SQL_STR}\s*,\s*{SQL_STR}\s*,\s*{SQL_STR}\s*,\s*(null|\d+)\s*,\s*(\d+)\s*\)", re.I)
    for block in re.findall(r"insert into prompts .*? values(.*?);", sql, re.S | re.I):
        for pid, sid, text, wl, order in row_re.findall(block):
            out.setdefault(sid, []).append(
                {"id": pid, "text": unquote(text), "wordLimit": None if wl.lower() == "null" else int(wl), "order": int(order)}
            )
    for rows in out.values():
        rows.sort(key=lambda r: r["order"])
        for r in rows:
            del r["order"]
    return out


def parse_similarity(sql: str) -> list[tuple[str, str, float]]:
    rows = []
    for block in re.findall(r"insert into prompt_similarity .*? values(.*?)on conflict", sql, re.S | re.I):
        for a, b, score in re.findall(rf"\(\s*{SQL_STR}\s*,\s*{SQL_STR}\s*,\s*([\d.]+)\s*\)", block):
            rows.append((unquote(a), unquote(b), float(score)))
    return rows


SQL_TO_JSON = {
    "name": "name", "platform": "platform", "test_optional": "testOptional",
    "english_p25": "englishP25", "english_p50": "englishP50", "english_p75": "englishP75",
    "math_p25": "mathP25", "math_p50": "mathP50", "math_p75": "mathP75",
    "difficulty": "difficulty", "importance": "importance", "acceptance_rate": "acceptanceRate",
    "us_news_rank": "usNewsRank",
}


def main() -> None:
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    sql = UPDATE_SQL.read_text(encoding="utf-8")
    updates = parse_updates(sql)
    replaced_prompts = parse_prompt_inserts(sql)
    cleared = set(re.findall(r"'([\w-]+)'", re.search(r"delete from prompts where school_id in \((.*?)\)", sql).group(1)))

    schools = []
    for s in seed:
        school = {k: v for k, v in s.items() if k != "prompts"}
        school["usNewsRank"] = s.get("usNewsRank")
        used: set[str] = set()
        prompts = []
        for p in s["prompts"]:
            base = f"{s['id']}--{slugify(p['text'])}"
            pid, n = base, 2
            while pid in used:
                pid, n = f"{base}-{n}", n + 1
            used.add(pid)
            prompts.append({"id": pid, "text": p["text"], "wordLimit": parse_word_limit(p["text"])})
        if s["id"] in cleared:
            prompts = replaced_prompts.get(s["id"], [])
        school["prompts"] = prompts
        provenance = "seed"
        for col, val in updates.get(s["id"], {}).items():
            if col in SQL_TO_JSON:
                school[SQL_TO_JSON[col]] = val
                provenance = "researched-2026-27"
        school["provenance"] = provenance
        schools.append(school)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "catalog.json").write_text(json.dumps(schools, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with open(OUT_DIR / "similarity.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["prompt_a_id", "prompt_b_id", "score"])
        for row in parse_similarity(sql):
            w.writerow(row)
    print(f"wrote {len(schools)} schools, {sum(len(s['prompts']) for s in schools)} prompts, "
          f"{len(parse_similarity(sql))} curated similarity pairs to {OUT_DIR}")


if __name__ == "__main__":
    main()
