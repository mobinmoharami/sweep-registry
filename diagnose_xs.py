#!/usr/bin/env python3
"""Mechanism diagnosis for CROSS-SECTIONAL sweeps.

diagnose.py reads data["symbols"] as a list of tradable symbols and hands
them to load_bars. A cross-sectional pre-registration puts a description
there instead, so that path cannot run. This builds the same panel
run_xs_sweep.py builds and decomposes every variant through
CrossSectionalRunner.run_detail.

NULL CALIBRATION
----------------
Each asset's returns are shuffled INDEPENDENTLY. A shared permutation
would preserve the cross-asset structure this sweep exists to test,
which is exactly what the null has to destroy.

MARKET
------
The equal-weighted mean return of the investable universe at each bar.
"""
from __future__ import annotations
import json, os, sys
from datetime import datetime, timezone
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srlab.canonical import canonical_sha256
from srlab.stats import annualise
from sweep.cross_sectional import CrossSectionalRunner
from sweep.engine import enumerate_variants
from run_xs_sweep import load_series


def sharpe_of(x):
    sd = x.std(ddof=1)
    return float(x.mean() / sd) if sd > 0 else 0.0


def r_squared(x, y):
    if x.size < 3 or x.std() == 0 or y.std() == 0:
        return 0.0
    r = float(np.corrcoef(x, y)[0, 1])
    return r * r


