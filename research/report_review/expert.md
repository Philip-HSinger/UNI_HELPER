# Expert review: Calliper_report_John_Smith.pdf (7 pages)

Reviewer stance: an admissions counselor plus a data editor. Every number on the page was checked against
`10_demo/outputs/odds.json`, `outputs/essay_plan.json`, `data/schools.json`, `data/prompts.json` and
`data/similarity_pairs.csv`. Most numbers match. The problems are in what the numbers are *labelled* as,
in the early-round advice, and in several captions that overclaim.

Format: **page**, what is wrong, then the exact suggested fix.

---

## 1. Numbers that don't match the outputs, or two places in the report that disagree

**1.1 p5, diagram title and caption: "Five strong links let John borrow 42%" is false.**
- The 42% (1 - 1,576/2,700) comes from all 11 links in the plan. The five arrows shown save 541 words (Fordham→Villanova 156, Penn→Emory 130, Emory→Rice 101, BU→Why Rice 79, Tufts→Penn 75). The plan saves 1,124 words in total.
- The caption also says "five strongest links". They are not the five strongest:
  - Tufts→Penn curiosity is 38%. That is weaker than Rice residential→Penn community (43%), Fordham→Emory community (43%) and Rice residential→BC (40%).
  - Ranked by words saved, the strongest links are Rice residential→BC (160), Fordham→Villanova (156), Villanova→Rice residential (144), Penn→Emory (130) and Emory→Rice academic (101).
- Fix, title: "Reusing material cuts John's January writing by 42%. The main chain is shown."
- Fix, caption: "Two independent scorers rated every pair of 2026–27 prompts. Shown: the Tufts→Penn→Emory→Rice chain and two other strong links. All 11 links are in the table below."

**1.2 p5 table vs p5 diagram vs p6 heatmap: the same pair is rounded differently.**
- The table and diagram round half up (63%, 43%, 53%, 43%). The heatmap uses banker's rounding (62, 42, 52, 42) for the same four pairs:
  - Villanova←Fordham (0.625)
  - Penn community←Rice residential (0.425)
  - Why Rice←Why BU (0.525)
  - Emory community←Fordham (0.425)
- A reader who compares the table with the heatmap sees 63 vs 62.
- Fix: round half up everywhere, so the heatmap shows 63, 43, 53 and 43.

**1.3 p3, UMass "105 new words" is computed against an essay John isn't writing.**
- `essay_plan.json` candidates→UMass step 3 reuses `rice-4` (the Rice "diverse community" essay). John's January plan picks `rice-3` (residential life), not `rice-4`. `rice-4` only exists in the old `full` plan.
- Against the January plan, UMass-4 reuses rice-3 at 0.575, which gives about 43 new words. That brings the UMass total to about **113**, not 105.
- Fix: rerun the UMass cost against `december.chosen` and print "113 new words · 3 short answers, mostly reused". The "Rice and BU" wording on p3 can stay.

**1.4 p7, "The full derivation of every number is in the annotated copy" points to an outdated document.**
- `Calliper_sample_report_annotated.pdf` (generated 19:06, before this report at 23:58) describes the earlier 10-school version:
  - "Thirteen prompts apply to this student"
  - a central risk of 41%
  - "Eight of ten schools' figures were confirmed"
- It also has a template bug in its first line: "How every number in Document was produced".
- A counselor who asks for it will find numbers that don't match.
- Fix: regenerate the annotated copy for this report before printing. Until then, delete the sentence or replace it with "Derivations available on request."

**1.5 p7, "Every input was collected from the source and then checked a second time by an independent agent" overstates the verification.**
- `schools.json` marks Fordham and Wesleyan stats `verified: "unresolved"`. Fordham's CDS could not be opened, and Wesleyan's file could not be reopened.
- `verify/prompts_check.json` marks the BU prompt "unresolved", because sources split on its second sentence.
- Fix: "Every input was collected from the original source and checked a second time. Two schools' statistics (Fordham, Wesleyan) and one prompt (BU) could not be fully confirmed."

