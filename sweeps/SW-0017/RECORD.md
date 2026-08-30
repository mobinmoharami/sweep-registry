# SW-0017 — Fair value gap on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Fair value gaps mark unfilled displacement that price is claimed to return to. Stated mechanically: A three-bar imbalance: the high of bar t-2 sits below the low of bar t (bullish) or the low of bar t-2 sits above the high of bar t (bearish). entry_threshold is the minimum gap size in ATR(14) units, so gaps no wider than the spread do not count. lookback is how many bars the gap stays live; entry is price re-entering it. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: fair_value_gap
- Variants tested: 540
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.5428 |
| Expected best if nothing works | 2.2727 |
| Needed to clear threshold | 2.9779 |
| **Detection limit** | **3.3853** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.2559** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -2.3776 | -1.9849 | -1.3354 | -0.6312 | -0.0427 | 0.2837 | 0.5428 |

Share of variants with positive Sharpe: 19.4%

## How to read this

This sweep could have detected a true annualised Sharpe of **3.3853** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `abf49c7742c2713f416b4e244044baf3bc3a9f07737e32626b96593aedce9263`
- Result sha256: `ff9f0884194142ec707775504779302cbf3b7795206f90bd138026ca08556bb3`
- Finalised: 2026-08-01T16:30:54+00:00
- Evidence: returns_matrix
