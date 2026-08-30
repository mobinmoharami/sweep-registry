# SW-0010 — Hour-of-day seasonality on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Hour-of-day effects produce no risk-adjusted edge after realistic costs. Calendar effects are among the easiest patterns to find by accident, which makes an explicit multiple-testing correction essential rather than optional.

## What was searched

- Families: intraday_seasonality
- Variants tested: 552
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.6465 |
| Expected best if nothing works | 5.7551 |
| Needed to clear threshold | 8.9759 |
| **Detection limit** | **11.0759** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.0000** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -5.076 | -4.3993 | -3.6289 | -1.4615 | -0.003 | 0.3614 | 0.6465 |

Share of variants with positive Sharpe: 24.8%

## How to read this

This sweep could have detected a true annualised Sharpe of **11.0759** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `84f9fd6686414b0bbc3e417c55d48dad61a9b7f787c465959c3d83b5bcaf2e13`
- Result sha256: `dc492ac635f2d072b1c71d3d8299d8c3c2d7dd3a42d956274f0d0a11e58384d0`
- Finalised: 2026-08-01T07:01:10+00:00
- Evidence: returns_matrix
- NOTE: Trial count differs from pre-registration: declared 576, supplied 552. Explain this in the record.
