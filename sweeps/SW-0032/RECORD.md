# SW-0032 — Cross-sectional momentum across a point-in-time top-20 crypto universe, hourly

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
| Best variant found | 0.9827 |
| Expected best if nothing works | 0.6367 |
| Needed to clear threshold | 1.2896 |
| **Detection limit** | **1.6241** |

Deflated Sharpe Ratio: **0.808562** (threshold 0.95)

Probability of Backtest Overfitting: **0.4786** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -0.178 | 0.0125 | 0.2806 | 0.5091 | 0.6807 | 0.8171 | 0.9827 |

Share of variants with positive Sharpe: 95.6%

## How to read this

This sweep could have detected a true annualised Sharpe of **1.6241** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `d406f3b72247277c88f9f6f954d9460f045a3ecddc372eff4e6db25a07ffb2d5`
- Result sha256: `c15e222bd32a54eac67581666c75d3f14ad6b0164343666ac0ac2d8f504050d9`
- Finalised: 2026-08-01T20:38:37+00:00
- Evidence: returns_matrix

<!-- annotations -->

## What was pre-registered

Pre-registered test: does the best of 90 cross-sectional momentum variants clear DSR 0.95? Verdict: NO. DSR 0.809 — the closest any sweep in this registry has come, and still short.

## Exploratory — NOT pre-registered

Everything in this section was noticed by looking at the finished result. It is a hypothesis, not a finding, and it carries no multiple-testing correction of its own.

96% of variants were positive with a median annualised Sharpe of 0.51 and a best of 0.98 against an expected-under-null of 0.64. The family behaves as one thing rather than as a spread of better and worse rules.

PBO is 0.479, near the 0.5 coin-flip line. Choosing among these 90 variants carries almost no information out of sample. That is consistent with a uniform family-wide effect and inconsistent with some variants genuinely being better.

The effect comes from the stable end of the universe, not the volatile end. Splitting by symbol lifetime: 81 long-lived symbols (>40,000 bars) give a net Sharpe of 0.72, while 55 short-lived symbols (<20,000 bars) give 0.04. A spurious altcoin-volatility artefact would show the opposite, and the effect is stronger where liquidity is better.

## Notes

- This is the only family in 33 records to show a coherent signal, and it is also the only one with substantial published academic support in crypto. The test cannot confirm it: the detection limit is around 1.6 annualised Sharpe and the observed effect is roughly 0.7.

- SW-0035, embargoed until 2029-06-30, is the holdout test — and its pre-registration states up front that it is underpowered. Confirming a true Sharpe of 0.72 at z=2 with 80% power needs roughly 136,000 hourly bars, about 15.6 years. Four years gives about 29%.

---

*Annotations added 2026-08-01T22:45:25+00:00. The frozen pre-registration, its hash and result.json are unmodified.*
