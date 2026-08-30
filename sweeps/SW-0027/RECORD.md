# SW-0027 — Engulfing candle on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

The oldest published candlestick reversal pattern. Stated mechanically: A bar whose body fully covers the previous bar's body in the opposite direction, with body size at least entry_threshold times the trailing average body over lookback bars. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: engulfing
- Variants tested: 810
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.6845 |
| Expected best if nothing works | 8.3869 |
| Needed to clear threshold | 16.193 |
| **Detection limit** | **21.6327** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.0003** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -10.2008 | -7.6726 | -5.2431 | -3.4155 | -0.5116 | 0.1703 | 0.6845 |

Share of variants with positive Sharpe: 8.4%

## How to read this

This sweep could have detected a true annualised Sharpe of **21.6327** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `34c3319084b5c14c40259be9f3ef640adb419fc704fab76427b9fd96c1802d90`
- Result sha256: `256f1573539c4b2ffa66ac6f46f49b3e340815e292469177169b3b03b1b288b5`
- Finalised: 2026-08-01T16:50:20+00:00
- Evidence: returns_matrix