**1.6 p7, "Tufts' Early Decision is priced halfway between its 11% overall and 32% Early Decision rates" gives the wrong number.**
- A reader taking the plain midpoint gets 21.4%. The model uses the midpoint on the log-odds scale, which is 19.3% (`rates_used.tufts` = 0.193).
- Fix: "Tufts' Early Decision is priced at about 19%, between its 11% overall and 32% Early Decision rates (midpoint on the log-odds scale). The published ED rate is inflated by recruited athletes and legacies, and early applicants tend to be stronger."

**1.7 p2, caption names one data exception but there are two on the chart.**
- The caption reads "2025–26 Common Data Set (Boston College 2024–25)". Fordham, which is on the chart, has no CDS and uses its Fall 2026 admission-facts page (p7 says so).
- Fix: "…from each school's 2025–26 Common Data Set (Boston College 2024–25; Fordham from its Fall 2026 admission facts page)."

**1.8 p2, box 1: the printed factors don't multiply to the printed answer.**
- 0.87 × 1.00 × 0.98 × 0.97 × 0.93 × 0.92 × 0.79 × 0.46 = 0.257, which rounds to 26%. The box says 25%, which is the unrounded 0.2528. A counselor checking the arithmetic with a phone will get 26%.
- Fix (either one):
  - print three decimals: "0.866 × 0.996 × 0.980 × 0.971 × 0.926 × 0.921 × 0.787 × 0.459", which gives 25.3%
  - or keep two decimals and change the result line to "about 25%" with a footnote "(unrounded)"

**1.9 p6 vs p4: "14 prompts" vs "11 essays".**
- Both counts are correct: 11 to write plus 3 already sent. Nothing on page 6 says so.
- Fix, p6 caption: "the 14 prompts in John's plan (3 already sent, 11 to write)".

**1.10 Pipeline bug, not visible in print but it will surface in the tool: Penn's central estimate lies outside its own range.**
- Baseline: `upenn.chance` 0.0035, `lo` 0.0018, `hi` 0.0028.
- After rejection: `chance` 0.00207, `hi` 0.00195.
- The chart hides this behind "under 1%", but any view that draws Penn's range will put the dot outside the line.
- Fix in `s4_odds.py` before anyone sees the tool: compute lo and hi with the same lapse and withheld-score handling as the central estimate.

**1.11 p4, Deferred box: "risk of no admissions falls to 14%" leaves out a later Tufts admission.**
- `scenarios.deferred.risk_rest` is the risk across the other seven schools only. A deferred applicant can still be admitted by Tufts in the regular round.
- Fix: "Deferred: risk of no admissions at his other seven schools falls to 14%."

---

## 2. Claims a counselor or essay coach would call wrong or misleading

**2.1 p4, "A Tufts rejection is the one result that needs action before January" ignores Early Decision II. This is the biggest strategic miss.**
- After an ED I rejection, the standard counselor move is ED II. Five schools already on John's list offer it (`schools.json`):
  - Emory, Jan 1 (ED 22% vs 10% overall)
  - Rice, Jan 4
  - Boston College, Jan 4 (33% vs 16%)
  - BU, Jan 5 (31% vs 13%)
  - Villanova, Jan 15 (60% vs 28%)
- A report that answers a Tufts rejection with only "add URI" will lose a counselor's trust on the spot.
- Fix, Rejected box: "Rejected: risk of no admissions rises to 48%. Two moves: (1) switch one January school to Early Decision II: BC, BU, Emory, Rice and Villanova all offer it; (2) add URI (no essays). Risk with URI: 5%."
- If the model can price an ED II switch, add that number too.

**2.2 p3/p4, the URI advice contradicts itself and misses the Early Action deadline.**
- p1 and p3 present URI as the fix now ("cuts John's risk… from 40% to 4%"). On p4, URI is only the rejection-branch action ("before its Feb 1 deadline"), and the Deferred branch says "Keep the list as it is", which leaves a 14% risk (range 9–26%) even though URI costs no essays.
- The p3 mock-up shows URI Early Action closes Dec 1, four days after the report date. Applying Early Action gets a decision before the January deadlines and is how URI considers merit aid. A counselor would say "apply to URI Early Action this week, whatever Tufts does."
- Fix, p3 lead: "Adding URI needs no new essays and cuts John's risk of no admissions from 40% to 4%. Apply by its Dec 1 Early Action deadline if possible; the Feb 1 regular deadline still works."
- Fix, p4 Deferred box: "Keep the list, and add URI if he has not already."
- Fix, p4 Rejected box: as in 2.1.

