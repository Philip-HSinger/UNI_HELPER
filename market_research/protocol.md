# Simulation protocol

Roles (all separate subagents; the orchestrator relays messages and keeps transcripts):
1. Persona generator: builds personas.json (public profile + private card + inbox habits + distractor inbox).
2. Manager: approves this protocol before launch; audits every transcript; can invalidate a run.
3. Seller: sees ONLY public_profiles.json + product_facts.md. Writes one cold email per prospect and replies to
   threads. Must stay truthful to the fact sheet.
4. Buyers: one brand-new agent per persona. No tools, no files. Sees only its own private card and messages relayed
   by the orchestrator. Never sees the seller's instructions or other buyers.

Stages per buyer:
  T0  inbox triage: ~12 emails shown as sender | subject | first ~140 chars, ours in a random position.
      Decide OPEN or IGNORE for each relevant item (only ours is tracked).
  T1  if opened: full email shown -> REPLY (with text) / IGNORE / FORWARD-INTERNALLY / UNSUBSCRIBE.
  T1b if not replied: one follow-up 7 days later in a fresh inbox snapshot (same rules).
  T2+ if replied: up to 2 seller<->buyer exchanges, then the buyer states a final outcome.
Outcomes: GHOSTED (never opened) / READ-NO-REPLY / DECLINED / INTERESTED-NO-COMMIT / TRIAL / BUY.

Anti-agreeableness rules for buyers: realistic busy professional; most cold vendor email is ignored; no obligation
to be polite or to engage; budget and approval constraints are real; a "yes" must be justified by the private card.

## Changes after manager pre-flight review (audit/00_preflight.md)
- Outcomes also include FORWARDED and UNSUBSCRIBED. No follow-up after UNSUBSCRIBE or DELETE.
- For buyers who never replied, the outcome comes from their recorded actions, not from buyer_final.
- A buyer IGNORE at T2 or later ends the thread.
- Only the buyer's MESSAGE text is relayed to the seller; ACTION, DECISION_IF_ANY, PRIVATE THOUGHTS and internal
  forwarding notes are never relayed.
- The seller receives the fact sheet and the public profiles inline (initially and in every reply prompt).
- Buyers run as the tool-less `sim-buyer` agent type, so they cannot read any file.
- Buyer cards show only `private_buyer_view` (written without product knowledge; `python sim.py lint` must return 0).
  `likely_objections` / `what_would_make_them_buy` stay manager-only predictions, compared with outcomes afterwards.
- Every inbox holds at least 2 other vendor pitches; the follow-up week uses 11 fresh distractors.
- If more than 6 of 36 buyers open our email at T0 (2x the cards' ~9% average open rate), T0 is re-run with
  24-item inboxes.
