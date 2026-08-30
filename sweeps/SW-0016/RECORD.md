# SW-0016 — Hour-of-day seasonality on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Hour-of-day effects produce no risk-adjusted edge after realistic costs. Calendar effects are among the easiest patterns to find by accident, which makes an explicit multiple-testing correction essential rather than optional. This is the out-of-market replication of SW-0010: identical search space, identical protocol, different asset class. Crypto results to date come from a single market over a single period, so they are not independent evidence of anything general. FX has different participants, different microstructure and far lower costs. If the pattern found in crypto is a property of markets rather than of that one sample, it should appear here too.

## What was searched

- Families: intraday_seasonality
- Variants tested: 828
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.7871 |
| Expected best if nothing works | 13.9901 |
| Needed to clear threshold | 23.3056 |
| **Detection limit** | **29.4075** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.0000** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -17.6113 | -10.9144 | -7.9442 | -2.8504 | -0.2768 | 0.3809 | 0.7871 |

Share of variants with positive Sharpe: 18.2%

## How to read this

This sweep could have detected a true annualised Sharpe of **29.4075** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `df81dad18f0d1077c4a7018b4bc72a73ecd717f4cf77cc3c1fbdb3064dc74949`
- Result sha256: `af27c1e52b98f7e9044c5fd7e19190a1bbc74a2fa819966a7e10a3a1b6bfa650`
- Finalised: 2026-08-01T16:18:43+00:00
- Evidence: returns_matrix
- NOTE: Trial count differs from pre-registration: declared 864, supplied 828. Explain this in the record.
