"""Statistics for multiple-testing-corrected strategy evaluation.

Pure standard library. No numpy needed here.

References
----------
Bailey, D. and Lopez de Prado, M. (2014).
"The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest
Overfitting and Non-Normality." Journal of Portfolio Management.

All Sharpe ratios in this module are PER-OBSERVATION (not annualised)
unless a function name says otherwise. Mixing the two is the single most
common way to get a wrong answer here.
"""
from __future__ import annotations

import math
from statistics import NormalDist

ND = NormalDist()
EULER_MASCHERONI = 0.5772156649015329


# ---------------------------------------------------------------------
# basic moments
# ---------------------------------------------------------------------
def sharpe(returns: list[float]) -> float:
    """Per-observation Sharpe ratio. Excess returns assumed."""
    n = len(returns)
    if n < 2:
        return 0.0
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / (n - 1)
    if var <= 0:
        return 0.0
    return mean / math.sqrt(var)


def skewness(returns: list[float]) -> float:
    n = len(returns)
    if n < 3:
        return 0.0
    mean = sum(returns) / n
    m2 = sum((r - mean) ** 2 for r in returns) / n
    m3 = sum((r - mean) ** 3 for r in returns) / n
    if m2 <= 0:
        return 0.0
    return m3 / m2 ** 1.5


def kurtosis(returns: list[float]) -> float:
    """NON-excess kurtosis. A normal distribution gives 3.0."""
    n = len(returns)
    if n < 4:
        return 3.0
    mean = sum(returns) / n
    m2 = sum((r - mean) ** 2 for r in returns) / n
    m4 = sum((r - mean) ** 4 for r in returns) / n
    if m2 <= 0:
        return 3.0
    return m4 / m2 ** 2


def variance(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return sum((v - mean) ** 2 for v in values) / (n - 1)


def annualise(sr_per_obs: float, periods_per_year: int) -> float:
    return sr_per_obs * math.sqrt(periods_per_year)


# ---------------------------------------------------------------------
# the multiple-testing correction
# ---------------------------------------------------------------------
def expected_max_sharpe(n_trials: int, var_of_trial_sharpes: float) -> float:
    """E[max SR] when every strategy tested has a TRUE Sharpe of zero.

    This is the number people never compute. Test 1,000 worthless
    strategies and the best one will still look good — this says exactly
    how good, purely by luck. Anything below it is noise.
    """
    if n_trials < 2 or var_of_trial_sharpes <= 0:
        return 0.0
    sd = math.sqrt(var_of_trial_sharpes)
    g = EULER_MASCHERONI
    a = ND.inv_cdf(1.0 - 1.0 / n_trials)
    b = ND.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    return sd * ((1.0 - g) * a + g * b)


def _dsr_denominator(sr: float, skew: float, kurt: float) -> float:
    inner = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr * sr
    if inner <= 0:
        raise ValueError(
            f"DSR variance term is non-positive (inner={inner:.6g}). "
            "Check that skew/kurtosis and SR are on the same per-observation scale."
        )
    return math.sqrt(inner)


def deflated_sharpe(
    sr_observed: float,
    sr_benchmark: float,
    t_obs: int,
    skew: float,
    kurt: float,
) -> float:
    """Probability the observed Sharpe reflects genuine skill, not selection.

    Returns a probability in [0, 1]. Convention: >= 0.95 to claim an edge.
    """
    if t_obs < 2:
        return 0.0
    num = (sr_observed - sr_benchmark) * math.sqrt(t_obs - 1)
    return ND.cdf(num / _dsr_denominator(sr_observed, skew, kurt))


# ---------------------------------------------------------------------
# the part almost nobody publishes
# ---------------------------------------------------------------------
def critical_sharpe(
    sr_benchmark: float,
    t_obs: int,
    skew: float,
    kurt: float,
    alpha: float = 0.05,
) -> float:
    """Smallest OBSERVED Sharpe that would clear DSR >= 1 - alpha."""
    target = ND.inv_cdf(1.0 - alpha)

    def f(sr: float) -> float:
        return (sr - sr_benchmark) * math.sqrt(t_obs - 1) / _dsr_denominator(
            sr, skew, kurt
        ) - target

    lo, hi = sr_benchmark, sr_benchmark + 1.0
    for _ in range(200):
        try:
            if f(hi) > 0:
                break
        except ValueError:
            break
        hi += 1.0
    for _ in range(300):
        mid = (lo + hi) / 2.0
        try:
            val = f(mid)
        except ValueError:
            hi = mid
            continue
        if val > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def min_detectable_sharpe(
    n_trials: int,
    var_of_trial_sharpes: float,
    t_obs: int,
    skew: float = 0.0,
    kurt: float = 3.0,
    alpha: float = 0.05,
    power: float = 0.80,
) -> float:
    """The DETECTION LIMIT: smallest TRUE Sharpe this design could find.

    Without this number a negative result is meaningless. "We found
    nothing" can mean the edge was not there, or that the instrument was
    too blunt to see it. This says which.
    """
    sr_b = expected_max_sharpe(n_trials, var_of_trial_sharpes)
    crit = critical_sharpe(sr_b, t_obs, skew, kurt, alpha)
    z_power = ND.inv_cdf(power)

    s = crit
    for _ in range(500):
        inner = 1.0 - skew * s + ((kurt - 1.0) / 4.0) * s * s
        se = math.sqrt(max(inner, 1e-12) / (t_obs - 1))
        s_new = crit + z_power * se
        if abs(s_new - s) < 1e-14:
            break
        s = s_new
    return s
