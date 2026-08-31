"""Strategy families, fully enumerated and vectorised.

Every variant here is a fixed rule with no fitted parameters. Nothing is
optimised in-sample. That matters: the selection bias in a sweep like this
comes entirely from *choosing among* the variants afterwards, which is
exactly what the Deflated Sharpe Ratio and PBO are built to correct for.

Position semantics, stated precisely because reproducibility depends on it:

  - A position opens on the bar where the entry condition first becomes true.
  - It stays open until the exit condition becomes true, or until it has been
    open for `holding_cap_bars` bars, whichever comes first.
  - One position per contiguous run of the entry condition. After a capped
    exit, re-entry requires the entry condition to go false and true again.
  - Long and short are computed independently and summed, so they can net to
    zero but never exceed 1x notional per side.

PERFORMANCE
-----------
Indicators depend only on the lookback, never on the threshold, exit rule or
holding cap. Computing them inside every variant means recomputing the same
six rolling series hundreds of times — with Wilder's RSI, which is inherently
recursive, that dominates the entire runtime. `Indicators` computes each one
once per (symbol, lookback) and caches it.
"""
from __future__ import annotations

import numpy as np

try:
    from scipy.signal import lfilter as _lfilter
except ImportError:
    _lfilter = None


# ---------------------------------------------------------------------
# rolling primitives
# ---------------------------------------------------------------------
def rolling_mean(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(x.shape, np.nan)
    if n > len(x):
        return out
    c = np.concatenate([[0.0], np.cumsum(x)])
    out[n - 1:] = (c[n:] - c[:-n]) / n
    return out


def rolling_std(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(x.shape, np.nan)
    if n > len(x):
        return out
    c1 = np.concatenate([[0.0], np.cumsum(x)])
    c2 = np.concatenate([[0.0], np.cumsum(x * x)])
    s1 = c1[n:] - c1[:-n]
    s2 = c2[n:] - c2[:-n]
    var = (s2 - s1 * s1 / n) / (n - 1)
    out[n - 1:] = np.sqrt(np.maximum(var, 0.0))
    return out


def _wilder_smooth(x: np.ndarray, n: int, seed: float, start: int) -> np.ndarray:
    """Recursive average: y[i] = y[i-1] + (x[i] - y[i-1]) / n."""
    out = np.full(x.shape, np.nan)
    if start >= len(x):
        return out
    alpha = 1.0 / n
    tail = x[start + 1:]
    out[start] = seed
    if tail.size == 0:
        return out
    if _lfilter is not None:
        out[start + 1:] = _lfilter([alpha], [1.0, -(1.0 - alpha)], tail, zi=[seed * (1.0 - alpha)])[0]
    else:
        acc = seed
        buf = np.empty(tail.size)
        one_minus = 1.0 - alpha
        for i, v in enumerate(tail):
            acc = acc * one_minus + v * alpha
            buf[i] = acc
        out[start + 1:] = buf
    return out


def wilder_rsi(close: np.ndarray, n: int) -> np.ndarray:
    if len(close) <= n:
        return np.full(close.shape, np.nan)
    delta = np.diff(close, prepend=close[0])
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)

    avg_gain = _wilder_smooth(gain, n, float(gain[1:n + 1].mean()), n)
    avg_loss = _wilder_smooth(loss, n, float(loss[1:n + 1].mean()), n)

    with np.errstate(divide="ignore", invalid="ignore"):
        rs = np.where(avg_loss > 0, avg_gain / avg_loss, np.inf)
        rsi = 100.0 - 100.0 / (1.0 + rs)
    return rsi


def _shift1(x: np.ndarray) -> np.ndarray:
    out = np.full(x.shape, np.nan)
    out[1:] = x[:-1]
    return out


def _shift_n(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(x.shape, np.nan)
    if n < len(x):
        out[n:] = x[:-n]
    return out


def _ewma(x: np.ndarray, alpha: float) -> np.ndarray:
    """Exponentially weighted mean, seeded with the first value."""
    if _lfilter is not None:
        return _lfilter([alpha], [1.0, -(1.0 - alpha)], x,
                        zi=[x[0] * (1.0 - alpha)])[0]
    out = np.empty_like(x)
    acc = x[0]
    one_minus = 1.0 - alpha
    for i, v in enumerate(x):
        acc = acc * one_minus + v * alpha
        out[i] = acc
    return out


def _rolling_extreme(x: np.ndarray, n: int, better) -> np.ndarray:
    """Rolling min/max in O(len(x)) via a monotonic deque."""
    from collections import deque

    out = np.full(x.shape, np.nan)
    dq: deque = deque()
    for i, v in enumerate(x):
        while dq and better(v, x[dq[-1]]):
            dq.pop()
        dq.append(i)
        if dq[0] <= i - n:
            dq.popleft()
        if i >= n - 1:
            out[i] = x[dq[0]]
    return out


def _rolling_max(x: np.ndarray, n: int) -> np.ndarray:
    return _rolling_extreme(x, n, lambda a, b: a >= b)


def _rolling_min(x: np.ndarray, n: int) -> np.ndarray:
    return _rolling_extreme(x, n, lambda a, b: a <= b)


def _rolling_rank(x: np.ndarray, window: int) -> np.ndarray:
    """Fraction of the trailing window that the current value exceeds.

    Uses only past bars — a percentile computed over the whole series would
    leak the future into every early bar.
    """
    n = len(x)
    out = np.full(n, np.nan)
    if window < 2:
        return out
    from collections import deque
    import bisect

    ordered: list = []
    dq: deque = deque()
    for i, v in enumerate(x):
        if np.isnan(v):
            continue
        bisect.insort(ordered, v)
        dq.append(v)
        if len(dq) > window:
            old = dq.popleft()
            k = bisect.bisect_left(ordered, old)
            if k < len(ordered) and ordered[k] == old:
                ordered.pop(k)
        if len(dq) >= min(window, 50):
            out[i] = bisect.bisect_left(ordered, v) / len(ordered)
    return out


def _ffill_window(arr: np.ndarray, window: int) -> np.ndarray:
    """Forward-fill a level, but only for `window` bars after it appears.

    A fair value gap or order block is not valid forever. Filling indefinitely
    would let a level from years ago trigger a trade today, which nobody
    trading these concepts would do and which quietly inflates the number of
    signals.
    """
    out = np.full(arr.shape, np.nan)
    age = window + 1
    current = np.nan
    for i, v in enumerate(arr):
        if not np.isnan(v):
            current = v
            age = 0
        elif age <= window:
            age += 1
        if age <= window:
            out[i] = current
    return out


def _ffill(arr: np.ndarray) -> np.ndarray:
    idx = np.where(~np.isnan(arr), np.arange(len(arr)), 0)
    np.maximum.accumulate(idx, out=idx)
    return arr[idx]


def _run_length(mask: np.ndarray) -> np.ndarray:
    """Number of consecutive True values ending at each index."""
    c = np.cumsum(mask.astype(np.int64))
    reset = np.maximum.accumulate(np.where(~mask, c, 0))
    return c - reset


def uncapped_side(entry: np.ndarray, exit_: np.ndarray):
    """0/1 holding series ignoring the cap, plus bars-held-so-far.

    Both are independent of `holding_cap_bars`, so they are computed once per
    (family, lookback, threshold, exit_rule) and reused for every cap.
    """
    entry = np.nan_to_num(entry, nan=0.0).astype(bool)
    exit_ = np.nan_to_num(exit_, nan=0.0).astype(bool)

    raw = np.where(entry, 1.0, np.where(exit_, 0.0, np.nan))
    raw[0] = 0.0 if np.isnan(raw[0]) else raw[0]
    held = np.nan_to_num(_ffill(raw), nan=0.0)
    return held, _run_length(held > 0)


def apply_cap(held: np.ndarray, run_len: np.ndarray, cap: int) -> np.ndarray:
    if not cap or cap <= 0:
        return held
    out = held.copy()
    out[run_len > cap] = 0.0
    return out


def build_side(entry: np.ndarray, exit_: np.ndarray, cap: int) -> np.ndarray:
    """Convenience wrapper kept for readability and tests."""
    held, run_len = uncapped_side(entry, exit_)
    return apply_cap(held, run_len, cap)


# ---------------------------------------------------------------------
# cached per-symbol indicators
# ---------------------------------------------------------------------
class Indicators:
    def __init__(self, bars: dict):
        self.close = bars["close"]
        self.high = bars["high"]
        self.low = bars["low"]
        self._mean_sd: dict[int, tuple] = {}
        self._z: dict[int, np.ndarray] = {}
        self._rsi: dict[int, np.ndarray] = {}
        self._ema: dict[int, np.ndarray] = {}
        self._atr: dict[int, np.ndarray] = {}
        self._donchian: dict[int, tuple] = {}
        self._roc: dict[int, np.ndarray] = {}
        self._realised_vol: dict[int, np.ndarray] = {}
        self._log_ret = None
        self._hour = bars.get("hour")

    # -- price-level -------------------------------------------------
    def mean_sd(self, lookback: int):
        if lookback not in self._mean_sd:
            self._mean_sd[lookback] = (
                rolling_mean(self.close, lookback),
                rolling_std(self.close, lookback),
            )
        return self._mean_sd[lookback]

    def zscore(self, lookback: int) -> np.ndarray:
        if lookback not in self._z:
            mean, sd = self.mean_sd(lookback)
            with np.errstate(invalid="ignore", divide="ignore"):
                self._z[lookback] = np.where(sd > 0, (self.close - mean) / sd, np.nan)
        return self._z[lookback]

    def rsi(self, lookback: int) -> np.ndarray:
        if lookback not in self._rsi:
            self._rsi[lookback] = wilder_rsi(self.close, lookback)
        return self._rsi[lookback]

    def ema(self, span: int) -> np.ndarray:
        if span not in self._ema:
            self._ema[span] = _ewma(self.close, 2.0 / (span + 1.0))
        return self._ema[span]

    def donchian(self, lookback: int):
        """Highest high and lowest low over the PREVIOUS `lookback` bars.

        Shifted by one bar deliberately: including the current bar's own high
        in the channel it is supposed to break makes the signal unachievable
        in real time.
        """
        if lookback not in self._donchian:
            hi = _rolling_max(self.high, lookback)
            lo = _rolling_min(self.low, lookback)
            self._donchian[lookback] = (_shift1(hi), _shift1(lo))
        return self._donchian[lookback]

    # -- volatility --------------------------------------------------
    def atr(self, lookback: int) -> np.ndarray:
        if lookback not in self._atr:
            prev_close = _shift1(self.close)
            tr = np.maximum(
                self.high - self.low,
                np.maximum(np.abs(self.high - prev_close),
                           np.abs(self.low - prev_close)),
            )
            tr = np.nan_to_num(tr, nan=0.0)
            self._atr[lookback] = rolling_mean(tr, lookback)
        return self._atr[lookback]

    @property
    def log_ret(self) -> np.ndarray:
        if self._log_ret is None:
            with np.errstate(divide="ignore", invalid="ignore"):
                lr = np.diff(np.log(self.close), prepend=np.log(self.close[0]))
            self._log_ret = np.nan_to_num(lr, nan=0.0, posinf=0.0, neginf=0.0)
        return self._log_ret

    def realised_vol(self, lookback: int) -> np.ndarray:
        if lookback not in self._realised_vol:
            self._realised_vol[lookback] = rolling_std(self.log_ret, lookback)
        return self._realised_vol[lookback]

    def roc(self, lookback: int) -> np.ndarray:
        """Return over the previous `lookback` bars."""
        if lookback not in self._roc:
            past = _shift_n(self.close, lookback)
            with np.errstate(invalid="ignore", divide="ignore"):
                self._roc[lookback] = np.where(past > 0, self.close / past - 1.0, np.nan)
        return self._roc[lookback]

    @property
    def hour(self):
        return self._hour


# ---------------------------------------------------------------------
# families
# ---------------------------------------------------------------------
def _exits(series, mid, lower, upper, exit_rule):
    if exit_rule == "mean_touch":
        return series >= mid, series <= mid
    if exit_rule == "opposite_band":
        return series >= upper, series <= lower
    # fixed_n_bars — the holding cap is the only exit
    zero = np.zeros(series.shape, dtype=bool)
    return zero, zero


def zscore_reversion(ind: Indicators, lookback, threshold, exit_rule):
    z = ind.zscore(lookback)
    lx, sx = _exits(z, 0.0, -threshold, threshold, exit_rule)
    return z < -threshold, lx, z > threshold, sx


def rsi_reversion(ind: Indicators, lookback, threshold, exit_rule):
    rsi = ind.rsi(lookback)
    lower, upper = 50.0 - threshold * 10.0, 50.0 + threshold * 10.0
    lx, sx = _exits(rsi, 50.0, lower, upper, exit_rule)
    return rsi < lower, lx, rsi > upper, sx


def bollinger_touch(ind: Indicators, lookback, threshold, exit_rule):
    mean, sd = ind.mean_sd(lookback)
    upper, lower = mean + threshold * sd, mean - threshold * sd
    if exit_rule == "mean_touch":
        lx, sx = ind.close >= mean, ind.close <= mean
    elif exit_rule == "opposite_band":
        lx, sx = ind.close >= upper, ind.close <= lower
    else:
        zero = np.zeros(mean.shape, dtype=bool)
        lx = sx = zero
    return ind.low < lower, lx, ind.high > upper, sx


# ---------------------------------------------------------------------
# continuation families — exact mirrors of the reversion ones
# ---------------------------------------------------------------------
# Same indicators, same lookbacks, same thresholds, same exit rules. Only the
# direction of entry is flipped. Keeping everything else identical is
# deliberate: any difference in outcome is then attributable to direction and
# nothing else. A structurally different momentum family (breakouts, moving
# average crosses) would confound the comparison.

def zscore_continuation(ind: Indicators, lookback, threshold, exit_rule):
    z = ind.zscore(lookback)
    if exit_rule == "mean_touch":
        lx, sx = z <= 0, z >= 0
    elif exit_rule == "opposite_band":
        lx, sx = z <= -threshold, z >= threshold
    else:
        lx = sx = np.zeros(z.shape, dtype=bool)
    return z > threshold, lx, z < -threshold, sx


def rsi_continuation(ind: Indicators, lookback, threshold, exit_rule):
    rsi = ind.rsi(lookback)
    lower, upper = 50.0 - threshold * 10.0, 50.0 + threshold * 10.0
    if exit_rule == "mean_touch":
        lx, sx = rsi <= 50.0, rsi >= 50.0
    elif exit_rule == "opposite_band":
        lx, sx = rsi <= lower, rsi >= upper
    else:
        lx = sx = np.zeros(rsi.shape, dtype=bool)
    return rsi > upper, lx, rsi < lower, sx


def bollinger_breakout(ind: Indicators, lookback, threshold, exit_rule):
    mean, sd = ind.mean_sd(lookback)
    upper, lower = mean + threshold * sd, mean - threshold * sd
    if exit_rule == "mean_touch":
        lx, sx = ind.close <= mean, ind.close >= mean
    elif exit_rule == "opposite_band":
        lx, sx = ind.close <= lower, ind.close >= upper
    else:
        zero = np.zeros(mean.shape, dtype=bool)
        lx = sx = zero
    return ind.high > upper, lx, ind.low < lower, sx


# ---------------------------------------------------------------------
# additional families
# ---------------------------------------------------------------------
# Each is registered and swept SEPARATELY, never merged into one giant space.
# Adding variants raises the multiple-testing bar for everything in the same
# sweep: 1,620 variants put the detection limit at 4.0 annualised Sharpe,
# 20,000 pushes it to 4.4. Ten clean sweeps beat one enormous one.
#
# `lookback` is the primary window and `entry_threshold` is reused as the
# family's second parameter, so every family fits the same four-parameter
# grid and the same runner. What that second number means is documented per
# family below — it is not the same quantity across families.

def ma_cross(ind: Indicators, lookback, threshold, exit_rule):
    """Moving average crossover. The single most widely sold rule there is.

    threshold = ratio of slow to fast span, so 2.0 means a 20/40 cross.
    """
    fast = ind.ema(int(lookback))
    slow = ind.ema(max(2, int(round(lookback * threshold))))
    above = fast > slow
    if exit_rule == "opposite_band":
        return above, ~above, ~above, above          # always in the market
    if exit_rule == "mean_touch":
        mid = ind.mean_sd(int(lookback))[0]
        return above, ind.close <= mid, ~above, ind.close >= mid
    zero = np.zeros(above.shape, dtype=bool)
    return above, zero, ~above, zero


def donchian_breakout(ind: Indicators, lookback, threshold, exit_rule):
    """Turtle-style channel breakout.

    threshold scales the exit channel: exit uses lookback / threshold bars.
    """
    hi, lo = ind.donchian(int(lookback))
    long_entry, short_entry = ind.close > hi, ind.close < lo
    if exit_rule == "opposite_band":
        short_win = max(2, int(round(lookback / max(threshold, 1e-9))))
        ehi, elo = ind.donchian(short_win)
        return long_entry, ind.close < elo, short_entry, ind.close > ehi
    if exit_rule == "mean_touch":
        mid = ind.mean_sd(int(lookback))[0]
        return long_entry, ind.close < mid, short_entry, ind.close > mid
    zero = np.zeros(long_entry.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def atr_breakout(ind: Indicators, lookback, threshold, exit_rule):
    """Volatility breakout: move more than N ATRs from the recent mean.

    threshold = number of ATRs.
    """
    mean = ind.mean_sd(int(lookback))[0]
    atr = ind.atr(int(lookback))
    up, down = mean + threshold * atr, mean - threshold * atr
    long_entry, short_entry = ind.close > up, ind.close < down
    if exit_rule == "mean_touch":
        return long_entry, ind.close <= mean, short_entry, ind.close >= mean
    if exit_rule == "opposite_band":
        return long_entry, ind.close < down, short_entry, ind.close > up
    zero = np.zeros(long_entry.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def momentum_roc(ind: Indicators, lookback, threshold, exit_rule):
    """Time-series momentum: hold in the direction of the trailing return.

    threshold = minimum absolute return, in percent, to act on.
    """
    roc = ind.roc(int(lookback))
    band = threshold / 100.0
    long_entry, short_entry = roc > band, roc < -band
    if exit_rule == "mean_touch":
        return long_entry, roc <= 0, short_entry, roc >= 0
    if exit_rule == "opposite_band":
        return long_entry, roc < -band, short_entry, roc > band
    zero = np.zeros(long_entry.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def vol_regime_momentum(ind: Indicators, lookback, threshold, exit_rule):
    """Momentum, but only when realised volatility is unusually low.

    threshold = volatility percentile cutoff / 100, so 2.0 means the quietest
    20% of bars. Tests the very common claim that a trend filter "works if you
    only trade the right regime".
    """
    vol = ind.realised_vol(int(lookback))
    ranked = _rolling_rank(vol, min(len(vol), 500))
    quiet = ranked < (threshold / 10.0)
    roc = ind.roc(int(lookback))
    long_entry, short_entry = quiet & (roc > 0), quiet & (roc < 0)
    if exit_rule == "mean_touch":
        return long_entry, roc <= 0, short_entry, roc >= 0
    if exit_rule == "opposite_band":
        return long_entry, ~quiet, short_entry, ~quiet
    zero = np.zeros(long_entry.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def intraday_seasonality(ind: Indicators, lookback, threshold, exit_rule):
    """Hour-of-day effect: go long in one UTC hour block, short in another.

    lookback selects the long block, threshold the short one. Tests calendar
    effects, which are among the easiest patterns to find by accident.
    """
    hour = ind.hour
    if hour is None:
        zero = np.zeros(ind.close.shape, dtype=bool)
        return zero, zero, zero, zero
    long_h = int(lookback) % 24
    short_h = int(round(threshold * 4)) % 24
    long_entry, short_entry = hour == long_h, hour == short_h
    if exit_rule in ("mean_touch", "opposite_band"):
        return long_entry, ~long_entry, short_entry, ~short_entry
    zero = np.zeros(long_entry.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


# ---------------------------------------------------------------------
# price action / "smart money" families
# ---------------------------------------------------------------------
# Only concepts with an UNAMBIGUOUS mechanical definition are here. That is a
# deliberate filter: if a rule needs a human to judge which instance "counts",
# a null result proves nothing, because the answer will always be that it was
# implemented wrong. Every definition below is stated exactly in the
# pre-registration and hashed before the test runs, so that objection is
# available in advance or not at all.
#
# Deliberately EXCLUDED, because no fixed definition exists: market structure
# reading, "context", premium/discount arrays keyed to a discretionary range,
# and anything requiring a chosen higher-timeframe bias.

def fair_value_gap(ind: Indicators, lookback, threshold, exit_rule):
    """Three-bar imbalance: bar t-2's high below bar t's low, or the reverse.

    The gap is unfilled displacement. The standard claim is that price returns
    to it. `threshold` is the minimum gap size in ATR units, so tiny gaps that
    are really just spread do not count. `lookback` sets how long a gap stays
    live.
    """
    high, low, close = ind.high, ind.low, ind.close
    atr = ind.atr(14)

    prev2_high = _shift_n(high, 2)
    prev2_low = _shift_n(low, 2)

    with np.errstate(invalid="ignore"):
        bull_gap = low - prev2_high          # gap up: unfilled space below
        bear_gap = prev2_low - high          # gap down: unfilled space above
        min_size = threshold * atr
        bull = bull_gap > np.maximum(min_size, 0)
        bear = bear_gap > np.maximum(min_size, 0)

    # a gap stays live for `lookback` bars, and price entering it is the entry
    bull_level = np.where(bull, prev2_high, np.nan)
    bear_level = np.where(bear, prev2_low, np.nan)
    live_bull = _ffill_window(bull_level, int(lookback))
    live_bear = _ffill_window(bear_level, int(lookback))

    long_entry = np.nan_to_num(low <= live_bull, nan=0.0).astype(bool) & ~np.isnan(live_bull)
    short_entry = np.nan_to_num(high >= live_bear, nan=0.0).astype(bool) & ~np.isnan(live_bear)

    mid = ind.mean_sd(int(lookback))[0]
    if exit_rule == "mean_touch":
        return long_entry, close >= mid, short_entry, close <= mid
    if exit_rule == "opposite_band":
        return long_entry, short_entry, short_entry, long_entry
    zero = np.zeros(close.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def order_block(ind: Indicators, lookback, threshold, exit_rule):
    """Last opposite-direction bar before a displacement move.

    Bullish: a down bar immediately followed by a move up of at least
    `threshold` ATR. The claim is that price returning to that bar's range
    finds support. `lookback` is how long the block stays live.
    """
    high, low, close = ind.high, ind.low, ind.close
    atr = ind.atr(14)
    prev_close = _shift1(close)

    with np.errstate(invalid="ignore"):
        move = close - prev_close
        down_bar = _shift1(close) < _shift_n(close, 2)
        up_bar = _shift1(close) > _shift_n(close, 2)
        displaced_up = move > threshold * atr
        displaced_down = move < -threshold * atr

    bull_block = down_bar & displaced_up
    bear_block = up_bar & displaced_down

    bull_level = np.where(bull_block, _shift1(low), np.nan)
    bear_level = np.where(bear_block, _shift1(high), np.nan)
    live_bull = _ffill_window(bull_level, int(lookback))
    live_bear = _ffill_window(bear_level, int(lookback))

    long_entry = (low <= live_bull) & ~np.isnan(live_bull)
    short_entry = (high >= live_bear) & ~np.isnan(live_bear)

    mid = ind.mean_sd(int(lookback))[0]
    if exit_rule == "mean_touch":
        return long_entry, close >= mid, short_entry, close <= mid
    if exit_rule == "opposite_band":
        return long_entry, short_entry, short_entry, long_entry
    zero = np.zeros(close.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def liquidity_sweep(ind: Indicators, lookback, threshold, exit_rule):
    """Stop hunt: take out a prior extreme, then close back inside.

    The most falsifiable smart-money claim there is. `threshold` is how far
    beyond the level, in ATR, the wick must reach.
    """
    high, low, close = ind.high, ind.low, ind.close
    atr = ind.atr(14)
    prior_high, prior_low = ind.donchian(int(lookback))

    with np.errstate(invalid="ignore"):
        swept_high = (high > prior_high + threshold * atr) & (close < prior_high)
        swept_low = (low < prior_low - threshold * atr) & (close > prior_low)

    # sweeping the highs traps longs, so the trade is short, and vice versa
    long_entry = np.nan_to_num(swept_low, nan=0.0).astype(bool)
    short_entry = np.nan_to_num(swept_high, nan=0.0).astype(bool)

    mid = ind.mean_sd(int(lookback))[0]
    if exit_rule == "mean_touch":
        return long_entry, close >= mid, short_entry, close <= mid
    if exit_rule == "opposite_band":
        return long_entry, short_entry, short_entry, long_entry
    zero = np.zeros(close.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def break_of_structure(ind: Indicators, lookback, threshold, exit_rule):
    """Close decisively beyond a prior swing extreme.

    The one piece of market structure with a fixed definition: a close beyond
    the previous `lookback`-bar extreme by at least `threshold` ATR. Everything
    else under that heading requires human judgement and is excluded.
    """
    close = ind.close
    atr = ind.atr(14)
    prior_high, prior_low = ind.donchian(int(lookback))

    with np.errstate(invalid="ignore"):
        long_entry = close > prior_high + threshold * atr
        short_entry = close < prior_low - threshold * atr

    long_entry = np.nan_to_num(long_entry, nan=0.0).astype(bool)
    short_entry = np.nan_to_num(short_entry, nan=0.0).astype(bool)

    mid = ind.mean_sd(int(lookback))[0]
    if exit_rule == "mean_touch":
        return long_entry, close <= mid, short_entry, close >= mid
    if exit_rule == "opposite_band":
        return long_entry, short_entry, short_entry, long_entry
    zero = np.zeros(close.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def engulfing(ind: Indicators, lookback, threshold, exit_rule):
    """Classic engulfing candle. The oldest published pattern of them all.

    `threshold` is the minimum body size relative to the trailing average
    body, so a marginal engulf does not count.
    """
    close, high, low = ind.close, ind.high, ind.low
    open_ = _shift1(close)                      # bar open ~ previous close
    body = np.abs(close - open_)
    avg_body = rolling_mean(np.nan_to_num(body, nan=0.0), int(lookback))

    prev_open, prev_close = _shift1(open_), _shift1(close)
    with np.errstate(invalid="ignore"):
        big = body > threshold * avg_body
        bull = (close > open_) & (prev_close < prev_open) & \
               (close >= prev_open) & (open_ <= prev_close) & big
        bear = (close < open_) & (prev_close > prev_open) & \
               (close <= prev_open) & (open_ >= prev_close) & big

    long_entry = np.nan_to_num(bull, nan=0.0).astype(bool)
    short_entry = np.nan_to_num(bear, nan=0.0).astype(bool)

    mid = ind.mean_sd(int(lookback))[0]
    if exit_rule == "mean_touch":
        return long_entry, close <= mid, short_entry, close >= mid
    if exit_rule == "opposite_band":
        return long_entry, short_entry, short_entry, long_entry
    zero = np.zeros(close.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


def inside_bar_breakout(ind: Indicators, lookback, threshold, exit_rule):
    """Range contraction then expansion: a bar inside the previous bar's
    range, followed by a break of that range.

    `lookback` sets how many consecutive inside bars are required; `threshold`
    scales the breakout distance in ATR.
    """
    high, low, close = ind.high, ind.low, ind.close
    atr = ind.atr(14)

    with np.errstate(invalid="ignore"):
        inside = (high <= _shift1(high)) & (low >= _shift1(low))
    inside = np.nan_to_num(inside, nan=0.0).astype(bool)

    need = max(1, int(lookback) // 10)
    streak = _run_length(inside) >= need

    ref_high = _shift1(np.where(inside, _shift1(high), np.nan))
    ref_low = _shift1(np.where(inside, _shift1(low), np.nan))
    live_high = _ffill_window(ref_high, 20)
    live_low = _ffill_window(ref_low, 20)

    # _shift1 returns floats (it pads with NaN), so cast back before combining
    prev_streak = np.nan_to_num(_shift1(streak.astype(float)), nan=0.0) > 0.5
    with np.errstate(invalid="ignore"):
        long_entry = prev_streak & (close > live_high + threshold * atr)
        short_entry = prev_streak & (close < live_low - threshold * atr)

    long_entry = np.nan_to_num(long_entry, nan=0.0).astype(bool)
    short_entry = np.nan_to_num(short_entry, nan=0.0).astype(bool)

    mid = ind.mean_sd(max(20, int(lookback)))[0]
    if exit_rule == "mean_touch":
        return long_entry, close <= mid, short_entry, close >= mid
    if exit_rule == "opposite_band":
        return long_entry, short_entry, short_entry, long_entry
    zero = np.zeros(close.shape, dtype=bool)
    return long_entry, zero, short_entry, zero


FAMILIES = {
    "zscore_reversion": zscore_reversion,
    "rsi_reversion": rsi_reversion,
    "bollinger_touch": bollinger_touch,
    "zscore_continuation": zscore_continuation,
    "rsi_continuation": rsi_continuation,
    "bollinger_breakout": bollinger_breakout,
    "ma_cross": ma_cross,
    "donchian_breakout": donchian_breakout,
    "atr_breakout": atr_breakout,
    "momentum_roc": momentum_roc,
    "vol_regime_momentum": vol_regime_momentum,
    "intraday_seasonality": intraday_seasonality,
    "fair_value_gap": fair_value_gap,
    "order_block": order_block,
    "liquidity_sweep": liquidity_sweep,
    "break_of_structure": break_of_structure,
    "engulfing": engulfing,
    "inside_bar_breakout": inside_bar_breakout,
}
