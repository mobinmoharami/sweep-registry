# SW-0013 — ATR volatility breakout on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Volatility breakout rules produce no risk-adjusted edge after realistic costs, and no detectable directional tilt across the family. This is the out-of-market replication of SW-0007: identical search space, identical protocol, different asset class. Crypto results to date come from a single market over a single period, so they are not independent evidence of anything general. FX has different participants, different microstructure and far lower costs. If the pattern found in crypto is a property of markets rather than of that one sample, it should appear here too.

## What was searched

- Families: atr_breakout
- Variants tested: 810
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 1.0954 |
| Expected best if nothing works | 2.8224 |
| Needed to clear threshold | 3.5735 |
| **Detection limit** | **3.9763** |

Deflated Sharpe Ratio: **8e-06** (threshold 0.95)

Probability of Backtest Overfitting: **0.1284** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -4.8767 | -2.3315 | -1.2152 | -0.562 | -0.0442 | 0.502 | 1.0954 |

Share of variants with positive Sharpe: 22.5%

## How to read this

This sweep could have detected a true annualised Sharpe of **3.9763** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `b7bb6e54e883e3ca65fa1019bad35623eaf2c3049b908b7564768ae4f1622900`
- Result sha256: `6bd9f1a2238d8363b20058417aa4ae6f57cb5af7101092a0a81be968a7938928`
- Finalised: 2026-08-01T16:14:44+00:00
- Evidence: returns_matrix
