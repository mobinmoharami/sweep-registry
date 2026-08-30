# SW-0024 — Order block on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Order blocks are claimed to mark institutional accumulation that supports price on a retest. Stated mechanically: The last opposite-direction bar before a displacement move: a down bar immediately followed by an up move of at least entry_threshold ATR(14) is a bullish block. Entry is price returning to that bar's low. lookback is how long the block stays live. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: order_block
- Variants tested: 810
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.8743 |
| Expected best if nothing works | 7.4646 |
| Needed to clear threshold | 10.7381 |
| **Detection limit** | **12.7912** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.0029** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -8.5286 | -6.6747 | -4.2122 | -2.1981 | -0.3992 | 0.3375 | 0.8743 |

Share of variants with positive Sharpe: 12.6%

## How to read this

This sweep could have detected a true annualised Sharpe of **12.7912** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `6c29e5b0c4bdfc8a9fde45fd0674bcb1503609fbf8ab85893d972c37e078fb77`
- Result sha256: `c8a1ac278b52daca6c545eb8bb64d0151f80e016d133a12bd875728f49ccb95c`
- Finalised: 2026-08-01T16:46:06+00:00
- Evidence: returns_matrix
