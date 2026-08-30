# SW-0007 — ATR volatility breakout on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Volatility breakout rules produce no risk-adjusted edge after realistic costs, and no detectable directional tilt across the family.

## What was searched

- Families: atr_breakout
- Variants tested: 540
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.2617 |
| Expected best if nothing works | 1.4934 |
| Needed to clear threshold | 2.0671 |
| **Detection limit** | **2.3602** |

Deflated Sharpe Ratio: **0.254761** (threshold 0.95)

Probability of Backtest Overfitting: **0.0348** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -2.4644 | -0.9063 | -0.334 | -0.0746 | 0.2317 | 0.6253 | 1.2617 |

Share of variants with positive Sharpe: 42.0%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.3602** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `8279ca8833eb2215b0e6af42afb98fd57e9e55606971f4f2e9214d16b55998d9`
- Result sha256: `0988ea96513dcf1582ccccd2565df8213704c007c3634088eb0fea5d62aced90`
- Finalised: 2026-08-01T06:57:31+00:00
- Evidence: returns_matrix
