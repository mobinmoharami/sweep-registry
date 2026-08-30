# SW-0005 — Moving average crossover on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Moving average crossovers — the single most widely sold technical rule — produce no risk-adjusted edge after realistic costs, and no detectable directional tilt across the family, once selection over the full parameter space is accounted for.

## What was searched

- Families: ma_cross
- Variants tested: 630
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.9575 |
| Expected best if nothing works | 1.2279 |
| Needed to clear threshold | 1.8159 |
| **Detection limit** | **2.1169** |

Deflated Sharpe Ratio: **0.224649** (threshold 0.95)

Probability of Backtest Overfitting: **0.1753** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -0.7645 | -0.5499 | -0.2567 | 0.0569 | 0.3288 | 0.7 | 0.9575 |

Share of variants with positive Sharpe: 54.4%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.1169** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `006ad69488fce6ff9133d5b846f91bdaf7ee3cedda963a58166612e10d0d6dc6`
- Result sha256: `d80cd0de042d4b6d2d9018f331c58c1f0234fad1cb59239a4460b17f1fe16ffa`
- Finalised: 2026-08-01T06:56:18+00:00
- Evidence: returns_matrix
