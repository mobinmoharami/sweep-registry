# sweep-registry

A registry of pre-registered strategy sweeps and their results — including,
especially, the ones that found nothing.

**[Browse the results →](https://mobinmoharami.github.io/sweep-registry/)**

---

## What was found

35 hypotheses were pre-registered, hashed, and anchored to the Bitcoin
blockchain **before** the corresponding data was loaded. 18,765 parameter
variants across 17 strategy families were then enumerated and run.

| | |
|---|---|
| Records pre-registered and timestamped | 35 |
| Scored | 29 |
| Voided (reasons below) | 5 |
| Sealed, window not yet open | 1 |
| Variants enumerated | 18,765 |
| Variants that produced at least one trade | 17,946 |
| Sweeps that cleared DSR ≥ 0.95 | **0** |
| Highest Deflated Sharpe Ratio observed | 0.823 |
| Sweeps where the best variant beat chance expectation | 2 of 29 |
| Median minimum detectable Sharpe | 3.49 |

In 27 of 29 scored sweeps, the best variant found performed *worse* than the
maximum expected from an equal number of random strategies. That is a stronger
statement than failing to reach significance. Treating the sweeps as one
sample, a two-sided sign test gives p = 1.6 × 10⁻⁶ — against the strategies,
not for them.

The two exceptions were cross-sectional momentum (DSR 0.809) and its
volatility-scaled variant (0.823) — both short of the 0.95 bar, both
pre-registered for a holdout test that has not been run. The stronger of the
two carries a Probability of Backtest Overfitting of 0.53, meaning the
best-ranked variant in a training split is close to a coin flip out of sample.

**This does not mean technical trading does not work.** The median minimum
detectable Sharpe was 3.49, which is high. A real strategy with a Sharpe of
0.8 would not have been detected here. The correct reading is: *within this
region, above this detection limit, nothing was found.* Smaller effects are
untested, not refuted.

## Three further results

**Most of these families lose money before costs, not because of them.** Gross
and net Sharpe were both recorded, so the cost assumption can be varied
without re-running anything. For 16 of the 26 sweeps with a cost
decomposition, the median variant is unprofitable at *zero* cost. Only two —
Donchian breakout and moving-average crossover on crypto — have a breakeven
cost above the 6 bps charged.

**Every power analysis in this registry understated the detection limit.**
Each pre-registration assumed a kurtosis of 8.0, a reasonable figure for
hourly returns on a liquid asset. The realised kurtosis of the *strategy*
return series exceeded it in all 29 sweeps, by a median factor of 354. The
cause is structural: a strategy return series is the asset return multiplied
by a position that is frequently zero, which concentrates mass at zero and
leaves the tails intact.

**That has a consequence for the metric.** Across these 29 sweeps the Deflated
Sharpe Ratio correlates more strongly with measured kurtosis (ρ = −0.79) than
with the performance of the best variant (ρ = +0.47). High kurtosis inflates
the chance threshold, and an inflated threshold drives DSR toward zero
regardless of what was found. A DSR reported without its accompanying kurtosis
is not interpretable.

## Paper

A write-up is in [`paper/`](paper/), along with the script that regenerates
every number, table and figure in it directly from this repository:

```bash
python3 paper/analysis.py
```

Nothing in the paper is hard-coded. If a sweep is added, voided or re-scored,
re-running that script updates the inputs and any discrepancy with the
published text becomes visible immediately.

## Corrections

Records are never deleted. Where a run failed or a decision was reversed, the
record stays and the reason is attached.

**Three voided for a failed run.** SW-0029, SW-0030 and SW-0031 were
OOM-killed partway through `run_xs_sweep.py`. `finalize.py` then scored the
resulting all-zero returns matrix, which produces DSR exactly 0.5 and prints
NO EDGE FOUND — output indistinguishable from a genuine null result, and not
one. A guard now refuses to score a matrix where every variant has Sharpe
exactly zero. The three hypotheses were re-run correctly as SW-0032, SW-0033
and SW-0034.

**Two voided as declined.** SW-0003 tested short-horizon continuation; its
discovery sample refuted the hypothesis (DSR 0.050, best variant below chance
expectation), so SW-0004, the holdout reserved for it, was never run. Running
a confirmatory test on a hypothesis the discovery sample has already refuted
adds no information and consumes a single-use window.

**Seven sweeps scored fewer variants than they enumerated.** 819 of the 18,765
enumerated variants produced no trade at all; the Sharpe of an identically
zero series is undefined and those columns were excluded at scoring time. The
exclusion biases DSR *upward*, since the multiple-testing penalty scales with
trial count. `finalize.py` flags every such sweep, and the reason is recorded
in each affected `annotations.json`. The largest DSR among the seven is 0.002.

## Verification

Each record's `preregistration.sha256.ots` is an OpenTimestamps proof
anchoring that hash in a Bitcoin transaction. To check that a
pre-registration predates its result:

```bash
cd sweeps/SW-0032
sha256sum -c preregistration.sha256
ots verify preregistration.sha256.ots
```

Records are additionally linked in a hash chain, so removing one changes every
subsequent link including the published head. Timestamping proves a document
predates its result; the chain is what makes quiet deletion visible.

## Layout

```
sweeps/SW-XXXX/
  preregistration.json         the frozen plan: grid, data, costs, threshold
  preregistration.frozen.json  canonical form that was hashed
  preregistration.sha256       its hash
  preregistration.sha256.ots   Bitcoin timestamp proof
  returns.npy                  variant × observation matrix, float32
  active_variants.json         which columns were scored
  variant_names.txt            parameter tuple per column
  result.json                  scoring output
  diagnostics.json             gross vs net, turnover, breakeven, null calibration
  annotations.json             corrections, void reasons, integrity notes
  RECORD.md                    human-readable summary
paper/                         write-up and the script that regenerates it
```

## Reproducing a sweep

Data come from public Binance archives; no API key or account is required.

```bash
pip install -r requirements.txt
./fetch_universe.sh                        # or ./fetch_fx.sh
python run_sweep.py sweeps/SW-0008
python finalize.py sweeps/SW-0008
python diagnose.py sweeps/SW-0008 --null 10
sha256sum sweeps/SW-0008/returns.npy       # compare to RETURNS_CHECKSUMS.json
```

## Registering a new sweep

```bash
$EDITOR sweeps/SW-00XX/preregistration.json
python register.py sweeps/SW-00XX    # computes detection limit, hashes, locks
ots stamp sweeps/SW-00XX/preregistration.sha256
python run_sweep.py sweeps/SW-00XX
python finalize.py sweeps/SW-00XX
python diagnose.py sweeps/SW-00XX --null 10
```

The order matters and is the only thing that makes any of this worth reading:
the hash is stamped before the data is loaded.

## License

See [LICENSE](LICENSE).
