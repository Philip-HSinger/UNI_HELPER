# UNIMATH product fact sheet (seller's ONLY source of truth)

Everything a seller says must be supported by this sheet. Anything not here is unknown: say "I don't know" or
"not yet". Never invent customers, testimonials, partnerships, results on real students, or features.

## What it is
- UNIMATH v0.1: an admissions-analytics tool. Today it is a command-line program / Python library that runs on the
  user's own computer (Bloomberg-terminal style: short commands, dense tables). No web app for counselors yet.
- Separately, a free student-facing web page exists ("Application Efficiency Guide") with a 5-school free cap and a
  waitlist. It is basic.
- Made by a solo founder. New product, no paying customers, no client references yet.

## What it does (honest status)
- Odds per school for 412 four-year US colleges (SAT bands + admit rates from the US Dept. of Education College
  Scorecard; 19 selective schools hand-curated). Uses the counselor's own 0-100 read of the student as an input.
- Treats a student's decisions as linked (same application read everywhere), so it flags lists where the risk of
  zero admits is higher than multiplying odds suggests. Shows the risk as a range.
- Re-prices remaining schools after each early decision/deferral/waitlist (Bayesian update).
- Screens a whole caseload from one CSV; writes a counselor brief (numbers) and a family brief (plain words).
- Essay planning: maps which supplement prompts overlap so students reuse drafts. STATUS: only 10 prompt pairs are
  human-scored so far (19 schools have prompts loaded); the automatic overlap scoring did NOT beat chance in testing.
  The founder is building a human-scored map for the 50-100 most-applied schools; not done.
- Freezes forecasts in a tamper-evident log so they can be graded against real outcomes in spring.
- Can score a counselor's past reach/target/likely calls against its own odds on their past class (BKTST).

## Evidence (all from simulated students, none from real outcomes)
- Multiplying odds understated zero-admit risk 4.5-8x in simulation; UNIMATH's own estimate over-warned ~2x when
  the simulated world broke its assumptions.
- Knowing a student's other decisions cut prediction error 18-24% in simulation.
- Single-school odds were only ~7% better than a simple statistical model; a counselor's own judgement beats a
  scores-only model; one class of ~25 students cannot statistically prove any method better.
- A 25-page methods manual documents all tests, including failures.

## Not available
- No CollegePlannerPro / Naviance / Scoir / SIS integration (CSV export/import only).
- Early-decision rates only approximated. No GPA/rigor/activities inputs beyond the counselor's single rating.
- No mobile app, no SSO, no SOC 2 / formal security audit, no student-data privacy certification.

## Data handling
- Runs locally by default; needs no student names. Optional opt-in pooling of de-identified outcomes (draft terms,
  not yet lawyer-reviewed).

## Pricing (TEST PRICES under evaluation; seller may quote these, must say they are introductory)
- Individual counselor: $390/year; founding-counselor offer: free through May, pay only if continuing.
- School site licence (up to 10 counselors): $1,500/year.
- Platforms/companies wanting the engine (API or licence): price negotiable; nothing packaged yet.
- Families direct: not currently sold.
