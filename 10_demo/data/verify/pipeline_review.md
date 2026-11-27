# Pipeline review: 10-school demo (review date 2026-11-27)

Scope: scripts/common.py, s1_merge.py, s3_matrix.py, s4_odds.py, rubric.md; data/raw, data/verify, data/*.json/csv, data/scores; outputs/*; toolkit/unimath/model.py.
No pipeline file was changed. All numbers below were recomputed independently from the raw/scorer files.

## Summary of what checks out

- **schools.json vs raw + verify**: every field matches the raw CDS records after the verifier corrections. The only correction (Fordham `cds_year` -> null) was applied. Every `admit_rate` equals admits/applicants to 4 dp, and every `ed_rate` equals ed_admits/ed_applicants. The SAT bands are internally consistent at all 9 schools with section data: the section 25ths sum to at most the composite 25th, and the section 75ths sum to at least the composite 75th. No SAT band is implausible.
- **Prompts**: the required set for a domestic arts-and-sciences applicant with no honors and no special program is right. It is Tufts-1 and Tufts-2; BC choose 1 of 4; BU-1; Fordham optional choose 1 of 3; UMass-1, -2 and -4. All 12 exclusions are correct (Tufts-3/4/5, BC-5, BU-2/3, UMass-3, URI-1..4, and Wesleyan-1, which is international only). Northeastern, Holy Cross, Fairfield and Wesleyan (domestic) have no supplement. URI has none for general applicants. The word limits match the sources: 150, 200, 400, 300, 300 and 100.
- **similarity_pairs.csv**: all 130 rows recompute exactly (scorer A, scorer B, mean, length factor, R). The length factor is applied in the right direction: R(p <- q) = content x min(1, L_q / L_p), with q the essay already written.
- **essay_plan.json arithmetic**: naive 1650 = 150+200+300+100+100+400+300+100; new 1339 = 400+292+165+170+120+50+70+72; saved = 1 - 1339/1650 = 0.188. Each step's reuse_share and new_words recompute (292 and 72 are banker's rounding of 292.5 and 72.5).
- **Odds reproducibility**: `python3 s4_odds.py` reproduces outputs/odds.json byte for byte (git status clean after the run).
- **ED pricing** is implemented as described: central = expit((logit 0.1082 + logit 0.3203)/2) = 0.1930. The Tufts chance is 6.6% / 13.4% / 24.9% at the low / central / high ends.

---

## Findings, by severity

### HIGH 1. The early-round strategy and the writing order conflict with the calendar (today is 2026-11-27)
Source: data/raw/stats_batch*.json `deadlines`; s4_odds.py `ED`/`EA`; outputs/essay_plan.json `plan`.
- These deadlines have already passed: Tufts ED1 (Nov 2), Northeastern ED/EA (Nov 1), Fordham EA/ED1 (Nov 1, extended to Nov 8), Fairfield EA (Nov 1), UMass EA (Nov 5), and Holy Cross, Wesleyan and Fairfield ED1 (Nov 15). Only URI EA (Dec 1) and the January deadlines remain.
- The odds still model Tufts ED plus EA at Northeastern, Fordham, Fairfield, UMass and URI. The essay plan still treats the Tufts, Fordham and UMass essays (950 of the 1,650 words) as unwritten. One of two things is true:
  - **The student has already submitted.** Then the essay plan overstates the remaining work by 950 words, and the reuse savings are counted against essays that are already final. Example: UMass-4 "reuses" BC-3, which is written later.
  - **The student has not submitted.** Then Tufts ED means ED2 (Jan 4; the CDS ED rate may pool ED1 and ED2), and the EA schools become RD.
- The greedy order ignores deadlines either way. BC-3 (due Jan 4) comes first, the Tufts ED essays are steps 4-5, and UMass (an EA school) comes last. A real plan has to write the earliest deadlines first.

### HIGH 2. The "accepted at Tufts ED" scenario is meaningless: ED is binding
Source: outputs/odds.json `scenarios.accepted`.
- The output gives chances at the other nine schools after a Tufts ED acceptance (BC 32.7%, BU 31.5%, Wesleyan 53.1% and so on). It also gives `risk_rest` = 0.2%.
- An ED admit has to withdraw every other application. Only EA results already in hand matter. A counselor would strike this block immediately.
- The scenario should read "enrolls at Tufts; other applications withdrawn".

### HIGH 3. RD and EA chances use overall admit rates that include ED admits, and some of those rates are stale
Source: schools.json `admit_rate`; s4_odds.py `entry()`.
- The student applies non-ED everywhere except Tufts. The rate for non-ED applicants, (admits - ED admits)/(applicants - ED applicants), is lower than the overall rate:

  | School | Overall rate used | Non-ED rate |
  | --- | --- | --- |
  | Holy Cross | 21.1% | **16.7%** |
  | BC | 16.2% | **13.8%** |
  | Wesleyan | 16.4% | 14.0% |
  | BU | 12.8% | 11.0% |
  | Northeastern | 5.6% | 4.0% |
  | Fairfield | 25.1% | 23.1% |
  | Tufts (low end of the ED range) | 10.8% | RD is really 8.5% |

- On top of that, BC uses the 2024-25 CDS (16.2%), while BC's own Class of 2030 profile in the raw notes shows 13.4% (41,923 apps / 5,636 admits). Holy Cross uses the 2023-24 CDS (21.1%), against about 18% for the Class of 2030 on its site.
- The result is that BC, Holy Cross and Wesleyan are overstated by roughly 20-35% in relative terms. Holy Cross at 40.4% is the clearest case: that is a "likely" label for a school whose current RD rate is probably 14-16%.

### HIGH 4. "Sends SAT" is wrong or knife-edge at several schools
Source: odds.json `baseline.*.sends_sat`; model.py `submit_policy` and `withheld_z = -0.25`.
I recomputed P(admit) when sending vs withholding:

| School | Admitted band (enrolled) | 1420 is... | Model says | P(send) | P(withhold) |
| --- | --- | --- | --- | --- | --- |
| Tufts | 1460-1520 | below the 25th | withhold | 10.2% | 13.4% |
| BC | 1460-1520 (math 25th 730) | below the 25th | **send** | 9.8% | 9.2% |
| BU | 1420-1510 | at the 25th | **send** | 9.3% | 8.8% |
| Northeastern | 1440-1510 | below the 25th | **send** | 4.5% | **1.7%** |
| Wesleyan | 1350-1510, median 1460 | below the median | send | 19.9% | 13.8% |
| Holy Cross, Fairfield, URI | | above the 75th | send | (correct) | |
| Fordham, UMass | | around the median | send | (reasonable) | |

- **BC and BU**: the model compares the student with an inferred applicant-pool mean, not with the admitted band. Then 1420 sits at z = -0.18 / -0.17, just above the arbitrary withheld_z of -0.25. The difference is 0.5-0.6 pp, which is noise. A counselor would say do not send at BC (below the 25th, and math 710 against a 730 25th), and probably not at BU.
- **Northeastern**: sending supposedly multiplies the chance by 2.6. That comes from the C7 "Very Important" weight (a = 1.0) combined with the withheld_z penalty. About 70% of Northeastern enrollees submitted no test (22% SAT + 8% ACT), so withholding cannot cut a student's chance by 60%. With 1420 below the 25th, the usual advice is to withhold.
- As built, the output tells the coach to send at schools where it hurts or is neutral. These should be presented as "borderline / withhold".

### HIGH 5. Wesleyan and Fordham stats go into the odds unverified, with no flag
Source: data/verify/stats_check.json.
- Wesleyan's verdict is `unresolved`: no field could be checked.
- Fordham's verdict is `unresolved`, and its data has three problems:
  - The figures are non-CDS and from a different cycle (Fall 2026 against Fall 2025 or older elsewhere).
  - `test_importance` is null, so model.py silently uses "Considered".
  - The SAT band is for enrolled students only (about 30% submitted).
- s1_merge stores `verified` but s4_odds never reads it, so odds.json shows these two schools with the same confidence as the verified ones. Separately, Fordham's `cds_url` still points to the 2024-25 CDS, which was not used (the `cds_year` was nulled but the URL was not). That is a misleading source citation.

### MEDIUM 6. Enrolled score bands are treated as admitted bands (`enrolled_shift = 0`)
- At schools with low yield, admitted students score higher than enrolled students. The raw notes give the admitted bands:

  | School | Admitted band | Enrolled band used |
  | --- | --- | --- |
  | Fairfield | 1320-1420 | 1280-1370 |
  | URI | 1170-1340 | 1090-1310 |
  | Fordham | 1380-1490 | 1355-1470 |

- So the student's relative standing is overstated at these schools: Fairfield 49.4%, Fordham 54.1%, Holy Cross 40.4%. Together with finding 3, the "target" schools look safer than they are.

### MEDIUM 7. Odds are driven by the SAT alone
- `Student(710, 710)` has no holistic rating. model.py infers non-test strength from the score: h = 0.4 x (1420 - 1300)/180 = +0.27 sd. In other words, it assumes the student is average for their score.
- GPA, rigor and essays are not inputs. A counselor will ask where the grades are.
- The 80% "lo-hi" ranges are close to uninformative (Tufts 1.0-41.4%, Fairfield 6.4-91.7%). They are spread over unknown applicant strength, not an error bar on the estimate. They need that caption, or they will be read as a confidence interval.

### MEDIUM 8. The essay plan ignores the Common App personal statement and tells one story three times
- The pipeline picks BC-3 ("a time someone defined you by a single story") and Fordham-1 (an experience that changed your perspective). UMass-4 (community) is then built from BC-3 as well. That is one identity/stereotype story used three times.
- That story may also duplicate the 650-word personal statement that every school receives, which the model does not consider. Supplements are meant to add new dimensions.
- BC-3 also assumes the student has actually been stereotyped. The choice should be the student's and the coach's.
- The choice rests on small margins. The BC reuse scores are 0.171 vs 0.152 / 0.148 / 0.144.
- The choice score in `required_set()` averages over *all* other-school prompts, including options that will never be written (Fordham-2/3 when scoring BC, the other BC options when scoring Fordham), instead of over the required set.
- Judged by its own metric, the choice is right. I enumerated every BC x Fordham pair with its optimal order: BC-3 + Fordham-1 = 1317 words, the next best is BC-1 + Fordham-3 = 1360, and the worst is 1414.
- The "saved 18.8%" depends on the optional Fordham essay. Without it, the naive total is 1350 and the optimum is 1174 words.

### MEDIUM 9. The greedy writing order is not optimal, and it ignores deadlines
- The greedy order gives 1339 new words. The brute-force optimum over all 8! orders is **1317**: BC-3, Fordham-1, Tufts-2, BU-1, Tufts-1, UMass-1, UMass-2, UMass-4.
- The loss comes from writing BU-1 second, where it gets 2.5% reuse. Written after Tufts-2 it would get 10%.
- The `supply` criterion only counts what an essay gives to later essays, never what it could receive. The deadline problem is covered in finding 1.

### MEDIUM 10. Similarity: the rubric direction rule is backwards, and some scores are questionable
- **Rubric (rubric.md)**: "a broad prompt usually supplies a narrow one better than the reverse" gets it the wrong way round. An essay written for a narrow prompt (BC-3, single story) is automatically a valid answer to a broad one (Fordham-1, a perspective change). An essay for the broad prompt may be about anything. The scorers sensibly ignored the rule: Fordham-1 <- BC-3 = 45, but BC-3 <- Fordham-1 = 30. The rubric should be fixed before any rescoring.
- **Probably too high**: Tufts-1 <- BU-1 = 20 and Tufts-1 <- UMass-1 = 22.5. Tufts-1 asks *how you learned about and engaged with Tufts* (visits, conversations, research). A why-BU or why-UMass essay supplies almost none of that, so 5-10 is more defensible. The plan relies on 0.20 for Tufts-1 (30 words).
- **Probably too low**: UMass-4 <- BC-1 = 45. Both are about a community, its significance and how it brings people together; UMass adds "how you'd enrich campus". The rubric anchor for "same core subject, one asks extra" is 60-80. Fordham-1 <- BC-3 = 45 is also at the low end. No score in the whole file exceeds 50.
- **Scorer independence**: 43% of the 130 scores are identical between A and B, and the reasons are near-paraphrases. The headline r = 0.94 / MAE 2.6 is inflated by the 63% of scores where both scorers gave 10 or less. On the 48 scores above 10, r = 0.84 and MAE = 5.0. No pair crossed the 25-point adjudication threshold.

**Hand recomputation (5 rows)**:

| p <- q | A | B | Mean | Factor | R |
| --- | --- | --- | --- | --- | --- |
| BC-1 (400) <- BU-1 (300) | 3 | 3 | 3 | 300/400 = 0.75 | 0.0225 -> 0.022 |
| BC-2 (400) <- UMass-4 (100) | 8 | 10 | 9 | 0.25 | 0.0225 -> 0.022 |
| BU-1 (300) <- Tufts-2 (200) | 15 | 15 | 15 | 0.667 | 0.100 |
| Fordham-3 (300) <- UMass-4 (100) | 10 | 10 | 10 | 0.333 | 0.033 |
| UMass-4 (100) <- BC-1 (400) | 50 | 40 | 45 | min(1, 4) = 1 | 0.45 |

All five match the CSV.

### MEDIUM 11. The Fordham composite-only fallback understates the score spread
- s4_odds.py splits the composite band in half for each section. model.py then recombines the two halves with rho_em = 0.6, as if the sections were imperfectly correlated.
- The fitted admitted composite SD comes out at 75, which is an IQR of about 101, against the published 1355-1470 IQR of 115.
- The halves are perfectly correlated by construction, so the composite should be fitted directly (or rho = 1 used). The effect on the chance is small but systematic. The median is also imputed as the midpoint, 1412.5, without a flag.

### LOW 12. Prompt-data caveats the coach should see
- **BU-1 wording**: decisions.json drops "How do you hope to contribute to our campus community?". The sources split 5 to 6, and the two portal-read sources omit it, so the call is reasonable but not settled. A 300-word draft should still cover "contribute", at no cost.
- **UMass third question**: its presence in the app is disputed (GradGPT says the community question is gone). The plan counts it at 100 words.
- **UMass-4 group label**: UMass-4 still carries `choose_group` "1 of 2" although only one option is eligible. The plan reports a one-option "group", which is confusing but harmless.
- **Tufts minimums**: Tufts word minimums (75 and 100) are not carried into the plan.
- **Wesleyan display flag**: Wesleyan has `no_supplement: false` in schools.json, but the student has no Wesleyan prompt, so the display is inconsistent.
- **URI prompt vintage**: URI prompts are the 2025-26 versions (cycle field). This does not affect this student.

### LOW 13. Model artifact in the deferral scenario
- URI comes out at 98.6% after a Tufts *deferral* but 98.4% after a Tufts *acceptance*.
- Cause: the admit likelihood includes the lapse term (S-independent), while the defer band does not.
- The effect is small, but a counselor reading the table will notice that a deferral looks better than an admit.

### LOW 14. Data points worth a caption
- Northeastern's CDS C7 says "Very Important" while the school is test-optional. That is as published, but it drives finding 4.
- The Tufts C1 totals disagree slightly with the residency table (33,395 vs 33,415).
- The URI C21 ED counts sit under a "Fall 2024" label.
- None of these changes a rate by more than 0.1 pp.
