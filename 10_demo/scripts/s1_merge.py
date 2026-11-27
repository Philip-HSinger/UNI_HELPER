"""Step 1: merge the agents' raw files into data/prompts.json and data/schools.json, and list every cross-school
prompt pair for the scorers (data/scores/pairs.json). Run after the research (and verification) agents finish."""
import itertools

from common import IDS, RAW, ROOT, SCORES, SHORT, limit_words, load, save

prompts, schools = [], {}
for sid in IDS:
    d = load(RAW / f"prompts_{sid}.json")
    for p in d.get("prompts", []):
        p = dict(p, school_id=sid, school=SHORT[sid], limit=limit_words(p),
                 limit_assumed=not (p.get("word_limit") or p.get("char_limit")))
        prompts.append(p)
    schools[sid] = {"school_id": sid, "school": SHORT[sid], "cycle": d.get("cycle"), "no_supplement": d.get("no_supplement"),
                    "prompt_notes": d.get("notes", ""), "prompt_sources": d.get("sources", [])}

stats = []
for f in sorted(RAW.glob("stats_batch*.json")):
    stats += load(f)
for s in stats:
    if s["school_id"] in schools:
        schools[s["school_id"]].update(stats=s)
missing = [sid for sid in IDS if "stats" not in schools[sid]]
assert not missing, f"no stats for {missing}"

save(ROOT / "data" / "prompts.json", prompts)
save(ROOT / "data" / "schools.json", [schools[s] for s in IDS])

pairs = []
for a, b in itertools.combinations(prompts, 2):
    if a["school_id"] == b["school_id"]:
        continue
    pairs.append({"pair": f"{a['id']}|{b['id']}",
                  "A": {"id": a["id"], "school": a["school"], "limit_words": a["limit"], "text": a["text"]},
                  "B": {"id": b["id"], "school": b["school"], "limit_words": b["limit"], "text": b["text"]}})
save(SCORES / "pairs.json", pairs)
print(f"{len(prompts)} prompts, {len(pairs)} cross-school pairs")
for sid in IDS:
    n = sum(p["school_id"] == sid for p in prompts)
    print(f"  {SHORT[sid]:15s} {n} prompts")
