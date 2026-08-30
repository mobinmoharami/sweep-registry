# SW-0006 — Donchian channel breakout on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Turtle-style channel breakouts produce no risk-adjusted edge after realistic costs, and no detectable directional tilt across the family.

## What was searched

- Families: donchian_breakout
- Variants tested: 432
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.1339 |
| Expected best if nothing works | 1.2107 |
| Needed to clear threshold | 1.8 |
| **Detection limit** | **2.1018** |

Deflated Sharpe Ratio: **0.414965** (threshold 0.95)

Probability of Backtest Overfitting: **0.1240** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -1.047 | -0.4934 | -0.2282 | 0.103 | 0.3829 | 0.7534 | 1.1339 |

Share of variants with positive Sharpe: 54.6%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.1018** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `076eab07fff7b663e25da49665b5cb1fe4cb29037864bb30e483360d751cdca3`
- Result sha256: `bec696140a47d5af1ff338a4f2887b8983e985d35b3aa8aeeb92975d32c47fd3`
- Finalised: 2026-08-01T06:56:47+00:00
- Evidence: returns_matrix
