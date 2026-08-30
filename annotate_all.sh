#!/usr/bin/env bash
# Apply the annotations decided on 2026-08-01. Idempotent per record only in
# the sense that reruns append; edit annotations.json directly to correct.
set -euo pipefail
cd "$(dirname "$0")"
A="python3 annotate.py"

$A sweeps/SW-0002 \
  --confirmatory "Pre-registered test: does the best of 1,599 variants clear a Deflated Sharpe Ratio of 0.95? Verdict: NO. DSR 0.0, best annualised Sharpe 0.64 against an expected-under-null of 2.53 — the best variant did not even reach what pure selection produces." \
  --confirmatory "The planning assumption was wrong in a direction that made the test harder, not easier: E[max|null] was projected at 1.35 and realised at 2.53, so the variance of trial Sharpes was about 3.5x the assumption and the detection limit rose from 2.24 to 4.01. Later sweeps use the realised figure." \
  --exploratory "Mean market-neutral gross Sharpe across the family was -0.336 against a shuffled null of +0.008 +/- 0.062 (z = -5.5). This is a population statistic, not the pre-registered maximum, and pooling across variants detects far smaller effects than a maximum can." \
  --exploratory "REPLICATION FAILED. The same six families applied to EURUSD, GBPUSD and USDJPY (SW-0011 to SW-0016) produced z values between -1.47 and +1.24 — indistinguishable from zero, despite costs a quarter as large and 48,772 bars. The crypto effect did not generalise." \
  --exploratory "Most likely explanation: Bitcoin rose from about 4,000 to over 100,000 across the sample. Linear beta removal does not fully neutralise a multi-year non-linear trend. FX had no comparable trend and showed no effect." \
  --note "21 of 1,620 enumerated variants never opened a position and were excluded from scoring. Counting variants that never traded would inflate the multiple-testing penalty without adding information." \
  --note "SW-0004, frozen and Bitcoin-timestamped on 2026-07-31 and embargoed until 2027-09-30, is the independent test of this finding." \
  --supersedes "" 2>/dev/null || true

$A sweeps/SW-0003 \
  --status VOID \
  --reason "Not an independent test. The continuation families were exact position-wise inversions of SW-0002's reversion families, so every statistic returned as the precise arithmetic negative of the original to four decimal places: gross Sharpe -0.2901 became +0.2901, z of -5.542 became +5.542. An exact inversion is an identity, not a replication. Kept rather than deleted: removing a sweep because it turned out uninformative is the selective reporting this registry exists to document." \
  --note "The one thing it does establish: gross Sharpe is antisymmetric under position inversion, so any symmetric bias — costs, spread, microstructure — contributes zero to it. Combined with the shuffled-null result, that rules out lookahead as the source of the SW-0002 effect."

for sid in SW-0029 SW-0030 SW-0031; do
  $A sweeps/$sid \
    --status VOID \
    --reason "run_xs_sweep.py was OOM-killed partway through; finalize.py then scored an all-zero returns matrix, which produces DSR exactly 0.5 and prints NO EDGE FOUND. That output is indistinguishable from a genuine null result and is not one. A guard now refuses to score a matrix where every variant has Sharpe exactly zero." \
    --superseded-by "$( [ $sid = SW-0029 ] && echo SW-0032 || { [ $sid = SW-0030 ] && echo SW-0033 || echo SW-0034; } )" \
    --note "The failure mode mattered more than the sweep: a crashed run that looks like a finding is the worst thing this registry could publish."
done

$A sweeps/SW-0032 \
  --confirmatory "Pre-registered test: does the best of 90 cross-sectional momentum variants clear DSR 0.95? Verdict: NO. DSR 0.809 — the closest any sweep in this registry has come, and still short." \
  --exploratory "96% of variants were positive with a median annualised Sharpe of 0.51 and a best of 0.98 against an expected-under-null of 0.64. The family behaves as one thing rather than as a spread of better and worse rules." \
  --exploratory "PBO is 0.479, near the 0.5 coin-flip line. Choosing among these 90 variants carries almost no information out of sample. That is consistent with a uniform family-wide effect and inconsistent with some variants genuinely being better." \
  --exploratory "The effect comes from the stable end of the universe, not the volatile end. Splitting by symbol lifetime: 81 long-lived symbols (>40,000 bars) give a net Sharpe of 0.72, while 55 short-lived symbols (<20,000 bars) give 0.04. A spurious altcoin-volatility artefact would show the opposite, and the effect is stronger where liquidity is better." \
  --note "This is the only family in 33 records to show a coherent signal, and it is also the only one with substantial published academic support in crypto. The test cannot confirm it: the detection limit is around 1.6 annualised Sharpe and the observed effect is roughly 0.7." \
  --note "SW-0035, embargoed until 2029-06-30, is the holdout test — and its pre-registration states up front that it is underpowered. Confirming a true Sharpe of 0.72 at z=2 with 80% power needs roughly 136,000 hourly bars, about 15.6 years. Four years gives about 29%."

$A sweeps/SW-0034 \
  --confirmatory "Pre-registered test: DSR 0.823 against a 0.95 threshold. Verdict: NO." \
  --exploratory "Marginally stronger than plain cross-sectional momentum (SW-0032, DSR 0.809), consistent with the standard argument that scaling by volatility stops the most volatile assets dominating the ranking. The difference is far too small to call a result." \
  --note "A numpy 'Degrees of freedom <= 0' warning appears during this sweep. It comes from all-NaN columns — symbols not yet listed — passing through nanstd. Those columns return NaN and are dropped by the ranking, so the result is unaffected."

echo
echo "annotated. review with: head -60 sweeps/SW-0032/RECORD.md"
