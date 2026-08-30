# SW-0033 — Cross-sectional reversal across a point-in-time top-20 crypto universe, hourly

**Verdict: NO EDGE FOUND**

Short-horizon cross-sectional reversal is the standard competing hypothesis to momentum, and is claimed to dominate at shorter rebalance intervals. Stated mechanically: Identical to cross-sectional momentum with the ranking inverted: long the worst trailing performers, short the best. Two things make this sweep different from every earlier one in this registry. First, a cross-sectional dollar-neutral portfolio cannot inherit a market trend, so the Bitcoin uptrend that contaminated the time-series crypto results cannot produce an effect here. Second, the universe is rebuilt monthly from the previous month's volume, so coins that later died are held while they lived. Ammann, Burdorf, Liebi and Stockl (SSRN 4287573) measured an annualised survivorship bias of 62.19% for equal-weighted crypto portfolios; taking today's top 20 and backtesting them would make almost any result meaningless.

## What was searched

- Families: xs_reversal
- Variants tested: 90
- Symbols: point-in-time top 20 by prior-month quote volume
- Period: 2019-02-01 to 2025-06-30 (1h, 56,126 observations)
- Costs: 4.0 bps, slippage 6.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Equal-weighted, dollar-neutral unless exit_rule is long-only. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.2872 |
| Expected best if nothing works | 0.6539 |
| Needed to clear threshold | 1.3029 |
| **Detection limit** | **1.635** |

Deflated Sharpe Ratio: **0.176524** (threshold 0.95)

Probability of Backtest Overfitting: **0.4542** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -0.7963 | -0.6706 | -0.3784 | -0.2086 | -0.0063 | 0.1611 | 0.2872 |

Share of variants with positive Sharpe: 23.3%

## How to read this

This sweep could have detected a true annualised Sharpe of **1.635** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `e64ad6e643c7f7e49dbf504a783130dc02f1bee4f7d39dd36c45e79d122fb5c1`
- Result sha256: `fbdb00902d31ec90a2024f146e946fc9ff5113a93f5741136e8972909775ce70`
- Finalised: 2026-08-01T20:39:30+00:00
- Evidence: returns_matrix