**2.3 p3–p4, Fordham's Early Action decision is never mentioned, though it arrives in December.**
- Fordham's EA result comes out at about the same time as Tufts'. It is the single result that settles the whole question: if Fordham admits him, his risk of no admissions is 0%. The report frames December as "When Tufts decides" and moves Fordham from 54% to 80% or 47% as if its decision were still pending.
- Fix, add one line under the p4 diagram: "Fordham's Early Action decision also arrives in December. If Fordham admits him, John is guaranteed a place and the rest of the list is about choice, not safety."
- Confirm Fordham's EA notification date before printing. It is not in `schools.json`.

**2.4 p4, the claim that a deferral is good news is stated as fact in the diagram and only hedged in the text.**
- The box says "A near miss at Tufts is good news for the other schools" and moves Villanova from 21% to 39% and Fordham from 54% to 80%. Counselors treat ED deferrals as neutral or a soft no. The body text admits this, but the diagram, which is what people remember, does not.
- Fix, box text: "Deferred: the model reads a deferral as a near miss, so other chances rise (BC 7%→14%, BU 8%→15%, Villanova 21%→39%). Counselors often read it more cautiously."
- Fix, body: "The model reads a deferral as a near miss: the application landed just below Tufts' bar. Many counselors treat an Early Decision deferral as a soft no, so this is the assumption most worth testing against real outcomes."

**2.5 p2 (and p1), chances are presented without saying the model ignores GPA.**
- p1 says John has "strong grades", but p7 says GPA is "not yet included". The model uses only SAT and published rates, plus a fixed assumption about how strongly the essays and recommendations read. A counselor will discount every number on p2 unless this is said next to the chart.
- Fix, add under the p2 chart: "Based on SAT scores and each school's published admit rates. GPA, course rigor, activities and hooks are not yet in the model."

**2.6 p2/p7, the report never says which schools get John's SAT.**
- The model withholds his 1420 at Tufts, Rice, Emory and BC (`sends_sat: false`) and sends it at BU and Villanova, where 1420 is the 25th percentile, and at Fordham. That is a real recommendation a counselor will want to see and may disagree with: sending a 25th-percentile score to a test-optional school is debatable.
- Fix, add to p7 "Admit rates and SAT ranges": "The model assumes John submits his 1420 only where it helps: sent to BU, Villanova, Fordham and Penn (required); withheld at Tufts, Rice, Emory and Boston College."

**2.7 p2, "1420 is below its range" for Penn is imprecise.**
- Penn's CDS gives no composite range. 1510 is the sum of the section 25th percentiles (EBRW 740, Math 770), and it describes enrolled students.
- Fix: "Penn requires test scores, and John's 1420 is well below the scores of most enrolled students (25th percentile about 1510), so his chance there is under 1%."

**2.8 p4, the Admitted box: ED is binding, but with a financial-aid exception.**
- Fix: "Admitted: Early Decision is binding, so he withdraws every other application, including Fordham (unless the aid offer is not affordable)."

**2.9 p5–p6, the "borrowing" framing will alarm an essay coach, and two links are exactly what coaches warn against.**
- "Why us" answers reused across schools are the classic mistake. The plan reuses 53% of "Why BU" for "Why Rice" and 50% of "Why BU" for "Why UMass" (p3). Rice academic (68%) and Emory academic (65%) reuse leaves only 49–70 new words for the school-specific part.
- Fix, add a sentence after the p5 table: "'Reuse' means the same story, research or idea, rewritten for each prompt, not pasted text. School-specific answers (Why Rice, Why BU, Community at Penn, Why UMass) reuse only the student's own interests; the school-specific half must be new."
- Fix, wording: replace "borrow" / "Borrows from" with "reuse" / "Builds on" throughout (p3, p5, p6).
- Better, in the pipeline: cap reuse into "why us" prompts at about 40%.

