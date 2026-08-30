"""Probability of Backtest Overfitting via CSCV.

Reference
---------
Bailey, Borwein, Lopez de Prado, Zhu (2017).
"The Probability of Backtest Overfitting." Journal of Computational Finance.

Chop the history into S blocks, take every way of splitting them half
in-sample / half out-of-sample, pick the variant that looked best in-sample,
then see where it ranked out-of-sample. If the in-sample winner lands in the
bottom half out-of-sample more often than not, the selection procedure is
fitting noise.

PBO near 0.5 or above means the whole sweep is a noise machine, no matter how
good the best backtest looked.

IMPLEMENTATION NOTE
-------------------
The naive version re-slices the returns matrix inside all C(16,8) = 12,870
iterations. With thousands of variants that is on the order of a trillion
operations and never finishes. Instead we precompute per-block sums and sums
of squares once, then assemble each split's Sharpe ratios from those — the
inner loop drops from O(T*N) to O(S*N).
"""
from __future__ import annotations

import math
from itertools import combinations

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None


def cscv_pbo(returns, n_splits: int = 16, columns=None) -> dict:
    """returns: array shape (T, N) — per-period returns of N variants.

    `columns` optionally selects a subset of variants. It is applied one
    block at a time so a memory-mapped matrix is never materialised whole.
    """
    if np is None:
        raise RuntimeError("numpy is required for PBO — pip install numpy")

    if returns.ndim != 2:
        raise ValueError("returns must be 2-D: (observations, variants)")
    t_obs = returns.shape[1]
    n_variants = returns.shape[0] if columns is None else len(columns)
    if n_variants < 2:
        raise ValueError("PBO needs at least 2 variants")
    if n_splits % 2 != 0:
        raise ValueError("n_splits must be even")
    if t_obs < n_splits * 2:
        raise ValueError(f"need at least {n_splits * 2} observations")

    blocks = np.array_split(np.arange(t_obs), n_splits)

    # per-block sufficient statistics — computed exactly once
    counts = np.array([len(b) for b in blocks], dtype=np.float64)
    s1 = np.empty((n_splits, n_variants), dtype=np.float64)
    s2 = np.empty((n_splits, n_variants), dtype=np.float64)
    for i, idx in enumerate(blocks):
        sl = slice(idx[0], idx[-1] + 1)
        rows = returns[columns, sl] if columns is not None else returns[:, sl]
        chunk = np.asarray(rows, dtype=np.float64).T
        s1[i] = chunk.sum(axis=0)
        s2[i] = np.einsum("ij,ij->j", chunk, chunk)

    total_count = counts.sum()
    total_s1 = s1.sum(axis=0)
    total_s2 = s2.sum(axis=0)

    def sharpe_from(sum1, sum2, n):
        mean = sum1 / n
        var = (sum2 - sum1 * sum1 / n) / (n - 1)
        sd = np.sqrt(np.maximum(var, 0.0))
        out = np.divide(mean, sd, out=np.zeros_like(mean), where=sd > 0)
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)

    half = n_splits // 2
    n_combos = math.comb(n_splits, half)
    logits = np.empty(n_combos, dtype=np.float64)
    ranks = np.empty(n_combos, dtype=np.float64)

    for k, combo in enumerate(combinations(range(n_splits), half)):
        sel = list(combo)
        n_is = counts[sel].sum()
        is_s1 = s1[sel].sum(axis=0)
        is_s2 = s2[sel].sum(axis=0)

        is_sr = sharpe_from(is_s1, is_s2, n_is)
        oos_sr = sharpe_from(total_s1 - is_s1, total_s2 - is_s2, total_count - n_is)

        best = int(np.argmax(is_sr))
        rank = float(np.count_nonzero(oos_sr <= oos_sr[best])) / (n_variants + 1.0)
        rank = min(max(rank, 1e-9), 1.0 - 1e-9)
        ranks[k] = rank
        logits[k] = math.log(rank / (1.0 - rank))

    return {
        "pbo": float(np.mean(logits < 0.0)),
        "n_splits": n_splits,
        "n_combinations": n_combos,
        "median_oos_rank": float(np.median(ranks)),
        "mean_logit": float(np.mean(logits)),
    }
