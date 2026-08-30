# SW-0025 — Liquidity sweep on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

The most falsifiable smart-money claim: that stop hunts beyond prior extremes reverse. Stated mechanically: Price exceeds the prior lookback-bar extreme by at least entry_threshold ATR(14) intrabar, then closes back inside it. Sweeping highs traps longs, so the trade is short, and vice versa. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: liquidity_sweep
- Variants tested: 810
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.8528 |
| Expected best if nothing works | 2.5049 |
| Needed to clear threshold | 3.3891 |
| **Detection limit** | **3.9784** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.5733** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -4.8543 | -2.0157 | -0.8336 | -0.41 | 0.0026 | 0.3903 | 0.8528 |

Share of variants with positive Sharpe: 25.3%

## How to read this

This sweep could have detected a true annualised Sharpe of **3.9784** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `6fd874183daf83dbafc05e4afa54e3318697b8a056ee99c29a6f2823bfe812c3`
- Result sha256: `35a216f47a9d0b8521c39769e42304c71ea3f3d18426705deef7321967b4608d`
- Finalised: 2026-08-01T16:49:26+00:00
- Evidence: returns_matrix
