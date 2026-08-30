# SW-0002 — Short-horizon mean reversion on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Price-based short-horizon mean reversion produces no risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for.

## What was searched

- Families: zscore_reversion, rsi_reversion, bollinger_touch
- Variants tested: 1,599
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.6396 |
| Expected best if nothing works | 2.5334 |
| Needed to clear threshold | 3.4488 |
| **Detection limit** | **4.0146** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.1978** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -3.3301 | -1.9437 | -1.1949 | -0.5542 | 0.0326 | 0.3507 | 0.6396 |

Share of variants with positive Sharpe: 27.0%

## How to read this

This sweep could have detected a true annualised Sharpe of **4.0146** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `4fc000f556164e9c51eb53e1dc886888ef40d08a836cc59af971e100fd3fb7cf`
- Result sha256: `c2ac1fc7b4b2c615b2ca6cb113e7fad0007193474bd590ab29663db25f41f328`
- Finalised: 2026-07-31T23:35:40+00:00
- Evidence: returns_matrix
- NOTE: Trial count differs from pre-registration: declared 1,620, supplied 1,599. Explain this in the record.

<!-- annotations -->

## What was pre-registered

Pre-registered test: does the best of 1,599 variants clear a Deflated Sharpe Ratio of 0.95? Verdict: NO. DSR 0.0, best annualised Sharpe 0.64 against an expected-under-null of 2.53 — the best variant did not even reach what pure selection produces.

The planning assumption was wrong in a direction that made the test harder, not easier: E[max|null] was projected at 1.35 and realised at 2.53, so the variance of trial Sharpes was about 3.5x the assumption and the detection limit rose from 2.24 to 4.01. Later sweeps use the realised figure.

## Exploratory — NOT pre-registered

Everything in this section was noticed by looking at the finished result. It is a hypothesis, not a finding, and it carries no multiple-testing correction of its own.

Mean market-neutral gross Sharpe across the family was -0.336 against a shuffled null of +0.008 +/- 0.062 (z = -5.5). This is a population statistic, not the pre-registered maximum, and pooling across variants detects far smaller effects than a maximum can.

REPLICATION FAILED. The same six families applied to EURUSD, GBPUSD and USDJPY (SW-0011 to SW-0016) produced z values between -1.47 and +1.24 — indistinguishable from zero, despite costs a quarter as large and 48,772 bars. The crypto effect did not generalise.

Most likely explanation: Bitcoin rose from about 4,000 to over 100,000 across the sample. Linear beta removal does not fully neutralise a multi-year non-linear trend. FX had no comparable trend and showed no effect.

## Notes

- 21 of 1,620 enumerated variants never opened a position and were excluded from scoring. Counting variants that never traded would inflate the multiple-testing penalty without adding information.

- SW-0004, frozen and Bitcoin-timestamped on 2026-07-31 and embargoed until 2027-09-30, is the independent test of this finding.

---

*Annotations added 2026-08-01T22:45:25+00:00. The frozen pre-registration, its hash and result.json are unmodified.*
