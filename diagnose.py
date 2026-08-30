#!/usr/bin/env python3
"""Diagnose WHY a sweep failed. Mechanism, not just verdict.

    python diagnose.py sweeps/SW-0002

"No edge found" has at least two very different causes that look identical
if you only ever inspect net returns:

    (a) there is no signal at all — gross Sharpe is centred on zero
    (b) there is a signal, and transaction costs eat it

This decomposes every variant into gross returns, cost drag and turnover,
then reports which one you are looking at.

Reads the FROZEN pre-registration and re-runs the same enumerated space, so
it cannot quietly widen or narrow what was tested. It reads no holdout data
and changes no verdict — it only explains the one already recorded.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

from srlab.canonical import canonical_sha256
from srlab.stats import annualise
from sweep.engine import Runner, enumerate_variants

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_sweep import load_bars  # noqa: E402


def sharpe_of(x: np.ndarray) -> float:
    sd = x.std(ddof=1)
    return float(x.mean() / sd) if sd > 0 else 0.0


def r_squared(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 3 or x.std() == 0 or y.std() == 0:
        return 0.0
    r = float(np.corrcoef(x, y)[0, 1])
    return r * r


def pct(vals: np.ndarray, q: float) -> float:
    return float(np.percentile(vals, q))


def sweep_stats(bars_by_symbol, variants, symbols, cost_bps, ppy, quiet=False):
    """Run the whole space and summarise. Used for the real data and, with
    shuffled prices, for the null distribution."""
    gross_sr, net_sr, turnover, exposure, breakeven = [], [], [], [], []
    tilt, beta, resid_sr = [], [], []
    total = len(variants) * len(symbols)
    done = 0

    for symbol in symbols:
        runner = Runner(bars_by_symbol[symbol], cost_bps)
        mkt = runner.ret
        mvar = float(mkt.var())
        for v in variants:
            det = runner.run_detail(v)
            g, n = det["gross"], det["net"]
            done += 1
            if det["turnover_per_bar"] <= 0 and not np.any(g):
                continue

            gross_sr.append(sharpe_of(g))
            net_sr.append(sharpe_of(n))
            turnover.append(det["turnover_per_bar"])
            exposure.append(det["exposure"])
            tilt.append(det["tilt"])

            b = float(np.cov(g, mkt, ddof=1)[0, 1] / mvar) if mvar > 0 else 0.0
            beta.append(b)
            resid_sr.append(sharpe_of(g - b * mkt))

            tpb = det["turnover_per_bar"]
            breakeven.append(1e4 * float(g.mean()) / tpb if tpb > 0 else float("nan"))

            if not quiet and (done % 200 == 0 or done == total):
                print(f"  {done:,}/{total:,}", end="\r", flush=True)

    return {
        "gross_sr": annualise(np.array(gross_sr), ppy),
        "net_sr": annualise(np.array(net_sr), ppy),
        "resid_sr": annualise(np.array(resid_sr), ppy),
        "turnover": np.array(turnover),
        "exposure": np.array(exposure),
        "tilt": np.array(tilt),
        "beta": np.array(beta),
        "breakeven": np.array(breakeven),
    }


def shuffled_bars(bars: dict, rng) -> dict:
    """Rebuild a price path from the SAME bar returns in random order.

    Preserves the return distribution — volatility, fat tails, skew — and
    destroys every trace of serial structure. Any pattern a strategy finds
    here is by construction not a pattern. This is what the real result has
    to be measured against.
    """
    close = bars["close"]
    log_ret = np.diff(np.log(close))
    rng.shuffle(log_ret)
    new_close = close[0] * np.exp(np.concatenate([[0.0], np.cumsum(log_ret)]))

    hi_frac = np.divide(bars["high"], close, out=np.ones_like(close), where=close > 0)
    lo_frac = np.divide(bars["low"], close, out=np.ones_like(close), where=close > 0)
    order = rng.permutation(close.size)
    out = {
        "close": new_close,
        "high": new_close * hi_frac[order],
        "low": new_close * lo_frac[order],
    }
    if "hour" in bars:
        out["hour"] = bars["hour"]   # calendar is real even when prices are not
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sweep_dir")
    ap.add_argument("--null", type=int, default=10,
                    help="shuffled datasets for null calibration (0 to skip)")
    args = ap.parse_args()
    n_null = args.null

    d = args.sweep_dir.rstrip("/")
    frozen = os.path.join(d, "preregistration.frozen.json")
    if not os.path.exists(frozen):
        sys.exit("no frozen pre-registration")

    with open(frozen, encoding="utf-8") as fh:
        prereg = json.load(fh)
    with open(os.path.join(d, "preregistration.sha256"), encoding="utf-8") as fh:
        stored = json.load(fh)["preregistration_sha256"]
    if canonical_sha256(prereg) != stored:
        sys.exit("frozen pre-registration hash mismatch")

    data = prereg["data"]
    proto = prereg["protocol"]
    cost_bps = float(proto["costs_bps"]) + float(proto["slippage_bps"])
    ppy = int(prereg["planning"]["periods_per_year"])

    variants = enumerate_variants(prereg["search_space"])
    symbols = data["symbols"]

    bars = {s: load_bars(s, data["timeframe"], data["start"], data["end"])
            for s in symbols}
    n_bars = min(len(b["close"]) for b in bars.values())
    for s in symbols:
        for k in ("open", "high", "low", "close", "time", "hour"):
            bars[s][k] = bars[s][k][-n_bars:]

    real = sweep_stats(bars, variants, symbols, cost_bps, ppy)
    print()
    gross_sr, net_sr, resid_sr = real["gross_sr"], real["net_sr"], real["resid_sr"]
    turnover, exposure = real["turnover"], real["exposure"]
    tilt, beta, breakeven = real["tilt"], real["beta"], real["breakeven"]

    # ---- null calibration ------------------------------------------
    # The instrument itself has a bias: on data with provably no structure it
    # still reports a negative residual Sharpe. Without measuring that bias
    # you will publish it as a discovery.
    null = None
    if n_null > 0:
        print(f"  calibrating against {n_null} shuffled null datasets")
        rng = np.random.default_rng(20260731)
        means = []
        for i in range(n_null):
            fake = {sym: shuffled_bars(bars[sym], rng) for sym in symbols}
            st = sweep_stats(fake, variants, symbols, cost_bps, ppy, quiet=True)
            means.append(float(st["resid_sr"].mean()))
            print(f"    null {i + 1}/{n_null}: {means[-1]:+.4f}", end="\r", flush=True)
        print()
        arr = np.array(means)
        sd = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
        obs = float(resid_sr.mean())
        null = {
            "n_runs": n_null,
            "residual_sharpe_mean": round(float(arr.mean()), 4),
            "residual_sharpe_sd": round(sd, 4),
            "observed": round(obs, 4),
            "z_score": round((obs - float(arr.mean())) / sd, 3) if sd > 0 else None,
            "note": ("Null datasets reuse the real bar returns in random order: "
                     "same distribution, no serial structure. If the observed "
                     "value sits inside this spread it is an artefact of the "
                     "measurement, not a property of the market."),
        }

    # how much of the spread in net Sharpe is just turnover?
    r2_turnover = r_squared(turnover, net_sr)
    r2_log_turnover = r_squared(np.log(np.maximum(turnover, 1e-12)), net_sr)
    r2_gross = r_squared(gross_sr, net_sr)
    r2_tilt_gross = r_squared(tilt, gross_sr)
    r2_beta_gross = r_squared(beta, gross_sr)

    finite_be = breakeven[np.isfinite(breakeven)]
    positive_gross = float((gross_sr > 0).mean())

    mkt_explains = max(r2_tilt_gross, r2_beta_gross)
    z = (null or {}).get("z_score")

    if abs(gross_sr.mean()) < 0.15 and 0.4 < positive_gross < 0.6:
        mechanism = ("NO SIGNAL. Gross Sharpe is centred on zero — the rules "
                     "carry no predictive content before costs are charged.")
    elif gross_sr.mean() > 0.3 and net_sr.mean() < 0:
        mechanism = ("SIGNAL DESTROYED BY COSTS. Gross returns are positive on "
                     "average; the cost of trading them is larger than the edge.")
    elif gross_sr.mean() < -0.15:
        if null is not None and (z is None or abs(z) < 2.0):
            mechanism = (
                "ARTEFACT, NOT SIGNAL. Gross returns are negative, but shuffled "
                f"data with no structure at all produces "
                f"{null['residual_sharpe_mean']:+.2f} residual Sharpe against an "
                f"observed {null['observed']:+.2f} (z = {z}). The negative result "
                "is a property of the measurement, not of the market. Claim "
                "nothing from it.")
        elif mkt_explains > 0.5 or abs(resid_sr.mean()) < 0.15:
            mechanism = (
                "DIRECTIONAL EXPOSURE, NOT SIGNAL. Gross returns are negative, "
                "but market exposure explains "
                f"{mkt_explains:.0%} of the spread and the market-neutral "
                f"residual Sharpe is {resid_sr.mean():.2f}. These rules were "
                "structurally short a market that rose. That is arithmetic, "
                "not a finding — do not claim an inverted edge from it.")
        else:
            mechanism = (
                "SIGNAL WITH INVERTED SIGN. Gross returns are negative and stay "
                f"negative after removing market exposure (residual Sharpe "
                f"{resid_sr.mean():.2f}, market explains only {mkt_explains:.0%}). "
                "The rules carry predictive content pointing the wrong way. "
                "Note this is still a fitted direction chosen after the fact — "
                "the opposite rules must be pre-registered and tested separately.")
    else:
        mechanism = ("MIXED. Gross returns are neither clearly zero nor clearly "
                     "positive — treat the mechanism as unresolved.")

    result = {
        "sweep_id": prereg["sweep_id"],
        "preregistration_sha256": stored,
        "cost_bps_total": cost_bps,
        "n_variants": int(gross_sr.size),
        "gross_sharpe_annual": {
            "mean": round(float(gross_sr.mean()), 4),
            "median": round(pct(gross_sr, 50), 4),
            "p05": round(pct(gross_sr, 5), 4),
            "p95": round(pct(gross_sr, 95), 4),
            "max": round(float(gross_sr.max()), 4),
            "share_positive": round(positive_gross, 4),
        },
        "net_sharpe_annual": {
            "mean": round(float(net_sr.mean()), 4),
            "median": round(pct(net_sr, 50), 4),
            "max": round(float(net_sr.max()), 4),
            "share_positive": round(float((net_sr > 0).mean()), 4),
        },
        "turnover_per_bar": {
            "median": round(float(np.median(turnover)), 6),
            "p05": round(pct(turnover, 5), 6),
            "p95": round(pct(turnover, 95), 6),
        },
        "mean_exposure": round(float(exposure.mean()), 4),
        "directional_tilt": {
            "mean": round(float(tilt.mean()), 4),
            "median": round(float(np.median(tilt)), 4),
            "share_net_short": round(float((tilt < 0).mean()), 4),
        },
        "market_beta": {
            "mean": round(float(beta.mean()), 4),
            "median": round(float(np.median(beta)), 4),
        },
        "market_neutral_residual_sharpe_annual": {
            "mean": round(float(resid_sr.mean()), 4),
            "median": round(float(np.median(resid_sr)), 4),
            "share_positive": round(float((resid_sr > 0).mean()), 4),
        },
        "variance_explained": {
            "net_sharpe_by_turnover": round(r2_turnover, 4),
            "net_sharpe_by_log_turnover": round(r2_log_turnover, 4),
            "net_sharpe_by_gross_sharpe": round(r2_gross, 4),
            "gross_sharpe_by_directional_tilt": round(r2_tilt_gross, 4),
            "gross_sharpe_by_market_beta": round(r2_beta_gross, 4),
        },
        "breakeven_cost_bps": {
            "best_variant": round(float(np.nanmax(finite_be)), 3)
            if finite_be.size else None,
            "median": round(float(np.nanmedian(finite_be)), 3)
            if finite_be.size else None,
            "note": "round-trip cost at which a variant's mean return reaches zero",
        },
        "mechanism": mechanism,
        "null_calibration": null,
    }

    out = os.path.join(d, "diagnostics.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)

    g, nsr, ve = (result["gross_sharpe_annual"], result["net_sharpe_annual"],
                  result["variance_explained"])
    print(f"\n{result['sweep_id']} — mechanism diagnosis\n")
    print(f"  gross Sharpe  mean {g['mean']:>8}   median {g['median']:>8}"
          f"   max {g['max']:>8}   positive {g['share_positive']:.1%}")
    print(f"  net Sharpe    mean {nsr['mean']:>8}   median {nsr['median']:>8}"
          f"   max {nsr['max']:>8}   positive {nsr['share_positive']:.1%}")
    print()
    print(f"  net Sharpe variance explained by turnover      : {ve['net_sharpe_by_turnover']:.1%}")
    print(f"  ... by log turnover                            : {ve['net_sharpe_by_log_turnover']:.1%}")
    print(f"  ... by gross Sharpe                            : {ve['net_sharpe_by_gross_sharpe']:.1%}")
    rs = result["market_neutral_residual_sharpe_annual"]
    print(f"  market-neutral residual Sharpe: mean {rs['mean']:>8}"
          f"   median {rs['median']:>8}   positive {rs['share_positive']:.1%}")
    print(f"  gross Sharpe explained by directional tilt     : "
          f"{ve['gross_sharpe_by_directional_tilt']:.1%}")
    print(f"  ... by market beta                             : "
          f"{ve['gross_sharpe_by_market_beta']:.1%}")
    print(f"  mean tilt {result['directional_tilt']['mean']:+.4f}"
          f"   net short in {result['directional_tilt']['share_net_short']:.1%} of variants")

    be = result["breakeven_cost_bps"]
    if be["best_variant"] is not None:
        print(f"\n  breakeven cost, best variant : {be['best_variant']} bps "
              f"(charged: {cost_bps} bps)")
    if null is not None:
        print(f"\n  null (shuffled) residual Sharpe : {null['residual_sharpe_mean']:+.4f}"
              f"  sd {null['residual_sharpe_sd']:.4f}   over {null['n_runs']} runs")
        print(f"  observed                        : {null['observed']:+.4f}"
              f"   z = {null['z_score']}")
    print(f"\n  {result['mechanism']}")
    print(f"\n  wrote {out}")


if __name__ == "__main__":
    main()
