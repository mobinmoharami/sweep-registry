# SW-0021 — Engulfing candle on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

The oldest published candlestick reversal pattern. Stated mechanically: A bar whose body fully covers the previous bar's body in the opposite direction, with body size at least entry_threshold times the trailing average body over lookback bars. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: engulfing
- Variants tested: 540
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.5527 |
| Expected best if nothing works | 4.4416 |
| Needed to clear threshold | 7.5197 |
| **Detection limit** | **9.5733** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.0069** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -5.8877 | -4.3385 | -2.7484 | -1.5601 | -0.4209 | 0.1726 | 0.5527 |

Share of variants with positive Sharpe: 10.7%

## How to read this

This sweep could have detected a true annualised Sharpe of **9.5733** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `b9a4ce83537cbac89fd21fce47c58c53c3351f3afff1ba8ed0e8c75c75b17ce4`
- Result sha256: `c08b7a93337f3ac93c2a84579b831f737f3c13d0b2aa2a5e5fd12c69e5a55089`
- Finalised: 2026-08-01T16:38:22+00:00
- Evidence: returns_matrix
