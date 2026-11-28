Subject: A Python library for correlated admissions risk

Hi Jonathan,

You write about admissions statistics, so I'll skip the pitch and give you the model.

UNIMATH is a Python library/CLI that treats a student's decisions as correlated (one application, read everywhere). In simulation, multiplying odds understated zero-admit risk 4.5-8x; my own estimate over-warned ~2x when the simulated world broke its assumptions, so it reports a range. Conditioning on a student's other decisions cut prediction error 18-24%, again in simulation. Single-school odds were only ~7% better than a simple model, and a counselor's judgment (a 0-100 input) beats a scores-only model.

It covers 412 US colleges from College Scorecard data, 19 selective ones hand-curated. No real outcomes yet, no customers. The 25-page methods manual includes the failures.

Founding counselors use it free through May ($390/year introductory after). Would you try it on your seniors and tell me where it breaks?

[Founder name], UNIMATH
