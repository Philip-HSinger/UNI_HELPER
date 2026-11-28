# Pitch v4: sharpened after four buyer personas read report v3

Pipeline stage 4 (2026-11-28). Report read: `product/demo/outputs/Calliper_report_v3_John_Smith.pdf` (9 pages,
including the new "Schools John never considered" panel and the "Who this helps" cards). Earlier reviews
(`expert.md`, `p03.md`, `p09.md`, `p17.md`) and the v1-v3 pitch emails plus the Nov 24 simulated email
(`research/emails/`) were read first, so points already fixed in v3 are not repeated. Personas are fictional
(`research/personas.json`); every number below comes from the report or `product/demo/outputs/`.

Core pitch being sharpened: Calliper finds schools a student never considered that he is likely to get into (SAT
bell-curve fit, linked decisions) and that need little or no new writing (essay-overlap scores), shows the real risk
of getting in nowhere, and plans the essay writing order, with the gain for student, essay coach and counselor clear
at once.

---

## (a) Report opening (2 sentences)

> John's eight schools carry a 40% chance that he gets in nowhere, not the 25% that multiplying each school's odds
> suggests, because every college reads the same application. Calliper found schools he never considered that he is
> likely to get into with little or no new writing (adding URI alone cuts the risk to 4%), and it sets an order for
> his 11 January essays that needs 42% fewer new words.

Why this shape: it leads with the one finding all four personas react to (the linked risk), puts the discovery
result in the same breath so it reads as the fix rather than a separate feature, and ends on the essay number that
the coach persona reads first. Detail (ranges, Bayes, the Tufts tree) stays below the fold for the quant reader.

## (b) One-sentence pitch per buyer type

| Buyer | Pitch |
|---|---|
| Solo private counselor | Send one senior's scores and list, no name, and Calliper returns the real chance they get in nowhere, the schools they never considered that cut it most for the least new writing, and an essay writing order, re-priced the day an early result lands. |
| Essay coach / coaching business | Calliper tells your coaches which supplement to write first so the later ones grow from it, and which schools a student could add without a new essay, so coach time goes to voice instead of the same story told five times; it never writes or rewrites a sentence. |
| Private-school counselor | Before ED results land, Calliper shows your office which lists could come back with no admissions because every college reads the same file, and which likely school with no extra essay closes the gap, in a counselor-only view where the percentages stay with you. |
| Public-school counselor | With no student names, Calliper's one-page example shows a parent why fifteen selective schools can say no together and how one likely school that needs no new essay fixes it, which is the page you need when a family is told their list is "too safe". |

Families and nonprofits get no separate pitch (families last; nonprofits share the public-school line).

---

## Persona readings of report v3 (in character, brief)

### p09: Jonathan Pierce, solo IEC, Seattle (quant, ~28 seniors)

- **Would make him reply:** the discovery panel finally does what he said was missing in his earlier review. "Add URI" was obvious;
  "Case Western, 29%, no supplement for his program, a school he never looked at" is not. Plus the Tufts tree, which
  replaces his December spreadsheet evening. He replies if the email says no names and that the method is written up.
- **Confuses him:** the chart's x-axis says "SAT bell-curve fit, linked model" but GPA is still absent, so is 29% a
  1420 with any grades? The 40% still has no sensitivity to the shared-factor strength (question 1 of his earlier review is still
  open). "Grey dots at 0 words" sit on the axis next to green ones: same cost, different chance, and the legend makes
  him work for it.
- **Hook sentence:** "It found schools he had never considered, likely admits needing no new essays; one cut the risk
  from 40% to 4%."

### p17: Maggie Holt, Inkwell Essay Studio, Brooklyn (9 coaches, 240 students in the December sprint)

- **Would make her reply/buy:** "which supplement to write first" in the subject line, and "No new essays" next to a
  school. She said in her earlier review that the list suggestion without extra essay load was the only odds part she would use; the
  discovery panel is now that, on a whole page. The v3 line "Calliper never writes or rewrites a sentence" answers her
  dealbreaker, but it is on page 9; she needs it in the email.
- **Confuses her:** page 2 to 3 are odds she skips. Still unsolved from her earlier review: "Rice: why Rice" borrows 53%
  from "Boston University: why BU" (table row 9, heatmap). That one row tells her the tool recycles why-us essays.
  "Two independent scorers" still does not say whether they are people or software.
- **Hook sentence:** "Across a student's whole list, which supplement goes first so the later ones grow from it?"

### p03: Eleanor Whitcombe, Director of College Counseling, CT boarding school

- **Would make her reply:** the three-box "25% vs 40%" panel for parent night, now joined by a concrete remedy (a
  likely school with no new writing) that she can defend to a dean, because it adds an application rather than
  recycling one. She replies in May, not now; a summer back-test on her eight years is the real hook.
- **Confuses her:** who reads this, still. "Who this helps" names the student first, which suggests families see
  percentages. Page 1 still says "every school is on Providence Country Day's 2024-2026 acceptance list" (a real
  school, flagged in her earlier review). URI and UMass are in-state answers that do not exist for her international
  boarders.
- **Hook sentence:** "Eight good schools are not a safe list, because every college reads the same file; Calliper
  shows your counselors which lists, and which one likely school closes the gap, without putting a percentage in
  front of a parent."

### p35: Karen Lieberman, public HS counselor, Bergen County NJ (~230 students)

- **Would make her reply:** a colleague mentioning it (her triage rule), or a page she can use at parent night with no
  student data, since nothing touches real students without a signed DPA. Her pain is "15 reaches that all fail
  together" and private consultants contradicting her; the linked-risk panel plus "add one likely school, no new
  essay" is exactly the argument she loses to parents today.
