# SW-0003 — Short-horizon continuation on BTC and ETH spot, hourly

**Verdict: EFFECT DETECTED**

Following on from the exploratory finding in SW-0002, that short-horizon mean reversion carries systematically negative market-neutral gross Sharpe: the mirrored continuation rules, using identical indicators, lookbacks, thresholds and exit rules, will show a POSITIVE mean market-neutral gross Sharpe across the search space, distinguishable from shuffled data. This is a confirmatory test of a direction discovered post hoc in SW-0002 and registered before being run.

## What was searched

- Families: zscore_continuation, rsi_continuation, bollinger_breakout
- Variants tested: 1,599
- Symbols: BTCUSDT, ETHUSDT
- Period: 2017-09-01 to 2025-06-30 (1h, 68,490 observations)
- Costs: 4.0 bps, slippage 2.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period. Market exposure removed per variant by regressing gross returns on the underlying bar returns; the residual Sharpe is the quantity of interest.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.4893 |
| Expected best if nothing works | 2.0678 |
| Needed to clear threshold | 2.646 |
| **Detection limit** | **2.9421** |

Deflated Sharpe Ratio: **0.050284** (threshold 2.0)

## Pre-registered test: cross-sectional residual Sharpe

The registered hypothesis concerns the whole population of variants, not the best one. Pooling across variants detects far smaller effects than a maximum ever could — but says nothing about any single rule.

- Observed mean market-neutral gross Sharpe: **0.3358**
- Shuffled null: -0.0077 ± 0.062 over 10 runs
- **z = 5.542** (threshold 2.0), direction positive

Probability of Backtest Overfitting: **0.0319** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -3.1848 | -1.1319 | -0.2985 | -0.0284 | 0.2948 | 0.8118 | 1.4893 |

Share of variants with positive Sharpe: 46.6%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.9421** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `d2f13ee4cdaa0f54423ec3e15bead9886e6ba8af099e4bbe0f89c3223304169e`
- Result sha256: `d4c1bb14b63bd4b63dd36c1aada62e76924dcfe321d7e99c74c6b2d61d3e16c4`
- Finalised: 2026-08-01T00:00:27+00:00
- Evidence: returns_matrix
- NOTE: Trial count differs from pre-registration: declared 1,620, supplied 1,599. Explain this in the record.

<!-- annotations -->

## Status: VOID

Not an independent test. The continuation families were exact position-wise inversions of SW-0002's reversion families, so every statistic returned as the precise arithmetic negative of the original to four decimal places: gross Sharpe -0.2901 became +0.2901, z of -5.542 became +5.542. An exact inversion is an identity, not a replication. Kept rather than deleted: removing a sweep because it turned out uninformative is the selective reporting this registry exists to document.

## Notes

- The one thing it does establish: gross Sharpe is antisymmetric under position inversion, so any symmetric bias — costs, spread, microstructure — contributes zero to it. Combined with the shuffled-null result, that rules out lookahead as the source of the SW-0002 effect.

---

*Annotations added 2026-08-01T22:45:25+00:00. The frozen pre-registration, its hash and result.json are unmodified.*
