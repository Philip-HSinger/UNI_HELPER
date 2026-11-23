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
