"""Cross-sectional strategies: rank assets against each other, not against time.

The time-series engine asks "should I be long or short THIS asset now". This
one asks "which of these twenty assets is best right now" — long the top
fraction, short the bottom, rebalanced periodically, dollar-neutral.

That difference matters more than it sounds. A cross-sectional portfolio is
market-neutral by construction, so it cannot inherit the Bitcoin uptrend that
contaminated the crypto time-series results. It is also the one crypto family
with genuine published evidence behind it.

The universe changes every month, and that is the whole point: a symbol is
held only in months when it was actually in the top N by prior volume, and
symbols that later died are still held while they lived.
"""
from __future__ import annotations

import numpy as np


def _rank_normalise(scores: np.ndarray) -> np.ndarray:
    """Map scores to evenly spaced ranks in [-1, 1], NaNs excluded.

    Ranks rather than raw values: one coin doing 400% in a week would
    otherwise dominate the entire portfolio weight.
    """
    valid = ~np.isnan(scores)
    n = int(valid.sum())
    out = np.zeros_like(scores)
    if n < 2:
        return out
    order = np.argsort(np.argsort(np.where(valid, scores, np.inf)))
    normed = order[valid].astype(float) / (n - 1) * 2.0 - 1.0
    out[valid] = normed
    return out


def momentum_score(prices: np.ndarray, t: int, lookback: int) -> np.ndarray:
    """Trailing return over `lookback` bars, per asset."""
    if t - lookback < 0:
        return np.full(prices.shape[1], np.nan)
    past, now = prices[t - lookback], prices[t]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where((past > 0) & (now > 0), now / past - 1.0, np.nan)


def reversal_score(prices: np.ndarray, t: int, lookback: int) -> np.ndarray:
    return -momentum_score(prices, t, lookback)


def vol_scaled_momentum(prices: np.ndarray, t: int, lookback: int) -> np.ndarray:
    """Trailing return divided by trailing volatility."""
    if t - lookback < 1:
        return np.full(prices.shape[1], np.nan)
    window = prices[t - lookback:t + 1]
    with np.errstate(invalid="ignore", divide="ignore"):
        rets = np.diff(window, axis=0) / window[:-1]
        vol = np.nanstd(rets, axis=0)
        mom = window[-1] / window[0] - 1.0
        return np.where(vol > 0, mom / vol, np.nan)


SCORERS = {
    "xs_momentum": momentum_score,
    "xs_reversal": reversal_score,
    "xs_vol_scaled_momentum": vol_scaled_momentum,
}


class CrossSectionalRunner:
    """Runs cross-sectional variants over a panel of aligned prices.

    prices : (T, N) float array, NaN where an asset is not in the universe
    membership : (T, N) bool array, True where the asset is investable

    MEMORY
    ------
    An earlier version built a full (T, N) weight matrix per variant. At
    56,000 bars x 184 assets that is ~83 MB each, and across a 90-variant
    sweep the process was OOM-killed. This walks the panel once per variant
    and keeps only two weight vectors alive.
    """

    def __init__(self, prices, membership, cost_bps: float):
        self.prices = np.asarray(prices, dtype=np.float64)
        self.membership = np.asarray(membership, dtype=bool)
        self.cost = cost_bps / 10_000.0

        p = self.prices
        ret = np.zeros_like(p)
        with np.errstate(invalid="ignore", divide="ignore"):
            ret[1:] = np.where(p[:-1] > 0, p[1:] / p[:-1] - 1.0, 0.0)
        # An asset entering or leaving the universe is not a price move.
        entering = self.membership & ~np.roll(self.membership, 1, axis=0)
        entering[0] = self.membership[0]
        ret[entering] = 0.0
        self.ret = np.nan_to_num(ret, nan=0.0, posinf=0.0, neginf=0.0)

    def _target_weights(self, t: int, variant: dict, n_assets: int):
        scorer = SCORERS[variant["family"]]
        scores = scorer(self.prices, t, int(variant["lookback"]))
        scores = np.where(self.membership[t], scores, np.nan)
        ranks = _rank_normalise(scores)

        live = ~np.isnan(scores)
        n_live = int(live.sum())
        w = np.zeros(n_assets)
        if n_live < 4:
            return w

        # entry_threshold is the fraction of the universe taken per side:
        # 0.2 means long the top 20%, short the bottom 20%
        frac = float(variant["entry_threshold"])
        k = max(1, int(round(n_live * frac)))
        idx = np.argsort(np.where(live, ranks, -np.inf))
        w[idx[-k:]] = 1.0 / k
        if variant["exit_rule"] == "mean_touch":      # long only
            w *= 2.0                                  # same gross exposure
        else:
            w[idx[:k]] = -1.0 / k
        return w

    def run_detail(self, variant: dict) -> dict:
        t_obs, n_assets = self.prices.shape
        rebalance = int(variant["holding_cap_bars"])

        gross = np.zeros(t_obs)
        turn = np.zeros(t_obs)
        exposure = np.zeros(t_obs)
        tilt = np.zeros(t_obs)

        target = np.zeros(n_assets)     # decided on bar t's close
        held = np.zeros(n_assets)       # what is actually held over bar t

        for t in range(t_obs):
            if t > 0:
                gross[t] = float(held @ self.ret[t])
            exposure[t] = float(np.abs(held).sum())
            tilt[t] = float(held.sum())

            if t % rebalance == 0:
                target = self._target_weights(t, variant, n_assets)

            # positions decided at t are held from t+1 onwards: no lookahead
            new_held = target
            turn[min(t + 1, t_obs - 1)] += float(np.abs(new_held - held).sum())
            held = new_held

        net = gross - turn * self.cost
        return {
            "gross": np.nan_to_num(gross, nan=0.0, posinf=0.0, neginf=0.0),
            "net": np.nan_to_num(net, nan=0.0, posinf=0.0, neginf=0.0),
            "turnover_per_bar": float(turn.mean()),
            "exposure": float(exposure.mean()),
            "tilt": float(tilt.mean()),
        }

    def run(self, variant: dict) -> np.ndarray:
        return self.run_detail(variant)["net"]