**2.10 p5, "nobody spots the chain by hand" insults the reader you are pitching.**
- Essay coaches map story reuse across supplements for a living.
- Fix: "Seen one pair at a time, these prompts look unrelated; across 8 schools and 27 prompts, the chain is easy to miss."

**2.11 p6, "the plan picks the option that needs the fewest new words" puts word count ahead of the best story.**
- Coaches would object to choosing a prompt on word count alone.
- Fix: "…the plan suggests the option that needs the fewest new words. John should still choose the prompt he has the best story for; the tool reprices the plan if he changes it."

**2.12 p4/p2, the size of the "linked decisions" update is an assumption nobody can see.**
- BU drops from 8% to 4% after a Tufts rejection, an outcome the model itself expects 87% of the time. A counselor will ask why one rejection at a 13% school halves the next school's odds. The size comes from a fixed parameter (`gamma_shared` 0.3) that the report never mentions.
- Fix, add to p7 "Linked decisions": "How strongly one result moves the others is set by an assumption (how much of a decision comes from the shared essays and recommendations rather than school-specific factors); it has not yet been fitted to real outcomes."

**2.13 p1, naming a real school's acceptance list.**
- "Every school is on Providence Country Day's 2024–2026 acceptance list" names a real school. It could read as an endorsement or a data relationship when shown to a counselor from another private school. The text also says "Providence", but PCD is in East Providence.
- Fix: "Example student. Every school on his list admitted students from a Providence-area independent school in 2024–2026 (from that school's public profile)." Or keep the name only if PCD has agreed to it.

**2.14 p1, the URI and Northeastern descriptions don't fit "state universities or the smaller colleges nearby".**
- Northeastern is neither.
- Fix: "He has never looked seriously at the state universities or at less familiar private colleges nearby."

---

## 3. Visual problems

**3.1 p2, the dot-and-range chart puts each value label at the end of the range line, so it reads as the upper bound.**
- "54%" sits at the right end of Fordham's line, next to where the 94% upper bound is. "13%" for Tufts touches the 50% dashed line.
- Fix: put the label next to the dot, or label as "54% (9–94%)". Add 0% and 100% ticks to the axis.

**3.2 p2, the 80% ranges are very wide (Fordham 9–94%, Villanova 1–61%) and nothing explains them.**
- A counselor will say a range this wide is uninformative, and will wonder why the list total (34–43%) is so narrow.
- Fix, add to the chart subtitle: "Ranges are wide for single schools because they depend on how the essays read; the list-level risk is narrower because those uncertainties partly cancel."

**3.3 p6, the heatmap column labels are internal IDs that the reader cannot decode.**
- Columns read "Tufts 2", "Penn 4", "Rice 3", "Emory 2", while rows use names ("Penn · your curiosity").
- Fix: label columns with the same short names as rows (Tufts assignment, Tufts engaging, Fordham, Villanova, Penn thank-you, Rice residential, Penn community, Penn curiosity, Emory academic, Rice academic, Why BU, Why Rice, Emory community, BC tradition), or add a matching row number to each column.

**3.4 p6, the first link of the "Strongest chain" (Tufts→Penn curiosity, 38%) is unlabelled because the threshold is 40%, so the chain the callout names can't be traced on the chart.**
- Fix: label every cell on the named chain, or drop the threshold to 35%.

**3.5 p6–p7, "Brighter cell = more" is wrong for dark columns.**
- Emory's navy cells (55, 68) and BU's green cells are darker, not brighter. Different hues per column make strength hard to compare across columns.
- Fix: use one sequential color for strength, show school only in the column header strip, and change the legend to "Darker cell = more of the row's essay can come from the column's essay." Update the p7 sentence to match.

**3.6 p6, rows for the three already-sent essays (Tufts ×2, Fordham) are noise as "essays he needs".**
- Fix: grey out those three rows, or move them to the bottom under a "Sent" label.

**3.7 p5, the 65% and 53% arrow labels float below and beside boxes and are hard to attach to their arrows.**
- Fix: put each percentage on its arrow's midpoint.

**3.8 Layout: orphaned headings and a split table.**
- "When Tufts decides" (p3) is separated from its diagram (p4).
- p4 is half blank under "Essays".
- The essay table splits so that row 11 sits alone on p6 under a repeated header.
- Fix: page break before "When Tufts decides"; put the "Essays" heading and lead at the top of p5 with the diagram; shrink row padding so all 11 rows fit on one page.

