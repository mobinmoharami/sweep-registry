# External results

Negative results measured outside the registry's own engine.

Everything in `sweeps/` was produced by `run_sweep.py`, scored by
`finalize.py` with a deflated Sharpe ratio and a probability of backtest
overfitting, and hashed to Bitcoin before its data was loaded. That
uniformity is what makes those records comparable to each other.

The files here have none of that. They were run with purpose-written
code, scored on mean net return, and written up after the fact. They are
published because the measurements are clean and the findings are useful,
and they are kept separate because calling them sweeps would break the
one guarantee the registry offers.

| file | question | verdict |
|---|---|---|
| EXT-0038 | Does shorting newly listed perpetuals pay, once stops fire on the path rather than at the endpoint? | No. Matched long and short means sum to exactly twice the assumed spread. |
| EXT-0039 | Can the funding payment be captured by entering just before settlement and exiting just after? | No. Price moves against the position by roughly three times the rate collected, worsening with window length. |
| EXT-0040 | Does the spot-perpetual basis revert profitably? | Mechanism confirmed, edge absent. Gross +0.039% at a 97% hit rate against a 0.08% cost of four fills. |

EXT-0040 is the one worth reading twice: it separates "nothing happens"
from "something happens and costs more than it pays", which are different
findings and only the second changes with a better fee tier.
