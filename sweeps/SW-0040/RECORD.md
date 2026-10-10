# SW-0040 — Cross-sectional reversal across a point-in-time top-20 crypto universe, hourly

**Verdict: NO EDGE FOUND**

Short-horizon cross-sectional reversal is the standard competing hypothesis to momentum, and is claimed to dominate at shorter rebalance intervals. Stated mechanically: Identical to cross-sectional momentum with the ranking inverted: long the worst trailing performers, short the best. Two things make this sweep different from every earlier one in this registry. First, a cross-sectional dollar-neutral portfolio cannot inherit a market trend, so the Bitcoin uptrend that contaminated the time-series crypto results cannot produce an effect here. Second, the universe is rebuilt monthly from the previous month's volume, so coins that later died are held while they lived. Ammann, Burdorf, Liebi and Stockl (SSRN 4287573) measured an annualised survivorship bias of 62.19% for equal-weighted crypto portfolios; taking today's top 20 and backtesting them would make almost any result meaningless.

## What was searched

- Families: xs_reversal
- Variants tested: 45
- Symbols: point-in-time top 20 by prior-month quote volume
- Period: 2019-02-01 to 2025-06-30 (1h, 56,126 observations)
- Costs: 4.0 bps, slippage 6.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Equal-weighted and dollar-neutral: the long and short legs are the same size and are drawn only from assets investable in that month. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | -0.2034 |
| Expected best if nothing works | 1.0116 |
| Needed to clear threshold | 1.6273 |
| **Detection limit** | **1.9411** |

Deflated Sharpe Ratio: **0.001166** (threshold 0.95)

Probability of Backtest Overfitting: **0.3477** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -1.9155 | -1.805 | -1.2954 | -0.9393 | -0.6203 | -0.4062 | -0.2034 |

Share of variants with positive Sharpe: 0.0%

## How to read this

This sweep could have detected a true annualised Sharpe of **1.9411** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `c9f6e0e88b84fc0af5fa9d5f6333a2b9535b144b39fdadf36102e0d1afdf01f1`
- Result sha256: `c85396c91c5ecd6cc642597d7b39f622b0b89d11e52ce17978b118d2bdf431b0`
- Finalised: 2026-10-10T18:20:08+00:00
- Evidence: returns_matrix
