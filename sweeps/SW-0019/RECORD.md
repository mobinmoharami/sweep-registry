# SW-0019 — Liquidity sweep on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

The most falsifiable smart-money claim: that stop hunts beyond prior extremes reverse. Stated mechanically: Price exceeds the prior lookback-bar extreme by at least entry_threshold ATR(14) intrabar, then closes back inside it. Sweeping highs traps longs, so the trade is short, and vice versa. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: liquidity_sweep
- Variants tested: 540
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.635 |
| Expected best if nothing works | 1.681 |
| Needed to clear threshold | 2.3181 |
| **Detection limit** | **2.7068** |

Deflated Sharpe Ratio: **5.7e-05** (threshold 0.95)

Probability of Backtest Overfitting: **0.1883** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -2.6951 | -1.3972 | -0.8076 | -0.3484 | -0.0238 | 0.2937 | 0.635 |

Share of variants with positive Sharpe: 23.5%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.7068** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `c0fad1a9a1c65e9dbfd5b385f4a0d84f28d6431435c95bfa552adeef962e2c02`
- Result sha256: `8992f7b54178a6f65c64e03813d8d443d39a853cb836396c98f49463fe5ce4b8`
- Finalised: 2026-08-01T16:37:27+00:00
- Evidence: returns_matrix
