"""Mechanical helpers for the buyer simulation. The orchestrator uses these so that:
  - the seller only ever sees public profiles (public_profiles.json),
  - each buyer's inbox is built the same way (our email at a seeded-random position among realistic distractors),
  - every message in every thread is recorded verbatim in transcripts/<id>.md.

Usage:
  python sim.py public                         -> writes public_profiles.json
  python sim.py card <id>                      -> prints the buyer's private card (persona minus nothing; for the buyer only)
  python sim.py inbox <id> <stage>             -> prints an inbox preview (stage: t0 | followup)
  python sim.py email <id> [followup]          -> prints our full email (emails/<id>.md or emails/<id>_followup.md)
  python sim.py log <id> <speaker> <file|->    -> appends a message to transcripts/<id>.md
  python sim.py outcome <id> <OUTCOME> <note>  -> records the final outcome in outcomes.json
"""
import json
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PERSONAS = json.loads((HERE / "personas.json").read_text()) if (HERE / "personas.json").exists() else []
BY_ID = {p["id"]: p for p in PERSONAS}
SENDER = "UNIMATH"


def preview(text: str, n: int = 140) -> str:
    body = " ".join(text.split())
    return body[:n] + ("…" if len(body) > n else "")


def our_email(pid: str, followup: bool = False) -> tuple[str, str]:
    """Returns (subject, body) from emails/<id>[_followup].md whose first line is 'Subject: ...'."""
    f = HERE / "emails" / f"{pid}{'_followup' if followup else ''}.md"
    lines = f.read_text().strip().splitlines()
    subject = lines[0].removeprefix("Subject:").strip()
    return subject, "\n".join(lines[1:]).strip()


def inbox(pid: str, stage: str) -> str:
    p = BY_ID[pid]
    rng = random.Random(f"{pid}-{stage}")
    # a fresh, full-size inbox each week (never shrink it: that would make our email stand out)
    items = list(p["inbox_distractors_followup"] if stage == "followup" else p["inbox_distractors"])
    rng.shuffle(items)
    subj, body = our_email(pid, followup=(stage == "followup"))
    ours = {"from": SENDER, "subject": subj, "preview": preview(body)}
    items.insert(rng.randrange(len(items) + 1), ours)
    out = [f"INBOX ({'one week later' if stage == 'followup' else 'this morning'}) - {len(items)} unread shown, "
           f"newest first. Your usual volume is about {p['inbox_habits']['emails_per_day']} emails a day."]
    for i, e in enumerate(items, 1):
        out.append(f"{i:>2}. FROM: {e['from']}\n    SUBJECT: {e['subject']}\n    PREVIEW: {e['preview']}")
    return "\n".join(out)


def card(pid: str) -> str:
    p = BY_ID[pid]
    # Buyers see only the sanitized view. likely_objections / what_would_make_them_buy stay manager-only predictions.
    return json.dumps({"you_are": p["public_profile"], "private": p["private_buyer_view"], "inbox_habits": p["inbox_habits"]},
                      indent=1)


LEAK = re.compile(r"unimath|simulat|solo.?founder|soc ?2|\bsso\b|no (paying|customers|references)|correlated|zero.?admit|"
                  r"prompt pairs|methods manual|command.?line|\bcli\b|python|scorecard|\$390|\$1,?500|founding|bayesian|"
                  r"bktst|families direct|not sold|engine|licen[cs]e|\bapi\b|the (product|tool)", re.I)


def lint() -> int:
    """Pre-launch check (manager change 1): no product knowledge may appear in anything a buyer sees except our email."""
    hits = 0
    for p in PERSONAS:
        seen = card(p["id"]) + json.dumps(p["inbox_distractors"]) + json.dumps(p.get("inbox_distractors_followup", []))
        for m in LEAK.finditer(seen):
            hits += 1
            print(p["id"], repr(seen[max(0, m.start() - 40): m.end() + 40]))
    return hits


def log(pid: str, speaker: str, src: str) -> None:
    text = sys.stdin.read() if src == "-" else Path(src).read_text()
    t = HERE / "transcripts" / f"{pid}.md"
    if not t.exists():
        p = BY_ID[pid]
        t.write_text(f"# Transcript: {pid}\n\nSegment: {p['segment']} | {p['public_profile']['title']}, "
                     f"{p['public_profile']['organization']}\n\n")
    with t.open("a") as f:
        f.write(f"## {speaker}\n\n{text.strip()}\n\n")


def outcome(pid: str, oc: str, note: str) -> None:
    f = HERE / "outcomes.json"
    d = json.loads(f.read_text()) if f.exists() else {}
    d[pid] = {"segment": BY_ID[pid]["segment"], "outcome": oc, "note": note}
    f.write_text(json.dumps(d, indent=1))


