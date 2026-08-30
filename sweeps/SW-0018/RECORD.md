# SW-0018 — Order block on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Order blocks are claimed to mark institutional accumulation that supports price on a retest. Stated mechanically: The last opposite-direction bar before a displacement move: a down bar immediately followed by an up move of at least entry_threshold ATR(14) is a bullish block. Entry is price returning to that bar's low. lookback is how long the block stays live. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: order_block
- Variants tested: 504
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.3492 |
| Expected best if nothing works | 3.498 |
| Needed to clear threshold | 5.689 |
| **Detection limit** | **7.1207** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.0978** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -4.4185 | -3.269 | -2.3297 | -1.071 | -0.4439 | 0.1694 | 0.3492 |

Share of variants with positive Sharpe: 7.7%

## How to read this

This sweep could have detected a true annualised Sharpe of **7.1207** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `ebf30dd8682781f6f435caed6bd7e8e29dafcde9dd7c070184070465206b5b82`
- Result sha256: `5899fae438f0ac43fba5293c886ae97a34d1f74a42842a09fefdbaaac626f212`
- Finalised: 2026-08-01T16:34:19+00:00
- Evidence: returns_matrix
- NOTE: Trial count differs from pre-registration: declared 540, supplied 504. Explain this in the record.
