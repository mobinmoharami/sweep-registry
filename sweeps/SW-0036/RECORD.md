# SW-0036 — Volume-confirmed price signals on BTC and ETH spot, hourly

**Verdict: NO EDGE FOUND**

Every one of the 21 families in this registry reads price alone. The claim these three encode is the one most widely taught alongside them: that a price move confirmed by volume behaves differently from one that is not. It has never been tested here.

The grid is built so the test answers itself. volume_breakout at threshold 0 disables the volume filter entirely and reduces to a plain Donchian breakout - verified byte-identical before freezing - so the low end of the threshold axis is an exact control for the high end. If volume confirmation carries information, variants must separate along that axis. If they do not separate, the confirmation adds nothing.

volume_climax fades the same volume spike that volume_breakout follows. The two are mirrors on one signal: if either direction is real the other should fail, and if both fail the spike carries no directional information at all, which is a stronger negative than either alone.

obv_trend has the same structure as ma_cross with cumulative signed volume substituted for price, making the two directly comparable.

Prediction, stated before any result was computed: no family clears the threshold, and volume_breakout does not separate from its threshold-0 control.

## What was searched

- Families: volume_breakout, obv_trend, volume_climax
- Variants tested: 1,080
- Symbols: BTCUSDT, ETHUSDT
- Period: 2019-01-01 to 2025-06-30 (1h, 56,870 observations)
- Costs: 4.0 bps, slippage 6.0 bps
- Protocol: Fixed rules, no in-sample parameter fitting. Every variant evaluated over the full period; in-sample/out-of-sample splitting is done by CSCV at scoring time.
- Holdout: 2025-07-01 onward is not loaded by this sweep and is reserved for a confirmatory sweep if anything clears.

## Result

| | annualised Sharpe |
|---|---|
| Best variant found | 0.8638 |
| Expected best if nothing works | 7.9205 |
| Needed to clear threshold | 8.5888 |
| **Detection limit** | **8.9338** |

Deflated Sharpe Ratio: **0.0** (threshold 0.95)

Probability of Backtest Overfitting: **0.2205** (12,870 CSCV splits)

## Distribution across all variants

Publishing only the best result is how noise gets sold as skill. The whole distribution:

| min | p05 | p25 | median | p75 | p95 | max |
|---|---|---|---|---|---|---|
| -13.6726 | -5.078 | -1.1717 | -0.4103 | -0.0621 | 0.394 | 0.8638 |

Share of variants with positive Sharpe: 23.3%

## How to read this

This sweep could have detected a true annualised Sharpe of **8.9338** or larger with 80% power. It says nothing about smaller edges, and nothing about strategy families outside the search space above.

## Integrity

- Pre-registration sha256: `73c4c07e773b2d9560fa05c3f9daddff50729c8dfecac0d344de3e40aec974c2`
- Result sha256: `b80ea62cb65ab3cffa8403e351bbb16604abc2e103275957e50d0b0b52011ed9`
- Finalised: 2026-08-31T00:34:47+00:00
- Evidence: returns_matrix
