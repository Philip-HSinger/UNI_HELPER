Subject: A chancing model you can actually audit — calibrated on your own clients' outcomes

Hi,

I build UNIMATH, an admissions analytics terminal for independent college counselors.

The problem: every chancing tool your families use (CollegeVine, Naviance scattergrams, list
"graders") gives a single percentage per school and then treats schools as independent. That is
mathematically wrong in a way that matters for your liability: admissions decisions at similar
schools are strongly correlated (same student, same essays, same recommendations). For a typical
1540 applicant with nine schools, multiplying the per-school odds says 98% chance of at least one
admit; a correlated model says 90%. One in ten of those families gets zero admits, and a list
built on the 98% number never warned them.

What UNIMATH does:
- PCTL  Score percentiles against each school's real distribution (skew- and 800-ceiling-aware, with
        test-measurement-error intervals), not a symmetric bell curve through the 25/75.
- CHNC  Per-school admission probability from a selection model calibrated to each school's
        acceptance rate and admitted-score band, with an uncertainty band and a submit/withhold call
        for test-optional schools.
- XADM  Cross-admit matrix: "if she's admitted to Stanford, her Princeton odds go from 20% to 50%".
- DEC/UPDT  Enter decisions as they arrive (ED/EA, deferrals, waitlists); every remaining school
        updates by Bayes' rule. Useful for ED-II and deposit decisions.
- PORT  Full distribution of number of admits, not just "safety / target / reach".
- ESSY/FREE  Essay-reuse matrix across the supplements of the 19 schools currently covered (more each month): which schools are nearly free given
        the essays the list already requires, and which add 1,500 new words.
- PLAN  List optimizer: maximize expected value of the best admit minus essay workload.
- FIT   Upload your past clients' outcomes (CSV from your CRM). UNIMATH refits the model to your
        practice and reports held-out Brier score, log loss and calibration, so you know how good
        the numbers are before you show them to a family.
- Every number is decomposable (SCH, SENS): you can show a parent exactly why.

It runs in a terminal (Bloomberg-style function codes) or as a Python library; JSON output plugs
into your own reports.

Pricing: $49/month per counselor, or $390/year. Includes the school catalog and prompt-similarity
matrix updated each cycle (prompts are re-curated every August when supplements drop), and a
40-page methods manual with backtest results.

Happy to run your current senior class through it for free so you can compare against what you
told them.

— The UNIMATH team
