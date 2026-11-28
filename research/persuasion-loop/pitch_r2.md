Subject: Your reach/target/likely calls, turned into odds and a zero-admit risk check

Hi [name],

I'm [founder name] at [company]. [One true line of background about the founder.] We make UNIMATH, an
admissions-analytics tool for independent counselors.

What it does, and what it doesn't
- It does NOT try to out-guess you. In our own simulations, a counselor who knows the student beats any model that
  only sees test scores. So UNIMATH uses your read of each student (one rating per student) plus their scores and
  each school's published data, and turns that into odds for every school on the list.
- It flags lists where the risk of no admits is higher than it looks. Most tools multiply each school's odds as if
  they were separate coin flips. But the same application is read everywhere, so outcomes move together. In every
  simulated scenario we tested, multiplying odds understated zero-admit risk by about 4-8x. Our own estimate can also be
  off (it over-warned about 2x in our hardest test), so the tool shows a range, e.g. "no admits: 3-11%, central 10%",
  never a single false-precision number.
- After each early result, deferral or waitlist, it re-prices every remaining school.
- It writes a plain-English paragraph per student that you can paste into a family email.

Coverage: admission odds for 412 four-year schools (US Department of Education College Scorecard data), and
hand-checked supplements for 19 selective schools. Early-decision/early-action rates are not modelled separately
yet; the essay-overlap estimate is experimental and failed our own accuracy test, so it's labelled as such.

What we can't promise: proof on your own data from one class. Our power analysis (in the manual) shows that a
25-student backtest can't reliably tell any two forecasting methods apart, and anyone who says otherwise is
overselling. Every accuracy number in our manual is simulated, and labelled as such.

What we offer instead
- Founding-counselor terms [pricing to be set by the founder]: use it this cycle, and we freeze your forecasts in
  October in a tamper-evident log. In May we grade them together against what actually happened. Pay $390 only if
  you want to continue.
- Data: it needs only scores, the school list, decisions and your rating, with no names. It runs on your own laptop
  (command line), or we run it with you over a screen-share. With your opt-in consent, de-identified outcomes join a
  shared pool so the model can be calibrated on real decisions across many practices.

Methods manual, including what failed: [link]. This is a new product with no client references yet.

[Name]
[Company, address, website]
