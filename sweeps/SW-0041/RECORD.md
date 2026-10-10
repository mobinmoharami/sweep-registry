# SW-0041 — Volatility-scaled cross-sectional momentum across a point-in-time top-20 crypto universe, hourly

**Verdict: NO EDGE FOUND**

Scaling by volatility is the standard refinement, on the grounds that raw returns let the most volatile assets dominate the ranking regardless of signal. Stated mechanically: As cross-sectional momentum, but assets are ranked by trailing return divided by trailing volatility rather than raw return. Two things make this sweep different from every earlier one in this registry. First, a cross-sectional dollar-neutral portfolio cannot inherit a market trend, so the Bitcoin uptrend that contaminated the time-series crypto results cannot produce an effect here. Second, the universe is rebuilt monthly from the previous month's volume, so coins that later died are held while they lived. Ammann, Burdorf, Liebi and Stockl (SSRN 4287573) measured an annualised survivorship bias of 62.19% for equal-weighted crypto portfolios; taking today's top 20 and backtesting them would make almost any result meaningless.

## What was searched

- Families: xs_vol_scaled_momentum
- Variants tested: 45
- Symbols: point-in-time top 20 by prior-month quote volume
- Period: 2019-02-01 to 2025-06-30 (1h, 56,126 observations)
- Costs: 4.0 bps, slippage 6.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Equal-weighted and dollar-neutral: the long and short legs are the same size and are drawn only from assets investable in that month. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.0431 |
| Expected best if nothing works | 0.7744 |
| Needed to clear threshold | 1.4528 |
| **Detection limit** | **1.8043** |

Deflated Sharpe Ratio: **0.74549** (threshold 0.95)

Probability of Backtest Overfitting: **0.3985** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -0.2361 | -0.1596 | 0.2478 | 0.4684 | 0.6873 | 0.9793 | 1.0431 |

Share of variants with positive Sharpe: 86.7%

## How to read this

This sweep could have detected a true annualised Sharpe of **1.8043** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `e6aad840fe4b3a4f15c0673cce445fc137638e25065abc3fc2fb40ee2bc784e3`
- Result sha256: `2fffc4c1e23f3f7011050a5262d67ece968ff6fa76f808ede4cc3b6641a796b9`
- Finalised: 2026-10-10T18:21:29+00:00
- Evidence: returns_matrix