if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    if cmd == "public":
        pub = [{"id": p["id"], **p["public_profile"]} for p in PERSONAS]
        (HERE / "public_profiles.json").write_text(json.dumps(pub, indent=1))
        print(f"wrote public_profiles.json ({len(pub)})")
    elif cmd == "card":
        print(card(a[0]))
    elif cmd == "inbox":
        print(inbox(a[0], a[1]))
    elif cmd == "email":
        s, b = our_email(a[0], followup=len(a) > 1)
        print(f"FROM: {SENDER}\nSUBJECT: {s}\n\n{b}")
    elif cmd == "log":
        log(*a)
    elif cmd == "packet":
        print(packet(a[0], a[1], a[2] if len(a) > 2 else None))
    elif cmd == "answer":
        f = answer(a[0], a[1])
        m = _meta()[a[0]]
        if "OPEN" in f:
            idx = m["idx_t0" if a[1] == "t0" else "idx_followup"]
            opened = idx in [int(x) for x in __import__("re").findall(r"\d+", f["OPEN"])]
            print(f"OURS_OPENED={opened} (ours=#{idx})")
        for k in ("ACTION", "DECISION_IF_ANY", "FINAL", "WOULD_PAY", "TOP_OBJECTION"):
            if k in f:
                print(f"{k}: {f[k].strip()}")
        if f.get("ACTION", "").strip().upper().startswith(("REPLY", "FORWARD")):
            print("MESSAGE:\n" + f.get("MESSAGE", "").strip())
    elif cmd == "lint":
        n = lint()
        print(f"lint hits: {n}")
        sys.exit(1 if n else 0)
    elif cmd == "outcome":
        outcome(a[0], a[1], " ".join(a[2:]))


# ---------------------------------------------------------------------------------------------- buyer packets
# Each buyer gets a private folder /tmp/mr/<random token>/ holding only its own stage prompts and its answers.
# The orchestrator-only map (persona -> token, index of our email in each inbox) lives in /tmp/mr/_meta.json.
import secrets  # noqa: E402

MR = Path("/tmp/mr")
META = MR / "_meta.json"
TPL = HERE / "prompts"


def _meta() -> dict:
    return json.loads(META.read_text()) if META.exists() else {}


def _save_meta(m: dict) -> None:
    MR.mkdir(exist_ok=True)
    META.write_text(json.dumps(m, indent=1))


def packet_dir(pid: str) -> Path:
    m = _meta()
    if pid not in m:
        m[pid] = {"token": secrets.token_hex(8)}
        _save_meta(m)
    d = MR / m[pid]["token"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def our_index(inbox_text: str) -> int:
    for line in inbox_text.splitlines():
        s = line.strip()
        if s[:3].strip(". ").isdigit() and "FROM: " + SENDER in s and s.endswith("FROM: " + SENDER):
            return int(s.split(".")[0])
    raise ValueError("our email not found in inbox")


def packet(pid: str, stage: str, extra: str | None = None) -> str:
    """Build the prompt file a buyer reads at a stage. Returns its path. Stages:
    t0 | open | followup | open_followup | reply (extra = file with the seller's reply) | final"""
    d = packet_dir(pid)
    m = _meta()
    if stage in ("t0", "followup"):
        inbox_txt = inbox(pid, "t0" if stage == "t0" else "followup")
        m[pid][f"idx_{stage}"] = our_index(inbox_txt)
        _save_meta(m)
        tpl = (TPL / "buyer_t0.md").read_text().replace("{INBOX}", inbox_txt)
        if stage == "t0":
            body = tpl.replace("{CARD}", card(pid))
        else:  # same character and rules; just the new week's inbox and the same triage task
            body = ("One week has passed. Same character and same rules as before.\n\n"
                    + tpl[tpl.index("Here is your inbox:"):].replace("this morning", "this morning, one week later"))
    elif stage in ("open", "open_followup"):
        fu = stage == "open_followup"
        s, b = our_email(pid, followup=fu)
        email = f"FROM: {SENDER}\nSUBJECT: {s}\n\n{b}"
        body = (TPL / "buyer_open.md").read_text().replace("{N}", str(m[pid]["idx_followup" if fu else "idx_t0"])).replace("{EMAIL}", email)
    elif stage == "reply":
        body = (TPL / "buyer_reply.md").read_text().replace("{EMAIL}", Path(extra).read_text().strip())
        n = len(list(d.glob("reply*_prompt.txt"))) + 1
        stage = f"reply{n}"
    elif stage == "final":
        body = (TPL / "buyer_final.md").read_text()
    else:
        raise ValueError(stage)
    f = d / f"{stage}_prompt.txt"
    f.write_text(body)
    log(pid, f"[shown to buyer] {stage}", str(f))
    return str(f)


def answer(pid: str, stage: str) -> dict:
    """Read the buyer's answer file for a stage, log it verbatim, and return its parsed fields."""
    d = packet_dir(pid)
    f = d / f"{stage}_answer.txt"
    txt = f.read_text()
    log(pid, f"[buyer answer] {stage}", str(f))
    fields, key = {}, None
    for line in txt.splitlines():
        head = line.split(":", 1)
        if len(head) == 2 and head[0].strip().isupper() and head[0].strip().replace("_", "").replace(" ", "").isalpha():
            key = head[0].strip()
            fields[key] = head[1].strip()
        elif key:
            fields[key] += "\n" + line
    return fields
