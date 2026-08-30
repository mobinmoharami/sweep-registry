# SW-0031 — Volatility-scaled cross-sectional momentum across a point-in-time top-20 crypto universe, hourly

**Verdict: NO EDGE FOUND**

Scaling by volatility is the standard refinement, on the grounds that raw returns let the most volatile assets dominate the ranking regardless of signal. Stated mechanically: As cross-sectional momentum, but assets are ranked by trailing return divided by trailing volatility rather than raw return. Two things make this sweep different from every earlier one in this registry. First, a cross-sectional dollar-neutral portfolio cannot inherit a market trend, so the Bitcoin uptrend that contaminated the time-series crypto results cannot produce an effect here. Second, the universe is rebuilt monthly from the previous month's volume, so coins that later died are held while they lived. Ammann, Burdorf, Liebi and Stockl (SSRN 4287573) measured an annualised survivorship bias of 62.19% for equal-weighted crypto portfolios; taking today's top 20 and backtesting them would make almost any result meaningless.

## What was searched

- Families: xs_vol_scaled_momentum
- Variants tested: 90
- Symbols: point-in-time top 20 by prior-month quote volume
- Period: 2019-02-01 to 2025-06-30 (1h, 56,126 observations)
- Costs: 4.0 bps, slippage 6.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Equal-weighted, dollar-neutral unless exit_rule is long-only. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.0 |
| Expected best if nothing works | 0.0 |
| Needed to clear threshold | 0.6498 |
| **Detection limit** | **0.9823** |

Deflated Sharpe Ratio: **0.5** (threshold 0.95)

Probability of Backtest Overfitting: **0.0000** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Share of variants with positive Sharpe: 0.0%

## How to read this

This sweep could have detected a true annualised Sharpe of **0.9823** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `b3b1e8b2198a35552b40607854791b4f2c99cbfe899f2379cbaac41372e6d8d2`
- Result sha256: `8a4431c8aec274e6f912f8ff517951e67faf447a8cd9fad950d32632b0d4cd5d`
- Finalised: 2026-08-01T20:26:55+00:00
- Evidence: returns_matrix

<!-- annotations -->

## Status: VOID

run_xs_sweep.py was OOM-killed partway through; finalize.py then scored an all-zero returns matrix, which produces DSR exactly 0.5 and prints NO EDGE FOUND. That output is indistinguishable from a genuine null result and is not one. A guard now refuses to score a matrix where every variant has Sharpe exactly zero.

## Notes

- The failure mode mattered more than the sweep: a crashed run that looks like a finding is the worst thing this registry could publish.

## Related records

- Superseded by SW-0034

---

*Annotations added 2026-08-01T22:45:25+00:00. The frozen pre-registration, its hash and result.json are unmodified.*
