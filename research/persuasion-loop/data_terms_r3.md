# UNIMATH data terms (DRAFT: for the founder to review with counsel before use)

1. **Default is local.** UNIMATH runs entirely on the counselor's own computer. No student data leaves it unless the
   counselor explicitly opts in to item 3.
2. **Minimum fields.** The tool needs: an internal student ID chosen by the counselor (no names), SAT section scores,
   the counselor's 0-100 rating, the school list, and decisions. It never asks for names, emails, high school, address,
   demographics or essays.
3. **Optional pooling (opt-in, revocable).** A counselor may contribute de-identified outcomes (the fields in item 2,
   with IDs re-hashed on export and scores rounded to 10) to a shared pool used only to calibrate the model. Pooled
   data is never sold, never shared with colleges, and is deleted on request within 30 days.
4. **Forecast ledger.** Frozen forecasts are hash-chained. The counselor keeps the file. The vendor keeps only the
   head hash, so either party can prove the forecasts were not changed after decisions arrived.
5. **Families.** Counselor-facing outputs are labelled "not for forwarding verbatim". The family brief uses words
   (low / moderate / high), not point probabilities, and states that the numbers are estimates.
6. **Continuity.** If the service ends, the counselor keeps the software (it runs locally) and their data. The
   catalog stops updating.
