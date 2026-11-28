"""Write emails/<id>.md and emails/<id>_followup.md: the user's Calliper email, with one personal line per prospect
written from the PUBLIC profile only."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / "personas.json").read_text())
HOOK = {
 "p01": "I saw your posts about FAFSA nights and TSI testing on the school site.",
 "p02": "Being the only counselor in a district while also running testing and College Credit Plus sounds like a lot.",
 "p03": "I came across your conference talks on ethics in admissions.",
 "p04": "I read that you run your office's annual outcomes report, so I thought you'd like the numbers side of this.",
 "p05": "I know you advise students across five countries, so US lists are only part of your year.",
 "p06": "I saw that most of your graduates head to the US and UK.",
 "p07": "I saw you serve on the state task force on college access.",
 "p08": "I saw your network publicly reports matriculation and persistence, which is rare.",
 "p09": "I've been reading your blog on admissions statistics.",
 "p10": "I saw you help local families with essays and Florida university applications.",
 "p11": "I saw Crestline works with families on selective admissions in the Bay Area.",
 "p12": "I know a caseload of ~35 seniors in December doesn't leave much spare time.",
 "p13": "I saw you lead the counselor analytics roadmap at Trellisway.",
 "p14": "I saw you lead the data team at ScoreRise.",
 "p15": "I saw you're building CampusOdds.",
 "p16": "I've watched a few of your 'chances me' streams.",
 "p17": "I saw your December Supplement Sprint.",
 "p18": "I saw First Rung publishes UC/CSU admission rates across its 12 schools.",
 "p19": "I saw the Saturday college-prep circle you run at Riverside.",
 "p20": "I saw BrightAbroad advises students applying to the US.",
 "p21": "I saw Jade Gate focuses on top-30 US undergraduate admissions.",
 "p22": "I saw Harmattan Gate is growing its US undergraduate clients.",
 "p23": "I've seen your posts on parent forums about admissions data.",
 "p24": "I saw your posts in the local college-parent group.",
 "p25": "I saw your posts on the admissions forums about your 14-school list.",
 "p26": "I saw you write school profiles and transcripts for your co-op families.",
 "p27": "I saw your talks on yield and admit modelling.",
 "p28": "I've read some of your work on undermatching.",
 "p29": "I saw your post about launching a college-advising category in Q1.",
 "p30": "I saw the FAFSA and CSS Profile workshops you run across the county.",
 "p31": "I saw you've backed a lot of edtech companies.",
 "p32": "I saw St. Benedict puts a lot of weight on affordability in college lists.",
 "p33": "I saw you help recruited athletes with admissions as well as recruiting.",
 "p34": "I saw the partnership follows students from grade 7 into college.",
 "p35": "I saw you present at Ridgeview's parent college nights.",
 "p36": "I saw the transfer workshops you run with UC, CSU and private universities.",
}
BODY = """Subject: your seniors' RD lists after early results
Hi {first},

{hook}

I'm an electrical engineering student at Brown, and I've built a tool for college counselors.

When early results come out next month, it uses Bayesian probability to update a student's chances at every school left on their list. It treats applications as dependent, not independent: the same application is read everywhere, so an ED admit or deferral shifts the odds at every other school. You'll know before Jan 1 whether the RD list still works, and which lists risk getting in nowhere.

I'm also working on the essay side: it maps which supplements overlap, so a student can see that their MIT essay on why they love their field already covers most of Princeton's academic-interest essay and how many new words each school actually needs. You can spot that two prompts overlap, but not across 20 schools with five prompts each.

Would you be up for trying it on one of your seniors? No name or identifying data needed, just their SAT, GPA and college list, and I'll send back a one-page report. It's free.

If you're curious how both features work, I've attached a short PDF that explains them, and I'm happy to walk you through it on a call.

Thanks,
Philip
Calliper

[Attachment: Calliper_overview.pdf]
"""
FOLLOW = """Subject: Re: your seniors' RD lists after early results
Hi {first},

Quick follow-up: early results start coming out in a couple of weeks. If you send me one senior's SAT, GPA and college list (no name), I'll send back a one-page report on their updated odds and how the list holds up. It's free and takes two minutes.

Thanks,
Philip
Calliper
"""
for p in P:
    name = p["public_profile"]["name"].replace("Dr. ", "").replace("Br. ", "Brother ")
    first = name.split()[0] if not name.startswith("Brother") else "Brother " + name.split()[1]
    if "Grace" in name:
        first = "Grace"
    if "Maggie" in name:
        first = "Maggie"
    hook = HOOK[p["id"][:3]]
    (HERE / "emails" / f"{p['id']}.md").write_text(BODY.format(first=first, hook=hook))
    (HERE / "emails" / f"{p['id']}_followup.md").write_text(FOLLOW.format(first=first))
print("ok", len(P))
