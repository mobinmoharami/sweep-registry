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

<!-- annotations -->

## Status: VOID

Weight-allocation bug in sweep/cross_sectional.py: assets outside the point-in-time universe scored -inf and therefore sorted first, so the entire short leg of every long_short variant (45 of 90) was allocated to non-investable assets whose returns are zeroed. Verified by replay: the stored returns matrix reproduces exactly under the buggy allocator (max abs diff 2.6e-08) and diverges materially under the fixed one (correlation 0.54-0.69; one variant moves from 0.187 to 0.468 annualised Sharpe). The mean_touch (long-only) branch was unaffected, but the corrupted variants are counted in n_trials, in the expected-maximum-Sharpe null and in the PBO combinatorics, so the primary metric is not valid. Pre-registration and its Bitcoin timestamp remain valid; only the execution failed. Fixed and covered by tests/test_cross_sectional_weights.py; re-registered under new IDs.

## Exploratory — NOT pre-registered

Everything in this section was noticed by looking at the finished result. It is a hypothesis, not a finding, and it carries no multiple-testing correction of its own.

Post hoc observation, carried forward to the replacement sweeps: the mean_touch exit rule is long-only with gross exposure 2.0, not dollar-neutral, so it is not market-neutral and does inherit the crypto trend. In all three sweeps the highest-Sharpe variant came from this branch. In SW-0034 that variant compounds to 0.22x of initial capital with a 100% maximum drawdown despite an annualised Sharpe of 0.989, losing between 37% and 53% in each of four hours during the LUNA/UST collapse (2022-05-11 to 2022-05-13; verified against BTCUSDT bar timestamps, not a data error). Sharpe and the deflated Sharpe ratio are computed from arithmetic moments and do not see the capital path.

---

*Annotations added 2026-10-10T18:05:35+00:00. The frozen pre-registration, its hash and result.json are unmodified.*
