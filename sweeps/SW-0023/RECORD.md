# SW-0023 — Fair value gap on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Fair value gaps mark unfilled displacement that price is claimed to return to. Stated mechanically: A three-bar imbalance: the high of bar t-2 sits below the low of bar t (bullish) or the low of bar t-2 sits above the high of bar t (bearish). entry_threshold is the minimum gap size in ATR(14) units, so gaps no wider than the spread do not count. lookback is how many bars the gap stays live; entry is price re-entering it. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: fair_value_gap
- Variants tested: 810
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.6496 |
| Expected best if nothing works | 4.6333 |
| Needed to clear threshold | 7.0298 |
| **Detection limit** | **8.597** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.0353** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -5.821 | -4.2834 | -2.3478 | -0.9569 | -0.3393 | 0.3501 | 0.6496 |

Share of variants with positive Sharpe: 12.0%

## How to read this

This sweep could have detected a true annualised Sharpe of **8.597** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `fe901a0195aa739ec9fc771f773c12cc4b5672aa17338e1bc7a693a1e125271b`
- Result sha256: `edb0183791fefb22eb4a6dd007eba91f4f9c3c02aaa66e1eb33a57c54321bcde`
- Finalised: 2026-08-01T16:42:31+00:00
- Evidence: returns_matrix
