# SW-0014 — Time-series momentum on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Time-series momentum at intraday-to-weekly horizons produces no risk-adjusted edge after realistic costs. Note this is the horizon at which momentum is LEAST documented; published crypto momentum results are mostly weekly to monthly and cross-sectional, so a null here does not contradict them. This is the out-of-market replication of SW-0008: identical search space, identical protocol, different asset class. Crypto results to date come from a single market over a single period, so they are not independent evidence of anything general. FX has different participants, different microstructure and far lower costs. If the pattern found in crypto is a property of markets rather than of that one sample, it should appear here too.

## What was searched

- Families: momentum_roc
- Variants tested: 792
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.1017 |
| Expected best if nothing works | 3.7739 |
| Needed to clear threshold | 4.4985 |
| **Detection limit** | **4.8966** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.2611** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -6.7794 | -2.9253 | -0.8046 | -0.3589 | 0.0492 | 0.4649 | 1.1017 |

Share of variants with positive Sharpe: 27.9%

## How to read this

This sweep could have detected a true annualised Sharpe of **4.8966** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `85a3aac279461f8544f76a78c2fd060d16aef75745efc3ba6126ccab1e25feb6`
- Result sha256: `45c1c0046c4d324949bbc6542d6f8ef540cfbc6c89e93015cf7a333cf91b0d83`
- Finalised: 2026-08-01T16:15:02+00:00
- Evidence: returns_matrix
- NOTE: Trial count differs from pre-registration: declared 810, supplied 792. Explain this in the record.
