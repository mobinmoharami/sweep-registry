# SW-0028 — Inside bar breakout on major FX pairs, hourly

**Verdict: NO EDGE FOUND**

Range contraction is claimed to precede expansion in a predictable direction. Stated mechanically: One or more consecutive bars contained within the prior bar's range, followed by a close beyond that range by entry_threshold ATR(14). lookback//10 sets how many consecutive inside bars are required. This sweep tests whether that produces a risk-adjusted edge after realistic costs, once selection across the full parameter space is accounted for. The definition is fixed and hashed before the test runs, so an objection that it was implemented wrong must be raised against this text in advance.

## What was searched

- Families: inside_bar_breakout
- Variants tested: 405
- Symbols: EURUSD, GBPUSD, USDJPY
- Period: 2017-09-01 to 2025-06-30 (1h, 48,749 observations)
- Costs: 1.0 bps, slippage 0.5 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward — not loaded or inspected until the verdict is written

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.7791 |
| Expected best if nothing works | 2.3964 |
| Needed to clear threshold | 3.1182 |
| **Detection limit** | **3.4918** |

Deflated Sharpe Ratio: **6.5e-05** (threshold 0.95)

Probability of Backtest Overfitting: **0.3476** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -5.1734 | -2.1065 | -0.7959 | -0.4217 | -0.0258 | 0.4366 | 0.7791 |

Share of variants with positive Sharpe: 23.0%

## How to read this

This sweep could have detected a true annualised Sharpe of **3.4918** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `88c1722b652f584f2572bca6db818868a7cc15df1f651eacce81aca808aab3ab`
- Result sha256: `b279edfe3fac2d22646ed2a960cf06be7d6a2f90fb8c77af49bec49153e1ff68`
- Finalised: 2026-08-01T16:50:56+00:00
- Evidence: returns_matrix
- NOTE: Trial count differs from pre-registration: declared 810, supplied 405. Explain this in the record.
