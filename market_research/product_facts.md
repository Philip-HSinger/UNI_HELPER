# Calliper fact sheet (seller's ONLY source of truth, v2)

Everything the seller says must be supported by this sheet. Anything not here is unknown: say "I don't know" or
"not yet". Never invent customers, testimonials, partnerships, results on real students, or features.

## Who
- Calliper is built by Philip, an electrical engineering student at Brown. New this cycle. No paying customers or
  client references yet.
- Email: calliper@agentmail.to. A detailed methods write-up exists and can be shared on request.

## What it does (status)
- Decision updates (works now): after an early admit, deferral, waitlist or rejection, it recalculates the student's
  chances at every school still on the list. It uses Bayesian probability and treats a student's applications as
  dependent (the same application is read everywhere), not as independent coin flips. Output is a range.
- List check (risk part works now): the chance of getting in nowhere, which multiplied per-school odds understate.
  Shown as a range and as low / moderate / high for families. "Which schools are cheap and worth adding" comes with
  Essay map.
- Essay map (not built yet; pilot from August 2027): maps which supplement prompts overlap, which of a student's
  essays covers which other school's prompt, and how many new words each school needs, measured from the student's
  own essays with consent. Output is a plan, never a rewritten essay.
- Inputs: test scores, GPA (being added to the model), the college list, and real decisions. No student names.
  Covers ~400 four-year US colleges from public data (US Dept. of Education College Scorecard).
- Accuracy: checked in testing; not yet checked against real outcomes. That is what this cycle's free pilot is for.
- Delivery today: Philip runs it and sends a one-page PDF report per student, usually within two days. No software to
  install, no login. Not integrated with Naviance, Scoir, CollegePlannerPro or any SIS.

## The offer
- Free now: send one senior's SAT, GPA and college list (no name, no identifying data) plus any early results; get a
  one-page report back.
- Founding-counselor pilot: free this cycle; in return, de-identified decisions in spring so the odds can be checked.
  Essay map for juniors free for 2027-28 in exchange for (consented, numbers-only) reuse data.
- After the pilot (introductory, test prices): $390 per counselor per year; $1,500 per school or firm (up to 10
  counselors). Platforms: negotiable. Families direct: not currently sold.
- Calls: happy to do a 15-minute call.

## Data handling
- No student names or identifying data. Essays only with the family's consent. Data terms are a draft, not yet
  lawyer-reviewed. No SOC 2 or formal privacy certification.

## Methods (for prospects who ask; the full write-up can be sent as a PDF)
- Per-school probit selection model calibrated to each school's published acceptance rate and admitted-student SAT
  25th/50th/75th percentiles (College Scorecard; Common Data Set for ~19 curated schools).
- Dependence: ONE shared latent "application strength" factor links all of a student's decisions (single factor,
  same for every school pair; not pair-specific). Its strength is a set parameter (default 0.3 on a 0-1 scale),
  NOT yet fitted on real joint outcomes; fitting it is what the pilot's spring data is for.
- The "3-11%" range is a sensitivity range, not a credible interval: the min and max of the no-admit risk across
  plausible settings (link strength 0.05-0.5, an unpredictability term of 2-10%, and how much of the student's
  non-test strength is unknown). The ~10% central value uses the default settings, which sit near the high end of
  those plausible values, which is why it is near the top of the range. (Presentation will be fixed.)
- Updates: Bayes' rule on the shared factor (801-point grid). A deferral/waitlist is treated as an outcome just below
  the admit cut-off, with a fixed assumed band (not school-specific).
- Test-optional: a non-submitter is given an assumed, slightly below-average imputed test level (set parameter); the
  model can suggest submit vs withhold per school. GPA not in the model yet.
- ED/EA: approximated by recalibrating to the school's early admit rate; hooked early pools (athletes, legacies)
  are not separated out.
- Not modelled: first-gen/low-income or international applicant subgroups, in-state status, intended major, net price
  or financial aid.
- Validation so far: tested on simulated students where the truth is known. Multiplying odds understated no-admit
  risk 4.5-8x; this model over-warned by up to ~2x when its assumptions were deliberately broken; using a student's
  other decisions cut prediction error 18-24%; single-school odds ~7% better than a simple logistic model. No
  backtest on real outcomes yet.
- No API, no white-label/branded reports, no consumer licence packaged yet; any of these would be a conversation.
- Data: no written retention policy yet beyond the draft data terms; nothing is shared with anyone.
