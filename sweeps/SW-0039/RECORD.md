# SW-0039 — Cross-sectional momentum across a point-in-time top-20 crypto universe, hourly

**Verdict: NO EDGE FOUND**

Cross-sectional momentum is the one crypto strategy family with substantial published academic support. If nothing in this registry works, this is where a null result is most surprising and most informative. Stated mechanically: Rank the investable universe by trailing return over `lookback` bars; go long the top `entry_threshold` fraction, short the bottom, equal-weighted and dollar-neutral, rebalanced every `holding_cap_bars` bars. Two things make this sweep different from every earlier one in this registry. First, a cross-sectional dollar-neutral portfolio cannot inherit a market trend, so the Bitcoin uptrend that contaminated the time-series crypto results cannot produce an effect here. Second, the universe is rebuilt monthly from the previous month's volume, so coins that later died are held while they lived. Ammann, Burdorf, Liebi and Stockl (SSRN 4287573) measured an annualised survivorship bias of 62.19% for equal-weighted crypto portfolios; taking today's top 20 and backtesting them would make almost any result meaningless.

## What was searched

- Families: xs_momentum
- Variants tested: 45
- Symbols: point-in-time top 20 by prior-month quote volume
- Period: 2019-02-01 to 2025-06-30 (1h, 56,126 observations)
- Costs: 4.0 bps, slippage 6.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Equal-weighted and dollar-neutral: the long and short legs are the same size and are drawn only from assets investable in that month. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.9698 |
| Expected best if nothing works | 0.859 |
| Needed to clear threshold | 1.5736 |
| **Detection limit** | **1.9488** |

Deflated Sharpe Ratio: **0.604679** (threshold 0.95)

Probability of Backtest Overfitting: **0.3386** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -0.6179 | -0.2251 | 0.0869 | 0.4033 | 0.7155 | 0.8792 | 0.9698 |

Share of variants with positive Sharpe: 82.2%

## How to read this

This sweep could have detected a true annualised Sharpe of **1.9488** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `ae0a502318589e6605f6179ce316ce99ad9315fce590889a8aafe7983497257b`
- Result sha256: `ccb96cc52b71b10474a16bb024e91ef00bbc1107cdbf75585ba40ca047fb83e5`
- Finalised: 2026-10-10T18:19:12+00:00
- Evidence: returns_matrix

<!-- annotations -->

## Exploratory — NOT pre-registered

Everything in this section was noticed by looking at the finished result. It is a hypothesis, not a finding, and it carries no multiple-testing correction of its own.

Post hoc, measured after both sweeps were run: SW-0040 (cross-sectional reversal) is not an independent test of this one. xs_reversal is implemented as the negation of the momentum score, so with a symmetric long/short fraction the resulting portfolio is the exact inverse. Per-variant correlation between the two returns matrices is -0.997 to -0.999; gross Sharpe, residual Sharpe, turnover and breakeven are mirror images to four decimal places. The two records should be read as one piece of evidence with a sign, not two. Only net Sharpe differs non-trivially, because transaction costs subtract from both legs rather than reflecting.

---

*Annotations added 2026-10-10T18:51:20+00:00. The frozen pre-registration, its hash and result.json are unmodified.*
