# SW-0020 — Break of structure on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

A decisive break of structure is claimed to signal a directional regime change. Stated mechanically: A close beyond the prior lookback-bar extreme by at least entry_threshold ATR(14). This is the only market-structure concept with a fixed definition; anything requiring a chosen swing point or higher-timeframe bias is deliberately excluded as untestable. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: break_of_structure
- Variants tested: 540
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.6929 |
| Expected best if nothing works | 1.7086 |
| Needed to clear threshold | 2.2903 |
| **Detection limit** | **2.5882** |

Deflated Sharpe Ratio: **0.482326** (threshold 0.95)

Probability of Backtest Overfitting: **0.0110** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -2.4663 | -0.7845 | -0.3407 | -0.016 | 0.3653 | 0.9205 | 1.6929 |

Share of variants with positive Sharpe: 48.1%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.5882** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `16ef3eb41274d97e1e6cc1afbd8d51cb38521b7d2ca8a2ce6a2a2b2d967e5329`
- Result sha256: `8665108a9d34ebdfcb4cc5354812c60274d40896c003d984b7fd7291e9e11c88`
- Finalised: 2026-08-01T16:37:55+00:00
- Evidence: returns_matrix
