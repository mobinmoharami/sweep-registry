# SW-0009 — Volatility-filtered momentum on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Restricting momentum to low-volatility regimes — the standard 'it works if you filter for the right regime' claim — produces no risk-adjusted edge after realistic costs.

## What was searched

- Families: vol_regime_momentum
- Variants tested: 360
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.9623 |
| Expected best if nothing works | 1.797 |
| Needed to clear threshold | 2.3807 |
| **Detection limit** | **2.6793** |

Deflated Sharpe Ratio: **0.009529** (threshold 0.95)

Probability of Backtest Overfitting: **0.2058** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -2.5916 | -1.292 | -0.5858 | -0.1279 | 0.213 | 0.7015 | 0.9623 |

Share of variants with positive Sharpe: 38.1%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.6793** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `3ea145e90bdf0d3a054541c0db7921ea57cb979ede800bf880d55815c5edc28b`
- Result sha256: `ed2db7b4bea7da3099830a689e2de2c40c8c9bf3e1c72af3bf6f00d62ff8e22c`
- Finalised: 2026-08-01T06:58:19+00:00
- Evidence: returns_matrix
