"""Backtest execution: signals in, per-bar net returns out."""
from __future__ import annotations

import itertools

import numpy as np

from .families import FAMILIES, Indicators, apply_cap, uncapped_side


def enumerate_variants(search_space: dict) -> list[dict]:
    """Cartesian product of every declared parameter, in a canonical order.

    Fully enumerated — no variant is added or dropped after the fact. The
    ordering groups variants that share everything but the holding cap, which
    lets the runner reuse the expensive part of the position state machine.
    Column order is recorded in variant_names.txt, so it is reproducible.
    """
    params = search_space["parameters"]
    keys = sorted(params)
    variants = []
    for family in sorted(search_space["families"]):
        for combo in itertools.product(*(params[k] for k in keys)):
            v = dict(zip(keys, combo))
            v["family"] = family
            variants.append(v)

    variants.sort(key=lambda v: (
        v["family"], v["lookback"], v["entry_threshold"],
        v["exit_rule"], v["holding_cap_bars"],
    ))
    return variants


class Runner:
    """Runs every variant for one symbol, reusing shared work.

    Two levels of caching, both driven by the observation that most of the
    cost does not depend on most of the parameters:
      - indicators depend only on the lookback (handled by Indicators)
      - the uncapped position series depends on everything except the cap
    With variants sorted so the cap varies fastest, a one-slot cache is enough.
    """

    def __init__(self, bars: dict, cost_bps: float):
        self.ind = Indicators(bars)
        self.cost = cost_bps / 10_000.0
        close = self.ind.close
        ret = np.zeros_like(close)
        ret[1:] = close[1:] / close[:-1] - 1.0

        # Markets that close leave gaps. The jump across a closed weekend is a
        # real return for anyone holding, but it is not tradable within the
        # bar and it dwarfs ordinary hourly moves, so a handful of Sunday
        # opens would otherwise dominate every statistic in the sweep.
        # `is_gap` marks bars that follow a break longer than one interval;
        # their return is excluded and no position is carried across.
        self.gap = np.zeros(close.shape, dtype=bool)
        times = bars.get("time")
        if times is not None and len(times) > 2:
            deltas = np.diff(times)
            step = int(np.median(deltas))
            if step > 0:
                self.gap[1:] = deltas > step
                ret[self.gap] = 0.0

        self.ret = ret                       # identical for every variant
        self._key = None
        self._sides = None

    def _sides_for(self, family, lookback, threshold, exit_rule):
        key = (family, lookback, threshold, exit_rule)
        if key != self._key:
            le, lx, se, sx = FAMILIES[family](
                self.ind, lookback, threshold, exit_rule
            )
            self._sides = (uncapped_side(le, lx), uncapped_side(se, sx))
            self._key = key
        return self._sides

    def run(self, variant: dict) -> np.ndarray:
        (l_held, l_run), (s_held, s_run) = self._sides_for(
            variant["family"], int(variant["lookback"]),
            float(variant["entry_threshold"]), variant["exit_rule"],
        )
        cap = int(variant["holding_cap_bars"])
        position = apply_cap(l_held, l_run, cap) - apply_cap(s_held, s_run, cap)
        return self._net_returns(position)

    def run_detail(self, variant: dict) -> dict:
        """Same position, decomposed: gross returns, costs, turnover.

        Lets a diagnostic separate "there is no signal" from "there is a
        signal and costs ate it" — two findings that look identical if you
        only ever look at net returns.
        """
        (l_held, l_run), (s_held, s_run) = self._sides_for(
            variant["family"], int(variant["lookback"]),
            float(variant["entry_threshold"]), variant["exit_rule"],
        )
        cap = int(variant["holding_cap_bars"])
        position = apply_cap(l_held, l_run, cap) - apply_cap(s_held, s_run, cap)

        held = np.empty_like(position)
        held[0] = 0.0
        held[1:] = position[:-1]
        held[self.gap] = 0.0                 # flat across market closures
        turnover = np.abs(np.diff(held, prepend=0.0))

        gross = np.nan_to_num(held * self.ret, nan=0.0, posinf=0.0, neginf=0.0)
        return {
            "gross": gross,
            "net": gross - turnover * self.cost,
            "turnover_per_bar": float(turnover.mean()),
            "exposure": float(np.abs(held).mean()),
            # signed average position: a rule that fades a rising market is
            # structurally short, and would lose money with or without signal
            "tilt": float(held.mean()),
        }

    def _net_returns(self, position: np.ndarray) -> np.ndarray:
        """Decide on bar t's close, hold over bar t+1. No lookahead.
        Costs are charged on the size of every position change."""
        held = np.empty_like(position)
        held[0] = 0.0
        held[1:] = position[:-1]
        held[self.gap] = 0.0                 # flat across market closures
        turnover = np.abs(np.diff(held, prepend=0.0))
        out = held * self.ret - turnover * self.cost
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


def net_returns(close: np.ndarray, position: np.ndarray, cost_bps: float) -> np.ndarray:
    """Standalone version, kept for tests and one-off use."""
    ret = np.zeros_like(close)
    ret[1:] = close[1:] / close[:-1] - 1.0
    held = np.zeros_like(position)
    held[1:] = position[:-1]
    turnover = np.abs(np.diff(held, prepend=0.0))
    return np.nan_to_num(held * ret - turnover * (cost_bps / 10_000.0),
                         nan=0.0, posinf=0.0, neginf=0.0)
