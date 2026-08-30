# SW-0015 — Volatility-filtered momentum on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Restricting momentum to low-volatility regimes — the standard 'it works if you filter for the right regime' claim — produces no risk-adjusted edge after realistic costs. This is the out-of-market replication of SW-0009: identical search space, identical protocol, different asset class. Crypto results to date come from a single market over a single period, so they are not independent evidence of anything general. FX has different participants, different microstructure and far lower costs. If the pattern found in crypto is a property of markets rather than of that one sample, it should appear here too.

## What was searched

- Families: vol_regime_momentum
- Variants tested: 540
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.8805 |
| Expected best if nothing works | 3.4142 |
| Needed to clear threshold | 4.1135 |
| **Detection limit** | **4.4951** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.1218** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -5.1668 | -3.1902 | -1.7324 | -1.0236 | -0.3619 | 0.3817 | 0.8805 |

Share of variants with positive Sharpe: 15.4%

## How to read this

This sweep could have detected a true annualised Sharpe of **4.4951** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `a2444273e63e54f93f18ffa01fe8933cb7308588fb372168627d443e576e23bd`
- Result sha256: `45b1b7139a151b8d5444589733a5ea2708d0651cf915b015b564f9690f6e602d`
- Finalised: 2026-08-01T16:15:35+00:00
- Evidence: returns_matrix
