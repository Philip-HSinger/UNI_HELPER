# School data (`schools.json`)

This file is the app's "database" for v1 — a plain, git-versioned JSON file. That's a deliberate
choice for reference data of this size: it's diffable, reviewable in a pull request, and needs no
server. If this later needs to be edited by non-technical people through an admin UI, swap it for
a real database table with the same shape and point `src/lib/defaults.ts`'s `CATALOG` import at an
API call instead — nothing else in the app needs to change, since every component only ever reads
`SchoolCatalogEntry` objects.

## Fields

| Field | Meaning | Source |
|---|---|---|
| `id` | stable slug, used as the catalog key | derived from name |
| `name` | display name | — |
| `platform` | Common App / Coalition / school-specific portal | school's application page |
| `testOptional` | whether SAT/ACT is optional there | school's admissions/testing policy page |
| `englishP25/50/75`, `mathP25/50/75` | SAT section score bands for enrolled students | the school's **Common Data Set (CDS), section C9** — published annually, usually as a PDF/spreadsheet on the school's institutional research site |
| `difficulty` | 1-100 subjective essay-prompt difficulty | editorial judgement — recalibrate if it feels off |
| `importance` | how much the school says it weighs standardized testing | CDS **section C7** ("Relative Importance of Academic and Nonacademic Factors") |
| `prompts` | this cycle's supplemental essay prompts | school's application portal |
| `acceptanceRate` | 0-1 admit rate | CDS **section C1**, or the Common App/IPEDS aggregate |

## Updating each admissions cycle

Common Data Sets are typically published in the winter/spring following each admissions cycle.
Once a school's new CDS is out:

1. Open `schools.json`, find the entry, update the percentile bands and acceptance rate.
2. Check whether `testOptional`/`importance` changed (policies shift year to year).
3. Replace `prompts` with the new cycle's supplemental questions once released (usually over the
   summer, from the Common App / school portal).
4. Commit as its own PR per admissions cycle so the history stays reviewable
   (e.g. `data: update 2027-28 percentiles and prompts`).

Schools users add themselves (via "Add custom school") never touch this file — they're only ever
stored in that user's own browser.
