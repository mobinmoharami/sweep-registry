# SW-0029 — Cross-sectional momentum across a point-in-time top-20 crypto universe, hourly

**Verdict: NO EDGE FOUND**

Cross-sectional momentum is the one crypto strategy family with substantial published academic support. If nothing in this registry works, this is where a null result is most surprising and most informative. Stated mechanically: Rank the investable universe by trailing return over `lookback` bars; go long the top `entry_threshold` fraction, short the bottom, equal-weighted and dollar-neutral, rebalanced every `holding_cap_bars` bars. Two things make this sweep different from every earlier one in this registry. First, a cross-sectional dollar-neutral portfolio cannot inherit a market trend, so the Bitcoin uptrend that contaminated the time-series crypto results cannot produce an effect here. Second, the universe is rebuilt monthly from the previous month's volume, so coins that later died are held while they lived. Ammann, Burdorf, Liebi and Stockl (SSRN 4287573) measured an annualised survivorship bias of 62.19% for equal-weighted crypto portfolios; taking today's top 20 and backtesting them would make almost any result meaningless.

## What was searched

- Families: xs_momentum
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

- Pre-registration sha256: `be45f17776a9a2f9fb87329432f05ff8e0aa167788679a79a0d3267bb92ba258`
- Result sha256: `1f5f8e816ee598c00128fea723b17e7a5de87e74797b7ac425df824ff4fbeb24`
- Finalised: 2026-08-01T20:26:23+00:00
- Evidence: returns_matrix

<!-- annotations -->

## Status: VOID

run_xs_sweep.py was OOM-killed partway through; finalize.py then scored an all-zero returns matrix, which produces DSR exactly 0.5 and prints NO EDGE FOUND. That output is indistinguishable from a genuine null result and is not one. A guard now refuses to score a matrix where every variant has Sharpe exactly zero.

## Notes

- The failure mode mattered more than the sweep: a crashed run that looks like a finding is the worst thing this registry could publish.

## Related records

- Superseded by SW-0032

---

*Annotations added 2026-08-01T22:45:25+00:00. The frozen pre-registration, its hash and result.json are unmodified.*