**3.9 p3, the mock-up's UMass row has no deadline, while every other row has one.**
- Fix: "113 new words · 3 short answers, mostly reused · Regular Jan 15".

**3.10 p3 vs p6, the two mock-ups show different navigation.**
- p3 has a sidebar: Overview, List check, Essays, Early results. p6 has tabs: List check, Essays, Early results.
- Fix: use the same nav in both (drop "Overview" or add it to p6).

**3.11 p1, the "UMass Amherst" pill text touches its right border.**
- Fix: add padding or widen the pill.

**3.12 Running header and footer are set in DejaVu Sans (fallback font).**
- Every other element uses the Anthropic Sans/Serif fonts, so the header and footer look like a different document.
- Fix: set the running header and footer to the body sans.

---

## 4. Wording: unclear, too long, or reads as AI-written

- **p1, all through: "chance of no admissions" is clumsy and repeated about 10 times.**
  Fix: "chance he is admitted nowhere" (or "risk of no offers"). Use one phrase throughout.
- **p1, the byline "@philip" looks like a social handle on a printed document for professionals.**
  Fix: "Prepared by Philip Singer, Calliper · Nov 27, 2026".
- **p2, box 2: "If Tufts says no, they probably read weaker than hoped" has an unclear "they".**
  Fix: "If Tufts says no, John's application probably reads weaker than hoped, and the next school will likely read it the same way."
- **p2, the lead under the chart repeats the chart title.**
  Fix: "Fordham is his only school above even odds. Penn requires test scores, and John's 1420 is well below most of its students' scores, so his chance there is under 1%." Drop "the only one keeping the risk from being far worse": it is unquantified.
- **p3, "nothing else on the board comes close": "board" is jargon.**
  Fix: "No other school comes close."
- **p3, "URI asks this student for no supplement" is stilted.**
  Fix: "URI has no supplemental essay for John's major and admits three in four applicants."
- **p3, "how many new essay words it costs given what he has already written" is inaccurate, because most of the source essays are not written yet.**
  Fix: "given what he has written or plans to write."
- **p4, "which is better than a 13% chance implied" is garbled.** See 2.4 for the full rewrite.
- **p4, the Essays lead is too dense.**
  Fix: "John has 11 essays due in January, 2,700 words in all. Written in the right order, reusing material, he needs only 1,576 new words: 42% less."
  Drop "short": two of the essays are 400 and 500 words.
- **p5/p6, prompt names change between the table, diagram and heatmap.**
  Examples: "Penn: something you are curious about" / "Penn: curiosity" / "Your curiosity"; "Rice: residential life and your experiences" / "Rice: residential life"; "Emory: a community you shaped" / "A community".
  Fix: pick one short label per prompt and use it everywhere.
- **p5, table headers.**
  Fix: "Words" → "Word limit"; "Share covered" → "Reusable"; "Borrows from" → "Builds on".
- **p6/p7, "colour" (British) in a report for US readers; the rest of the report uses US spelling.**
  Fix: "color".
- **p7, "Ranges cover what nobody can measure in advance." is vague, aphoristic AI phrasing.**
  Fix: "The ranges show how much each answer depends on how strongly the essays and recommendations read, which cannot be measured in advance."
- **p7, "correlation 0.89 on the pairs that matter" is vague.**
  Fix: "correlation 0.89 on the 394 scores above 10%".
- **p7, "checked … by an independent agent" and "two independent scorers": if these are AI models, say so.**
  A counselor will assume they are people, and finding out later costs trust.
  Fix: "checked a second time by a separate AI review" and "two independently prompted AI scorers".
- **p6–p7, colon-heavy sentence pattern.**
  "The chain matters: …", "Most cells are faint: the value is in the handful of bright ones…": this reads as machine-written.
  Fix, p7: "Most cells are faint. The few bright ones are the links worth using, and they are hard to find reading prompts one pair at a time."
- **p7, contact address "calliper@agentmail.to" looks temporary on a printed business document.**
  Fix: use a domain address, or Philip's own email.