- **Confuses her:** "send scores and list, no name" is still student data under her district's rules. Is there a web
  version? What would a parent see? The report's Bayesian Tufts tree is more than she would show a family.
- **Hook sentence:** "When a consultant tells a family the list is too safe, here is one page showing why fifteen
  selective schools can say no together, and the one school with no new essay that fixes it."

---

## (c) Cold emails (each under 120 words including subject, sign-off, postal line and opt-out)

Also saved as `sales/pitch-email-v4-private-counselor.md` and `sales/pitch-email-v4-essay-coach.md`. Attach the v3
sample report (or the one-page version, next-steps item 3, once it exists).

### Private counselors (119 words)

```
Subject: 40% chance of no admits, and the fix

Hi [first name],

I'm Philip Singer, a Brown freshman in electrical engineering. Every college reads the same application, so rejections often come together, and multiplying odds hides that.

Calliper measures it. A sample senior's eight schools had a 40% chance of no admits. It found schools he had never considered, likely admits needing no new essays; one cut the risk to 4%. It also orders his essays and re-prices every school when an early result lands. Sample attached.

Want one for a senior of yours, free? Send scores and list, no name.

Philip Singer, Calliper
Calliper · 69 Brown Street #7457, Providence, RI 02912
Reply "stop" and I won't write again.
```

### Essay coaches (117 words)

```
Subject: which supplement to write first

Hi [first name],

I'm Philip Singer, a Brown freshman in electrical engineering. Calliper answers one December question: across a student's whole list, which supplement goes first so the later ones grow from it?

A sample senior had 11 January supplements, 2,700 words. Written in the right order, about 1,600 were new. Calliper also finds schools he never considered that he'd likely get into and that need no new essay. It never writes or rewrites a sentence. Sample attached.

Want a plan for one of your students, free? Send list and scores, no name.

Philip Singer, Calliper
Calliper · 69 Brown Street #7457, Providence, RI 02912
Reply "stop" and I won't write again.
```

Notes on the emails:
- No "simulated", no "AI", no "Bayesian" in the body: p09 and p17 both delete hype, and in the Nov 24 simulation every
  engaged reader asked how the linking is set, so the method is better offered on reply (p09 asks for it first).
- "Sample senior" keeps the fictional student honest without the word "simulated".
- Both emails ask for no name. Neither claims coach hours saved (not measured) or a school count for the prompt map.

---

## (d) Conflict log

Priority order: solo private counselors and essay coaches; then private-school counselors; then public-school
counselors and nonprofits; families last.

| # | Conflict | Side A | Side B | Winner and resolution |
|---|---|---|---|---|
| 1 | **What leads: odds or essays** (biggest) | p09 (solo): lead with risk and the post-ED update; essays are a nice extra | p17 (coach): essays first, odds are "a well-dressed preamble" | **Tie at top tier, resolved by splitting the email by buyer** and by a report opening where the discovery result joins both: one school that is a likely admit *and* needs no new essay. Risk sentence first in the report (3 of 4 personas react to it); the coach email leads with writing order. |
| 2 | Percentages vs bands | p09 (solo): wants numbers, ranges and sensitivity | p03 (private school) and p35 (public): no raw percentages near families | **p09 wins.** Opening and emails keep "40%" and "4%". Concession: the private-school pitch says the percentages stay with the counselor; the report's existing family-version line (Likely / Possible / Reach) stays. |
| 3 | When to sell | p09 and p17: now, on December deferrals and the Jan 1 sprint | p03: summer pilot only; p35: budget in February, adoption over summer | **p09/p17 win.** Offer is one free report now. The summer back-test is kept for the private-school conversation (Dec 3 meeting), not the cold email. |
| 4 | How it is delivered | p09: local Python package so names never leave his laptop; p17: no setup, CSV/Airtable | p35: web tool with a signed DPA; p03: Director of Technology review | **Solo/coach win with today's delivery:** no name, send scores and list, get a PDF back, nothing to install. p35 loses: she gets the no-data example page, not a pilot, until a DPA exists. |
| 5 | Essay-saving framing | p17 (coach): show what is saved, measured in coach time, not words | p03 (private school): drop word counts, say "ideas to build on" so it doesn't read as gaming | **p17 wins on keeping a concrete number** (2,700 words to about 1,600 new) framed as writing order, which also answers p03's "order, not borrowing" point. Coach hours are not claimed because they are not measured. |
| 6 | Level of method detail | p09: wants the shared-factor parameter, sensitivity, Bayes | p17, p35: no maths in the pitch | **p17 wins in the email** (no "Bayesian"), **p09 in the report**, where the method section stays; the method write-up is offered on reply. |
| 7 | Which discovery example to show | p03 (private school): URI is exactly what she would suggest | p09 (solo): URI is "just add a safety"; the non-obvious find is the value | **p09 wins on emphasis:** the email says "schools he had never considered" and gives the 4% result without naming URI as the point; the report should headline Case Western (29%, no supplement) as the find and URI as the cheapest fix, as v3 already does. |
| 8 | Who the report talks to first | Who-this-helps cards: student first | p03: counselor view only; families must not read "40%" alone | **Kept as is** (families last, but the student card is the benefit buyers sell to families). One-liners address the buyer, never the family. |

## Open items for stage 5 (not pitch, but each persona tripped on them in v3)

1. "Rice: why Rice" borrowing 53% from "BU: why BU" is still in the essay table and heatmap; p03 and p17 both called
   this the single most damaging row. Exclude why-us to why-us links.
2. "Providence Country Day's 2024-2026 acceptance list" on page 1 names a real school (p03).
3. Say who the "two independent scorers" are (p09, p17, p03, expert review).
4. Move "Calliper never writes or rewrites a sentence" from page 9 to the essay section (p17).
