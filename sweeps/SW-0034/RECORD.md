# SW-0034 — Volatility-scaled cross-sectional momentum across a point-in-time top-20 crypto universe, hourly

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
| Best variant found | 0.9892 |
| Expected best if nothing works | 0.6219 |
| Needed to clear threshold | 1.2757 |
| **Detection limit** | **1.6109** |

Deflated Sharpe Ratio: **0.822663** (threshold 0.95)

Probability of Backtest Overfitting: **0.5301** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -0.1632 | 0.0834 | 0.3655 | 0.5531 | 0.6813 | 0.8624 | 0.9892 |

Share of variants with positive Sharpe: 95.6%

## How to read this

This sweep could have detected a true annualised Sharpe of **1.6109** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `6045b45304dbfe2d62bf574d8386a0f4909822b07f6833264036c400881ddc05`
- Result sha256: `625e6807fee3c76e7accc031277d6caf8e54f949cb1fc7e611acd0babcee7684`
- Finalised: 2026-08-01T20:40:58+00:00
- Evidence: returns_matrix

<!-- annotations -->

## What was pre-registered

Pre-registered test: DSR 0.823 against a 0.95 threshold. Verdict: NO.

## Exploratory — NOT pre-registered

Everything in this section was noticed by looking at the finished result. It is a hypothesis, not a finding, and it carries no multiple-testing correction of its own.

Marginally stronger than plain cross-sectional momentum (SW-0032, DSR 0.809), consistent with the standard argument that scaling by volatility stops the most volatile assets dominating the ranking. The difference is far too small to call a result.

## Notes

- A numpy 'Degrees of freedom <= 0' warning appears during this sweep. It comes from all-NaN columns — symbols not yet listed — passing through nanstd. Those columns return NaN and are dropped by the ranking, so the result is unaffected.

---

*Annotations added 2026-08-01T22:45:25+00:00. The frozen pre-registration, its hash and result.json are unmodified.*