def build_panel(prereg):
    data = prereg["data"]
    here = os.path.dirname(os.path.abspath(__file__))
    uni = json.load(open(os.path.join(here, "data", "universe",
                                      data["universe"] + ".json"), encoding="utf-8"))
    series = {}
    for s in uni["all_symbols_ever"]:
        x = load_series(s, data["timeframe"])
        if x:
            series[s] = x
    lo = int(datetime.fromisoformat(data["start"]).replace(tzinfo=timezone.utc).timestamp() * 1000)
    hi = int(datetime.fromisoformat(data["end"]).replace(tzinfo=timezone.utc).timestamp() * 1000)
    stamps = sorted({t for v in series.values() for t in v if lo <= t <= hi})
    act = sorted(series)
    idx = {t: i for i, t in enumerate(stamps)}
    prices = np.full((len(stamps), len(act)), np.nan)
    for j, s in enumerate(act):
        for t, p in series[s].items():
            i = idx.get(t)
            if i is not None:
                prices[i, j] = p
    member = np.zeros(prices.shape, dtype=bool)
    col = {s: j for j, s in enumerate(act)}
    for i, t in enumerate(stamps):
        e = uni["months"].get(datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m"))
        if not e:
            continue
        for s in e["symbols"]:
            j = col.get(s)
            if j is not None and not np.isnan(prices[i, j]):
                member[i, j] = True
    return prices, member


def market_return(prices, member):
    ret = np.zeros_like(prices)
    with np.errstate(invalid="ignore", divide="ignore"):
        ret[1:] = np.where(prices[:-1] > 0, prices[1:] / prices[:-1] - 1.0, 0.0)
    ret = np.nan_to_num(ret, nan=0.0, posinf=0.0, neginf=0.0)
    n = member.sum(axis=1)
    tot = (ret * member).sum(axis=1)
    return np.where(n > 0, tot / np.maximum(n, 1), 0.0)


def shuffled_panel(prices, rng):
    """Shuffle each asset's log returns independently."""
    out = np.full_like(prices, np.nan)
    for j in range(prices.shape[1]):
        col = prices[:, j]
        ok = np.where(~np.isnan(col))[0]
        if ok.size < 3:
            continue
        seg = col[ok[0]:ok[-1] + 1]
        good = ~np.isnan(seg)
        vals = seg[good]
        if vals.size < 3 or np.any(vals <= 0):
            continue
        lr = np.diff(np.log(vals))
        rng.shuffle(lr)
        rebuilt = vals[0] * np.exp(np.concatenate([[0.0], np.cumsum(lr)]))
        seg = seg.copy()
        seg[good] = rebuilt
        out[ok[0]:ok[-1] + 1, j] = seg
    return out


def sweep_stats(prices, member, variants, cost_bps, ppy, mkt=None, quiet=False):
    runner = CrossSectionalRunner(prices, member, cost_bps)
    if mkt is None:
        mkt = market_return(prices, member)
    mvar = float(mkt.var())
    g_sr, n_sr, turn, expo, tilt, beta, res, be = [], [], [], [], [], [], [], []
    for k, v in enumerate(variants):
        det = runner.run_detail(v)
        g, n = det["gross"], det["net"]
        if det["turnover_per_bar"] <= 0 and not np.any(g):
            continue
        g_sr.append(sharpe_of(g)); n_sr.append(sharpe_of(n))
        turn.append(det["turnover_per_bar"]); expo.append(det["exposure"])
        tilt.append(det["tilt"])
        b = float(np.cov(g, mkt, ddof=1)[0, 1] / mvar) if mvar > 0 else 0.0
        beta.append(b); res.append(sharpe_of(g - b * mkt))
        tpb = det["turnover_per_bar"]
        be.append(1e4 * float(g.mean()) / tpb if tpb > 0 else float("nan"))
        if not quiet:
            print("  %d/%d" % (k + 1, len(variants)), end="\r", flush=True)
    return {
        "gross_sr": annualise(np.array(g_sr), ppy),
        "net_sr": annualise(np.array(n_sr), ppy),
        "resid_sr": annualise(np.array(res), ppy),
        "turnover": np.array(turn), "exposure": np.array(expo),
        "tilt": np.array(tilt), "beta": np.array(beta), "breakeven": np.array(be),
    }


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sweep_dir")
    ap.add_argument("--null", type=int, default=10)
    a = ap.parse_args()
    d = a.sweep_dir.rstrip("/")

    prereg = json.load(open(os.path.join(d, "preregistration.frozen.json"), encoding="utf-8"))
    stored = json.load(open(os.path.join(d, "preregistration.sha256"), encoding="utf-8"))["preregistration_sha256"]
    if canonical_sha256(prereg) != stored:
        sys.exit("frozen pre-registration hash mismatch")

    proto = prereg["protocol"]
    cost = float(proto["costs_bps"]) + float(proto["slippage_bps"])
    ppy = int(prereg["planning"]["periods_per_year"])
    variants = enumerate_variants(prereg["search_space"])

    print("building panel ...", flush=True)
    prices, member = build_panel(prereg)
    print("  panel %d x %d" % prices.shape, flush=True)
    mkt = market_return(prices, member)

    real = sweep_stats(prices, member, variants, cost, ppy, mkt)
    print()
    g, n, rs = real["gross_sr"], real["net_sr"], real["resid_sr"]

    null = None
    if a.null > 0:
        print("  calibrating against %d independently shuffled panels" % a.null)
        rng = np.random.default_rng(20260731)
        means = []
        for i in range(a.null):
            fake = shuffled_panel(prices, rng)
            st = sweep_stats(fake, member, variants, cost, ppy, quiet=True)
            means.append(float(st["resid_sr"].mean()))
            print("    null %d/%d: %+.4f" % (i + 1, a.null, means[-1]), end="\r", flush=True)
        print()
        arr = np.array(means); sd = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
        obs = float(rs.mean())
        null = {"n_runs": a.null,
                "residual_sharpe_mean": round(float(arr.mean()), 4),
                "residual_sharpe_sd": round(sd, 4),
                "observed": round(obs, 4),
                "z_score": round((obs - float(arr.mean())) / sd, 3) if sd > 0 else None,
                "note": ("Each asset's returns were shuffled independently: same "
                         "per-asset distribution, no cross-sectional or serial "
                         "structure. A value inside this spread is an artefact of "
                         "the measurement, not a property of the market.")}

    mkt_expl = max(r_squared(real["tilt"], g), r_squared(real["beta"], g))
    pos = float((g > 0).mean())
    z = (null or {}).get("z_score")
    if abs(g.mean()) < 0.15 and 0.4 < pos < 0.6:
        mech = ("NO SIGNAL. Gross Sharpe is centred on zero — the ranking carries "
                "no predictive content before costs are charged.")
    elif g.mean() > 0.3 and n.mean() < 0:
        mech = ("SIGNAL DESTROYED BY COSTS. Gross returns are positive on average; "
                "rebalancing the basket costs more than the edge is worth.")
    elif g.mean() < -0.15:
        if null is not None and (z is None or abs(z) < 2.0):
            mech = ("ARTEFACT, NOT SIGNAL. Gross returns are negative, but panels "
                    "with no structure produce %+.2f residual Sharpe against an "
                    "observed %+.2f (z = %s). Claim nothing from it."
                    % (null["residual_sharpe_mean"], null["observed"], z))
        else:
            mech = ("SIGNAL WITH INVERTED SIGN. Gross returns stay negative after "
                    "removing market exposure (residual Sharpe %.2f). Still a "
                    "direction chosen after the fact; the opposite ranking must be "
                    "pre-registered separately." % rs.mean())
    else:
        mech = "MIXED. Gross returns are neither clearly zero nor clearly positive."

    fbe = real["breakeven"][np.isfinite(real["breakeven"])]
    out = {
        "sweep_id": prereg["sweep_id"],
        "preregistration_sha256": stored,
        "cost_bps_total": cost,
        "n_variants": int(g.size),
        "engine": "cross_sectional",
        "gross_sharpe_annual": {"mean": round(float(g.mean()), 4),
                                "median": round(float(np.median(g)), 4),
                                "p05": round(float(np.percentile(g, 5)), 4),
                                "p95": round(float(np.percentile(g, 95)), 4),
                                "max": round(float(g.max()), 4),
                                "share_positive": round(pos, 4)},
        "net_sharpe_annual": {"mean": round(float(n.mean()), 4),
                              "median": round(float(np.median(n)), 4),
                              "max": round(float(n.max()), 4),
                              "share_positive": round(float((n > 0).mean()), 4)},
        "turnover_per_bar": {"median": round(float(np.median(real["turnover"])), 6),
                             "p05": round(float(np.percentile(real["turnover"], 5)), 6),
                             "p95": round(float(np.percentile(real["turnover"], 95)), 6)},
        "mean_exposure": round(float(real["exposure"].mean()), 4),
        "directional_tilt": {"mean": round(float(real["tilt"].mean()), 4),
                             "median": round(float(np.median(real["tilt"])), 4),
                             "share_net_short": round(float((real["tilt"] < 0).mean()), 4)},
        "market_beta": {"mean": round(float(real["beta"].mean()), 4),
                        "median": round(float(np.median(real["beta"])), 4),
                        "note": "market = equal-weighted mean return of the investable universe"},
        "market_neutral_residual_sharpe_annual": {
            "mean": round(float(rs.mean()), 4),
            "median": round(float(np.median(rs)), 4),
            "share_positive": round(float((rs > 0).mean()), 4)},
        "variance_explained": {
            "net_sharpe_by_turnover": round(r_squared(real["turnover"], n), 4),
            "net_sharpe_by_gross_sharpe": round(r_squared(g, n), 4),
            "gross_sharpe_by_directional_tilt": round(r_squared(real["tilt"], g), 4),
            "gross_sharpe_by_market_beta": round(r_squared(real["beta"], g), 4)},
        "breakeven_cost_bps": {
            "best_variant": round(float(np.nanmax(fbe)), 3) if fbe.size else None,
            "median": round(float(np.nanmedian(fbe)), 3) if fbe.size else None,
            "note": ("per-variant round-trip cost at which mean gross return reaches "
                     "zero; the reported figure is the median OF those points, not "
                     "the breakeven of the median variant")},
        "mechanism": mech,
        "null_calibration": null,
    }
    p = os.path.join(d, "diagnostics.json")
    json.dump(out, open(p, "w", encoding="utf-8"), indent=2, sort_keys=True)

    print("\n%s — mechanism diagnosis (cross-sectional)\n" % out["sweep_id"])
    print("  gross Sharpe  mean %8.4f  median %8.4f  max %8.4f  positive %.1f%%"
          % (g.mean(), np.median(g), g.max(), 100 * pos))
    print("  net Sharpe    mean %8.4f  median %8.4f  max %8.4f  positive %.1f%%"
          % (n.mean(), np.median(n), n.max(), 100 * (n > 0).mean()))
    print("  residual (market-neutral) mean %8.4f  median %8.4f" % (rs.mean(), np.median(rs)))
    print("  mean exposure %.3f   mean tilt %+.4f   mean beta %+.4f"
          % (real["exposure"].mean(), real["tilt"].mean(), real["beta"].mean()))
    print("  median turnover/bar %.4f   median breakeven %.2f bps (charged %.1f)"
          % (np.median(real["turnover"]), np.nanmedian(fbe), cost))
    if null:
        print("\n  null residual Sharpe %+.4f  sd %.4f over %d runs"
              % (null["residual_sharpe_mean"], null["residual_sharpe_sd"], null["n_runs"]))
        print("  observed             %+.4f   z = %s" % (null["observed"], null["z_score"]))
    print("\n  %s" % mech)
    print("\n  wrote %s" % p)


if __name__ == "__main__":
    main()
