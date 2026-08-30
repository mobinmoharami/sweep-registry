# SW-0026 — Break of structure on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

A decisive break of structure is claimed to signal a directional regime change. Stated mechanically: A close beyond the prior lookback-bar extreme by at least entry_threshold ATR(14). This is the only market-structure concept with a fixed definition; anything requiring a chosen swing point or higher-timeframe bias is deliberately excluded as untestable. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: break_of_structure
- Variants tested: 810
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.8 |
| Expected best if nothing works | 2.4913 |
| Needed to clear threshold | 3.4111 |
| **Detection limit** | **3.9372** |

Deflated Sharpe Ratio: **8e-06** (threshold 0.95)

Probability of Backtest Overfitting: **0.2199** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -4.4731 | -2.0065 | -0.9539 | -0.4122 | -0.0139 | 0.4534 | 0.8 |

Share of variants with positive Sharpe: 22.4%

## How to read this

This sweep could have detected a true annualised Sharpe of **3.9372** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `defa3ca09a9a0bb396c3622b734b90a88fdcabe0158e1db334a653cd44078ec5`
- Result sha256: `c4767ea2655249d70d482df9cef966f8f7ee5a990898173271495faf1c41399d`
- Finalised: 2026-08-01T16:49:53+00:00
- Evidence: returns_matrix
