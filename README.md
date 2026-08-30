# sweep-registry

A registry of pre-registered strategy sweeps and their results — including,
especially, the ones that found nothing.

**[Browse the results →](https://mobinmoharami.github.io/sweep-registry/)**

---

## What was found

34 hypotheses were pre-registered, hashed, and anchored to the Bitcoin
blockchain **before** the corresponding data was loaded. 21,285 parameter
variants across 21 strategy families were then enumerated and run.

| | |
|---|---|
| Sweeps pre-registered and timestamped | 34 |
| Variants enumerated | 21,285 |
| Sweeps that cleared DSR ≥ 0.95 | **0** |
| Highest Deflated Sharpe Ratio observed | 0.823 |
| Sweeps where the best variant beat chance expectation | 2 of 28 |
| Median minimum detectable Sharpe | 3.49 |

In 26 of 28 scored sweeps, the best variant found performed *worse* than the
maximum expected from an equal number of random strategies. That is a stronger
statement than failing to reach significance.

The two exceptions were cross-sectional momentum (DSR 0.809) and its
volatility-scaled variant (0.823) — both short of the 0.95 bar, both
pre-registered for a holdout test that has not been run.

**This does not mean technical trading does not work.** The median minimum
detectable Sharpe was 3.49, which is high. A real strategy with a Sharpe of
0.8 would not have been detected here. The correct reading is: *within this
region, above this detection limit, nothing was found.* Smaller effects are
untested, not refuted.

## Why this exists

Everything we "know" about markets has passed through a filter: only what
worked got published. A thousand people test a strategy, 999 fail silently,
one succeeds and gets a following — even though statistically that one is
exactly what luck predicts.

Backtests are cheap and the space of testable rules is unbounded, so the
filter is severe. The statistical corrections for it already exist —
[Bailey & López de Prado's Deflated Sharpe Ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551),
[Harvey, Liu & Zhu on multiple testing](https://academic.oup.com/rfs/article/29/1/5/1843824)
— but they get applied to a sample that has already been filtered.

This fixes one half of that. The search space, the protocol and the threshold
are written down and hashed **before** the test runs. Then the full result is
published — the whole distribution, not just the best variant.

## The unit of publication

Not a strategy. A **region of strategy space**.

"RSI 14 didn't work on BTC" is worthless — it describes one point in a
continuum, and you cannot tell whether the neighbouring parameter would have
worked.

"The entire mean-reversion family, 1,620 enumerated variants, across three
symbols over six years, produced nothing above a detection limit of 2.4
annualised Sharpe" is a claim someone can build on.

## Verifying a pre-registration

Every sweep carries an OpenTimestamps proof. To check that a hypothesis
predates its result:

```bash
pip install opentimestamps-client
cd sweeps/SW-0032
ots verify preregistration.sha256.ots
```

This resolves to a Bitcoin block height and timestamp. The document itself
never left the author's control — only its hash was submitted.

To confirm the hash matches the frozen document:

```bash
python3 -c "
from srlab.canonical import canonical_sha256
import json
print(canonical_sha256(json.load(open('preregistration.frozen.json'))))
"
cat preregistration.sha256
```

## Reproducing a sweep

Raw return matrices (4.3 GB) and price data (1.1 GB) are not in the
repository. Both are regenerable, and the SHA-256 of every matrix is
published in [`RETURNS_CHECKSUMS.json`](RETURNS_CHECKSUMS.json) so a
reproduction can be checked byte-for-byte.

```bash
pip install numpy requests opentimestamps-client

# 1. get the bars — no API key, no account
python data/fetch_binance_bulk.py BTCUSDT 1h 2017-08 2026-07

# 2. re-run a sweep from its frozen pre-registration
python run_sweep.py sweeps/SW-0008

# 3. score it
python finalize.py sweeps/SW-0008

# 4. check the matrix against the published checksum
sha256sum sweeps/SW-0008/returns.npy
```

## Running your own

```bash
python new_sweep.py SW-0036          # copies a template without its seal
$EDITOR sweeps/SW-0036/preregistration.json
python register.py sweeps/SW-0036    # computes detection limit, hashes, locks
ots stamp sweeps/SW-0036/preregistration.sha256
python run_sweep.py sweeps/SW-0036
python finalize.py sweeps/SW-0036
python diagnose.py sweeps/SW-0036 --null 10
```

Step 6 is what turns "nothing worked" into a finding. "No edge" has two very
different causes that look identical in net returns: there is no signal at
all, or there is a signal and costs ate it. `diagnose.py` decomposes every
variant into gross return, cost drag, turnover and market beta, and tells you
which one you are looking at.

## Corrections

Three sweeps (SW-0029, SW-0030, SW-0031) produced returns matrices that were
identically zero. The scorer accepted the empty matrix as a valid null result
and reported "best Sharpe 0.0, zero variants positive" as a finding. It was
not a finding; it was a failed run that looked like one.

All three have the same SHA-256, which is visible in `RETURNS_CHECKSUMS.json`
and is what makes the failure verifiable rather than merely asserted. The
hypotheses were re-run correctly as SW-0032, SW-0033 and SW-0034; the original
records are marked void with the superseding record named.

A fourth (SW-0004) is voided as *declined*, not failed. It is the holdout for
SW-0003, whose discovery sample produced a best Sharpe of 1.489 against a
chance expectation of 2.068 — a confirmatory test on an already-refuted
hypothesis adds nothing, and spending the sealed window would only consume it.

A registry that hides its own failed runs reproduces the problem it exists to
address.

## Survivorship

Cross-sectional universes are rebuilt monthly from the *previous* month's
quote volume, so a symbol is held only in months when it would actually have
been selected, and symbols that later delisted are retained for the period
they traded.

[Ammann, Burdorf, Liebi & Stöckl (SSRN 4287573)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4287573)
measured an annualised survivorship bias of 62.19% for equal-weighted crypto
portfolios built from a present-day universe. Without point-in-time
construction, almost any result in this asset class is uninterpretable.

## Contributing

Negative results are welcome — that is the point. Open an issue with the
family you want to enumerate and the parameter grid, and it can be added as a
numbered sweep.

The one rule: the pre-registration is timestamped before the data is loaded.
A sweep whose grid was adjusted after seeing a result is not a sweep.

## Licence

MIT.

