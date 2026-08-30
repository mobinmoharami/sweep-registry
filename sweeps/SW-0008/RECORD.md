# SW-0008 — Time-series momentum on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Time-series momentum at intraday-to-weekly horizons produces no risk-adjusted edge after realistic costs. Note this is the horizon at which momentum is LEAST documented; published crypto momentum results are mostly weekly to monthly and cross-sectional, so a null here does not contradict them.

## What was searched

- Families: momentum_roc
- Variants tested: 540
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.1117 |
| Expected best if nothing works | 2.3354 |
| Needed to clear threshold | 2.9246 |
| **Detection limit** | **3.2263** |

Deflated Sharpe Ratio: **0.00031** (threshold 0.95)

Probability of Backtest Overfitting: **0.0787** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -3.7156 | -1.7606 | -0.4949 | -0.127 | 0.2562 | 0.6312 | 1.1117 |

Share of variants with positive Sharpe: 41.5%

## How to read this

This sweep could have detected a true annualised Sharpe of **3.2263** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `c4c590c0702cba4325339dd8f78164c2249e1ea3973a81f9bbdae0193b000c64`
- Result sha256: `7a9271f088df212e794f7a80b865753807c4f5a155f8bcf98513e3bc441b28b6`
- Finalised: 2026-08-01T06:57:49+00:00
- Evidence: returns_matrix
