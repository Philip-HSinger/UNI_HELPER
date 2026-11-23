# Pre-flight review (Manager, consultation 0)

Date: 2026-11-23. Files reviewed: protocol.md, product_facts.md, sim.py, prompts/*.md, personas.json (36
personas; full private cards read for p01, p07, p09, p15, p17, p21, p24, plus a lint scan of all 36),
public_profiles.json. I rendered a sample inbox from a scratch copy of sim.py with a dummy email, so the real
emails/ folder is still empty.

**Verdict: APPROVE WITH CHANGES.** Change 1 blocks launch. Do not start buyers until it is done and the lint in
change 1 returns zero hits.

## What is fine (no change)
- The structure is sound: separate seller and buyer agents, the orchestrator relays messages, transcripts are
  verbatim, and outcomes come from a fixed list.
- public_profiles.json holds only public fields (name, title, organization, org_type, location, public_notes).
  Segment labels, budgets and inbox habits are not exposed, so the seller cannot see private cards through it.
- The buyer card leaves out `segment`. Labels such as "(data-curious)" never reach the buyer.
- Each card includes a base open rate and a triage rule. Persona skepticism varies realistically: 2 personas are low
  (p15, p24), most are medium to high, and none is tuned to gush.
- The buyer_t0 anti-agreeableness paragraph is good. Its language about ignoring and the lack of any duty to be
  polite should stay.
- Distractors are realistic and season-appropriate. Several include competing "chances" vendor pitches (AdmitScope
  and others), which is good.
- The seller prompt is honest and allows "not yet". The fact sheet is candid about the product's limits.

## Findings

### F1 (BLOCKING): private cards were written from the fact sheet, so the product leaks to buyers
35 of the 36 cards name UNIMATH-specific facts that only the fact sheet contains. Examples:
- p17: "will notice only 10 prompt pairs scored and that auto-scoring didn't beat chance"
- p09: "Over-warns ~2x when assumptions break", "BKTST", "$390/yr is trivial", "free-through-May lets him test"
- p07: "a solo-founder product with no SOC 2, no SSO, and no references"
- p24: "Not a target buyer (families direct not sold)"
- p31: "no paying customers, solo founder, simulated-only evidence"

`sim.py card` copies these to the buyer verbatim. As a result:
1. Buyers know facts the seller never disclosed. This breaks isolation (mandate B).
2. Every buyer's objections and its "yes" condition are pre-scripted. The run would measure the persona
   generator's predictions, not reactions to the email (mandate A).
3. Price anchors such as "$390 is trivial" shape WOULD_PAY.

### F2: our email stands out in the inbox
Every distractor sender is a plain label, for example "Vendor", "Graduate student" or "AdmitScope". Ours alone
reads "Founder, UNIMATH <founder@unimath.example>": the only sender with an email address, and the `.example`
domain looks fake. The mismatch draws attention to our email and hints that the inbox is staged.

### F3: the follow-up inbox is unrealistic and gives our email more weight
For the follow-up stage, sim.py shuffles the same 11 distractors and cuts them to 8. The code comment promises
"plus some new-looking ones", but none are added. The same buyer agent therefore sees last week's emails again,
still unread, in a smaller inbox: 9 items instead of 12, so our email is 1 of 9.

### F4: inbox burial and screening are not modelled
- Only 12 items are shown, against a stated 30-200 emails a day.
- p32 has no other cold vendor pitch, and p27 has only one, so ours is the only or nearly the only cold pitch in
  those inboxes.
- Some triage rules screen mail before the person sees it: p07 (an assistant screens), p16 (a manager filters),
  p21 (cold mail often goes to spam). The simulation does not apply these screens.
- There is no calibration check. The cards' base open rates average about 9%, so roughly 3 of 36 buyers should
  open our email.

### F5: wording that nudges buyers
- buyer_t0 calls the exercise a "workplace simulation". That cues the buyer that something in the inbox is the
  item being tested.
- buyer_t0's THOUGHTS field ("mentioning any vendor emails specifically") points the buyer at vendor mail before
  it decides.
- buyer_open lists REPLY first and has no plain DELETE option. Its PRIVATE THOUGHTS field asks "what would need to
  be true for you to pay", which frames the email as a purchase decision.
- buyer_final lets the buyer report a stronger outcome (TRIAL or BUY) than anything it committed to in a message
  it actually sent.

### F6: protocol gaps
- The outcome list has no code for FORWARD or UNSUBSCRIBE.
- Nothing says that a follow-up must not be sent after an UNSUBSCRIBE.
- Nothing says that only the buyer's MESSAGE field is relayed. ACTION, DECISION_IF_ANY, PRIVATE THOUGHTS and
  internal forwarding notes must never reach the seller.
- Isolation relies on instructions only. The seller has file tools and works in the same directory as
  personas.json.

## Required changes
See the numbered CHANGES in the manager's reply. They are repeated here.

1. **(Blocking)** In `sim.py card()`, stop showing `likely_objections` and `what_would_make_them_buy` to buyers.
   Keep both in personas.json as manager-only, pre-registered predictions to compare against the outcomes later.
   Then have a fresh agent that has never seen product_facts.md rewrite `skepticism`, `dealbreakers`, `budget`,
   `tech_comfort` and `math_literacy` in general terms about vendors, tools and habits. For example, replace
   "would not use a CLI" with "uses only web apps; will not install software", and replace "$390/yr is trivial"
   with "a few hundred dollars a year is easy if useful".

   Lint (must return 0 across all 36 card outputs):
   `unimath|simulat|solo.?founder|soc ?2|\bsso\b|no (paying|customers|references)|correlated|zero.?admit|prompt pairs|methods manual|command.?line|\bcli\b|python|scorecard|\$390|\$1,?500|founding|bayesian|bktst|families direct|not sold|engine|licen[cs]e|\bapi\b|the (product|tool)`
2. In sim.py, change the inbox sender for our email to `UNIMATH` so it matches the distractor style. Drop the
   `<...@unimath.example>` address everywhere.
3. In sim.py, replace the follow-up truncation with a fresh set of distractors:
   `items = list(p["inbox_distractors_followup"])`. That is 11 new week-later items per persona, written
   without knowledge of the product. Never shrink the inbox.
4. Make sure every inbox, for both T0 and the follow-up, contains at least 2 other unsolicited vendor or marketing
   pitches. Today p32 has none and p27 has one.
   Add to buyer_t0 after the inbox: "If, under your triage rule, an email would be caught by a spam filter or
   screened out by an assistant before you saw it, list it under IGNORE."
   Calibration rule for the protocol: "If T0 opens exceed 2x the mean card open rate (more than 6 of 36), the
   manager flags inbox salience and T0 is re-run with 24-item inboxes."
5. buyer_t0: replace "You are role-playing a real person in a realistic workplace simulation." with "You are
   role-playing a specific real person." Replace the THOUGHTS line with
   "THOUGHTS: <2-3 sentences in character on how you triaged this batch>".
6. buyer_open: change the format to "ACTION: <IGNORE | DELETE | UNSUBSCRIBE | FORWARD | REPLY>" and list the
   options in that order. Replace the PRIVATE THOUGHTS line with
   "PRIVATE THOUGHTS: <2-4 sentences: your honest reaction to this email>".
7. buyer_final: add "FINAL may not be stronger than what you actually committed to in a message you sent (TRIAL only
   if you agreed to try it; BUY only if you agreed to pay)." Change WOULD_PAY to "<amount per year you would actually
   pay from a budget you control or could get approved this cycle, or 0>".
8. protocol.md:
   - Add the outcomes FORWARDED and UNSUBSCRIBED.
   - Outcomes for buyers who did not reply are assigned mechanically from their actions; buyer_final is not asked.
   - No follow-up is sent after UNSUBSCRIBE.
   - A buyer's IGNORE at T2 or later ends the thread.
   - Only the buyer's MESSAGE text is relayed to the seller.
   - The seller gets the fact sheet and the public profiles inline; seller_reply also includes the fact sheet
     inline.
   - Buyers are spawned without tools.
   - Tool-call logs are kept. Any seller or buyer read of personas.json, prompts/, transcripts/ or audit/ voids
     that run.

## What I will check at later audits
- Seller claims compared line by line with product_facts.md. In particular: pricing must be labelled introductory,
  there must be no implied customers or real-outcome results, and essay-feature limits must not be glossed over.
- Leaks in either direction, and the T0 open-rate calibration rule.
- Whether each buyer's stated outcome matches its actions, and whether any "yes" is justified by its card.
