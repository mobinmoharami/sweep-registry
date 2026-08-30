# SW-0012 — Donchian channel breakout on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Turtle-style channel breakouts produce no risk-adjusted edge after realistic costs, and no detectable directional tilt across the family. This is the out-of-market replication of SW-0006: identical search space, identical protocol, different asset class. Crypto results to date come from a single market over a single period, so they are not independent evidence of anything general. FX has different participants, different microstructure and far lower costs. If the pattern found in crypto is a property of markets rather than of that one sample, it should appear here too.

## What was searched

- Families: donchian_breakout
- Variants tested: 648
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.0923 |
| Expected best if nothing works | 2.3298 |
| Needed to clear threshold | 2.8981 |
| **Detection limit** | **3.1986** |

Deflated Sharpe Ratio: **0.000262** (threshold 0.95)

Probability of Backtest Overfitting: **0.2426** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -2.3622 | -1.9291 | -1.06 | -0.5586 | -0.0943 | 0.4784 | 1.0923 |

Share of variants with positive Sharpe: 22.7%

## How to read this

This sweep could have detected a true annualised Sharpe of **3.1986** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `141fa8c1656c3f2edc0c3dc44fdfabc2dac549e74bddbbf2a1b79923908f5735`
- Result sha256: `89850f872bda07cdae511b58b9620142e925a2356eebb6b8da6fbf560982024a`
- Finalised: 2026-08-01T16:13:53+00:00
- Evidence: returns_matrix
