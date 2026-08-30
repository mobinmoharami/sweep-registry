# SW-0022 — Inside bar breakout on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Range contraction is claimed to precede expansion in a predictable direction. Stated mechanically: One or more consecutive bars contained within the prior bar's range, followed by a close beyond that range by entry_threshold ATR(14). lookback//10 sets how many consecutive inside bars are required. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: inside_bar_breakout
- Variants tested: 261
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.4101 |
| Expected best if nothing works | 1.4399 |
| Needed to clear threshold | 2.2668 |
| **Detection limit** | **2.7371** |

Deflated Sharpe Ratio: **0.002186** (threshold 0.95)

Probability of Backtest Overfitting: **0.3023** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -2.7697 | -1.3806 | -0.6872 | -0.4067 | -0.1094 | 0.1661 | 0.4101 |

Share of variants with positive Sharpe: 13.0%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.7371** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `eaf544abcb9384c8e6cc63d86f51622e63f1b866f932f5d64d54dc3647b77c30`
- Result sha256: `d5e5c571711a773b39b224e6546bf2d0d6741fa067c6b8fa8cfa05308e434213`
- Finalised: 2026-08-01T16:38:59+00:00
- Evidence: returns_matrix
- NOTE: Trial count differs from pre-registration: declared 540, supplied 261. Explain this in the record.
