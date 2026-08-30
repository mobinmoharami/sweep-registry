# SW-0011 — Moving average crossover on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Moving average crossovers — the single most widely sold technical rule — produce no risk-adjusted edge after realistic costs, and no detectable directional tilt across the family, once selection over the full parameter space is accounted for. This is the out-of-market replication of SW-0005: identical search space, identical protocol, different asset class. Crypto results to date come from a single market over a single period, so they are not independent evidence of anything general. FX has different participants, different microstructure and far lower costs. If the pattern found in crypto is a property of markets rather than of that one sample, it should appear here too.

## What was searched

- Families: ma_cross
- Variants tested: 945
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.8098 |
| Expected best if nothing works | 1.6881 |
| Needed to clear threshold | 2.3771 |
| **Detection limit** | **2.7293** |

Deflated Sharpe Ratio: **0.018598** (threshold 0.95)

Probability of Backtest Overfitting: **0.3544** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -2.7403 | -1.4943 | -0.7628 | -0.5412 | -0.275 | 0.2248 | 0.8098 |

Share of variants with positive Sharpe: 13.0%

## How to read this

This sweep could have detected a true annualised Sharpe of **2.7293** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `5375656cb4974be0840854de073e1d0361cab2bf2fa26722a54bd61595717062`
- Result sha256: `b57041aa3dcff1682df918cb1a6209a6eb71b7aa7bb094fceded786cf73ae185`
- Finalised: 2026-08-01T16:13:22+00:00
- Evidence: returns_matrix
