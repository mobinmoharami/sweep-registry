#!/usr/bin/env python3
"""
Regenerates every number, table and figure in the paper directly from the
registry on disk. Nothing is hard-coded: if a sweep is added, voided or
re-scored, re-running this script updates the paper inputs.

Usage:
    cd /opt/sweep-registry
    python3 paper/analysis.py [--sweeps sweeps] [--out paper/build]

Outputs into --out:
    stats.txt     every figure quoted in the paper, with its label
    tableA1.tex   all scored sweeps
    tableA2.tex   variant distributions
    tableA3.tex   cost sensitivity
    fig1.pdf      distribution of variant Sharpe ratios by sweep
"""
import argparse
import glob
import json
import math
import os
import statistics as st

# ----------------------------------------------------------------- loading

def load(sweeps_dir):
    """Return (scored, voided, unrun). A sweep is scored iff it has a result
    and is not annotated void."""
    scored, voided, unrun = [], [], []
    for d in sorted(glob.glob(os.path.join(sweeps_dir, "SW-*"))):
        pre_p = os.path.join(d, "preregistration.json")
        if not os.path.exists(pre_p):
            continue
        pre = json.load(open(pre_p, encoding="utf-8"))
        sid = os.path.basename(d)

        ann = {}
        ann_p = os.path.join(d, "annotations.json")
        if os.path.exists(ann_p):
            try:
                ann = json.load(open(ann_p, encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        void = str(ann.get("void") or ann.get("status") or "").upper() == "VOID"

        res_p = os.path.join(d, "result.json")
        if not os.path.exists(res_p):
            (voided if void else unrun).append({"id": sid, "pre": pre, "ann": ann})
            continue
        res = json.load(open(res_p, encoding="utf-8"))

        diag = None
        diag_p = os.path.join(d, "diagnostics.json")
        if os.path.exists(diag_p):
            diag = json.load(open(diag_p, encoding="utf-8"))

        rec = {"id": sid, "pre": pre, "res": res, "diag": diag, "ann": ann}
        (voided if void else scored).append(rec)
    return scored, voided, unrun


def market_of(pre):
    syms = pre.get("data", {}).get("symbols") or []
    text = " ".join(syms)
    if "point-in-time" in text:
        return "XS crypto"
    if any(s.endswith("USDT") for s in syms):
        return "BTC/ETH"
    return "FX"


def family_of(pre):
    """Derive the family label from the pre-registration title, which is of
    the form '<Family> on <market>, <timeframe>'."""
    t = pre.get("title", "")
    fam = t.split(" on ")[0].split(" across ")[0].strip()
    return fam[0].upper() + fam[1:] if fam else "unknown"


def pbo_of(res):
    """pbo is stored as a nested object; older records may store a float."""
    p = res.get("pbo")
    if isinstance(p, dict):
        return p.get("pbo")
    return p


# ------------------------------------------------------------- statistics

def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    out = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def binom_two_sided(k, n, p=0.5):
    """Two-sided sign test. k is the count on the more extreme side."""
    k = max(k, n - k)
    tail = sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))
    return min(1.0, 2 * tail)


# ------------------------------------------------------------------ tables

def fmt(x, n=3):
    if x is None:
        return "---"
    return ("%." + str(n) + "f") % x


def table_a1(scored, out):
    lines = []
    abbrev = {
        "Short-horizon mean reversion": "Mean reversion",
        "Moving average crossover": "MA crossover",
        "Donchian channel breakout": "Donchian breakout",
        "ATR volatility breakout": "ATR breakout",
        "Time-series momentum": "TS momentum",
        "Volatility-filtered momentum": "Vol-filtered mom.",
        "Hour-of-day seasonality": "Hour-of-day",
        "Volume-confirmed price signals": "Volume-confirmed",
        "Cross-sectional momentum": "XS momentum",
        "Cross-sectional reversal": "XS reversal",
        "Volatility-scaled cross-sectional momentum": "XS vol-scaled mom.",
    }
    for r in scored:
        res, pre = r["res"], r["pre"]
        fam = family_of(pre)
        fam = abbrev.get(fam, fam)
        decl = int(pre["search_space"]["n_trials"])
        lines.append(" & ".join([
            r["id"], fam, market_of(pre),
            f"{decl:,}", f"{res['n_trials']:,}",
            fmt(res.get("best_sharpe_annual")),
            fmt(res.get("expected_max_sharpe_under_null_annual")),
            fmt(res.get("deflated_sharpe_ratio")),
            fmt(res.get("min_detectable_sharpe_annual"), 2),
            fmt(pbo_of(res)),
        ]) + r" \\")
    open(os.path.join(out, "tableA1.tex"), "w").write("\n".join(lines))


def table_a2(scored, out):
    lines = []
    for r in scored:
        d = r["res"].get("distribution_annualised", {})
        cells = [fmt(d.get(k), 2) for k in
                 ("min", "p05", "p25", "median", "p75", "p95", "max")]
        sp = d.get("share_positive")
        cells.append((fmt(sp * 100, 1) + r"\%") if sp is not None else "---")
        lines.append(" & ".join([r["id"]] + cells) + r" \\")
    open(os.path.join(out, "tableA2.tex"), "w").write("\n".join(lines))


def table_a3(scored, out):
    """Sharpe is linear in per-unit cost, so the measured gross and net points
    determine the whole curve."""
    lines = []
    for r in scored:
        d = r["diag"]
        if not d:
            continue
        charged = float(d["cost_bps_total"])
        g = d["gross_sharpe_annual"]["median"]
        n = d["net_sharpe_annual"]["median"]
        be = d["breakeven_cost_bps"]["median"]
        slope = (g - n) / charged
        vals = [g - slope * c for c in (0, 2, 6, 10, 20)]
        lines.append(" & ".join([r["id"]] + [fmt(v) for v in vals]
                                + [fmt(be, 2)]) + r" \\")
    open(os.path.join(out, "tableA3.tex"), "w").write("\n".join(lines))


# ------------------------------------------------------------------ figure

def figure(scored, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    rows = [r for r in scored if r["res"].get("distribution_annualised")]
    rows.sort(key=lambda r: r["res"]["distribution_annualised"]["median"])
    lo = min(r["res"]["distribution_annualised"]["p05"] for r in rows)
    hi = max(r["res"]["expected_max_sharpe_under_null_annual"] for r in rows)
    pad = 0.06 * (hi - lo)

    fig, ax = plt.subplots(figsize=(7.2, 7.4))
    for i, r in enumerate(rows):
        d = r["res"]["distribution_annualised"]
        emax = r["res"]["expected_max_sharpe_under_null_annual"]
        ax.plot([d["p05"], d["p95"]], [i, i], color="#9a9a9a", lw=0.9, zorder=1)
        ax.plot([d["p25"], d["p75"]], [i, i], color="#2b2b2b", lw=4.0,
                solid_capstyle="butt", zorder=2)
        ax.plot([d["median"]], [i], marker="o", mfc="white", mec="#2b2b2b",
                ms=3.0, mew=0.8, zorder=3)
        ax.plot([d["max"]], [i], marker="D", color="#c0392b", ms=3.6, zorder=4)
        ax.plot([emax], [i], marker="o", mfc="none", mec="#1f5fa8",
                ms=5.6, mew=1.2, zorder=5)
    ax.axvline(0, color="#444444", lw=0.7, ls=(0, (4, 3)), zorder=0)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{r['id'][3:]}  {family_of(r['pre'])}" for r in rows],
                       fontsize=7.0)
    ax.set_ylim(-1.0, len(rows) - 0.2)
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_xlabel("Annualised Sharpe ratio", fontsize=9)
    ax.tick_params(axis="x", labelsize=8)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.grid(axis="x", color="#dddddd", lw=0.5)
    ax.set_axisbelow(True)
    leg = [
        Line2D([], [], color="#2b2b2b", lw=4.0, label="interquartile range"),
        Line2D([], [], color="#9a9a9a", lw=0.9, label="5th to 95th percentile"),
        Line2D([], [], color="#2b2b2b", marker="o", mfc="white", ls="", ms=3.0,
               label="median"),
        Line2D([], [], color="#c0392b", marker="D", ls="", ms=3.6,
               label="best variant"),
        Line2D([], [], color="#1f5fa8", marker="o", mfc="none", ls="", ms=5.6,
               label=r"$E[\max SR]$ under the null"),
    ]
    ax.legend(handles=leg, fontsize=7.4, loc="upper center",
              bbox_to_anchor=(0.5, -0.075), frameon=False, ncol=3,
              handletextpad=0.5, columnspacing=1.6)
    plt.tight_layout()
    plt.savefig(os.path.join(out, "fig1.pdf"), bbox_inches="tight")
    plt.close()


# ------------------------------------------------------------------- stats

def stats(scored, voided, unrun, out):
    L = []
    def p(label, value):
        L.append(f"{label:<52} {value}")

    res = [r["res"] for r in scored]
    decl = [int(r["pre"]["search_space"]["n_trials"]) for r in scored]
    best = [x["best_sharpe_annual"] for x in res]
    emax = [x["expected_max_sharpe_under_null_annual"] for x in res]
    dsr = [x["deflated_sharpe_ratio"] for x in res]
    mds = [x["min_detectable_sharpe_annual"] for x in res]
    kurt = [x["measured_kurtosis"] for x in res]
    skew = [x["measured_skewness"] for x in res]
    pbo = [pbo_of(x) for x in res]

    L.append("=== SCOPE ===")
    p("records in registry", len(scored) + len(voided) + len(unrun))
    p("scored", len(scored))
    p("voided", len(voided))
    p("sealed, not yet run", len(unrun))
    p("variants enumerated (declared)", f"{sum(decl):,}")
    p("variants scored (traded at least once)", f"{sum(x['n_trials'] for x in res):,}")
    p("families with a scored sweep",
      len({family_of(r["pre"]) for r in scored}))
    for m in ("BTC/ETH", "XS crypto", "FX"):
        sel = [r for r in scored if market_of(r["pre"]) == m]
        if sel:
            p(f"  {m}: sweeps / declared variants",
              f"{len(sel)} / {sum(int(r['pre']['search_space']['n_trials']) for r in sel):,}")
    crypto = [r for r in scored if market_of(r["pre"]) != "FX"]
    p("crypto total: sweeps / declared",
      f"{len(crypto)} / {sum(int(r['pre']['search_space']['n_trials']) for r in crypto):,}")

    L.append("")
    L.append("=== HEADLINE ===")
    p("threshold", res[0]["threshold"])
    p("sweeps clearing threshold", sum(1 for d in dsr if d >= res[0]["threshold"]))
    p("max DSR", f"{max(dsr):.6f} ({scored[dsr.index(max(dsr))]['id']})")
    p("median minimum detectable Sharpe", f"{st.median(mds):.4f}")
    p("min / max detectable Sharpe", f"{min(mds):.2f} / {max(mds):.2f}")

    L.append("")
    L.append("=== JOINT TEST ===")
    k = sum(1 for b, e in zip(best, emax) if b < e)
    p("best variant below E[maxSR]", f"{k} of {len(scored)}")
    p("two-sided sign test p", f"{binom_two_sided(k, len(scored)):.3e}")
    p("median best / E[maxSR] ratio",
      f"{st.median([b / e for b, e in zip(best, emax)]):.3f}")

    L.append("")
    L.append("=== COST SENSITIVITY ===")
    withd = [r for r in scored if r["diag"]]
    p("sweeps with a cost decomposition", f"{len(withd)} of {len(scored)}")
    p("missing", ", ".join(r["id"] for r in scored if not r["diag"]) or "none")
    gneg = [r for r in withd if r["diag"]["gross_sharpe_annual"]["median"] < 0]
    p("median gross Sharpe below zero", f"{len(gneg)} of {len(withd)}")
    bes = {r["id"]: r["diag"]["breakeven_cost_bps"]["median"] for r in withd}
    p("median breakeven cost (bps)", f"{st.median(list(bes.values())):.2f}")
    above = [i for i, r in zip(bes, withd)
             if bes[i] > float(r["diag"]["cost_bps_total"])]
    p("breakeven above the cost charged", ", ".join(above) or "none")
    worst = min(bes, key=bes.get)
    p("most negative breakeven", f"{worst} at {bes[worst]:.2f} bps")

    L.append("")
    L.append("=== POWER CALIBRATION ===")
    ak = {float(r["pre"]["planning"]["assumed_kurtosis"]) for r in scored}
    asw = {float(r["pre"]["planning"]["assumed_skewness"]) for r in scored}
    p("assumed kurtosis (distinct values)", sorted(ak))
    p("assumed skewness (distinct values)", sorted(asw))
    p("measured kurtosis median / min / max",
      f"{st.median(kurt):.1f} / {min(kurt):.1f} / {max(kurt):.1f}")
    p("measured skewness median / max", f"{st.median(skew):.2f} / {max(skew):.1f}")
    facs = [k_ / float(r["pre"]["planning"]["assumed_kurtosis"])
            for k_, r in zip(kurt, scored)]
    p("underestimation factor median / max",
      f"{st.median(facs):.1f}x / {max(facs):.0f}x")
    p("sweeps where measured kurtosis exceeded assumed",
      f"{sum(1 for f_ in facs if f_ > 1)} of {len(facs)}")

    L.append("")
    L.append("=== DSR DRIVERS ===")
    p("spearman(kurtosis, DSR)", f"{spearman(kurt, dsr):+.3f}")
    p("spearman(best Sharpe, DSR)", f"{spearman(best, dsr):+.3f}")
    p("spearman(kurtosis, E[maxSR])", f"{spearman(kurt, emax):+.3f}")
    exp_pairs = [(r["diag"]["mean_exposure"], r["res"]["measured_kurtosis"])
                 for r in scored if r["diag"]]
    p("spearman(mean exposure, kurtosis)",
      f"{spearman([a for a, _ in exp_pairs], [b for _, b in exp_pairs]):+.3f}"
      f"   (n={len(exp_pairs)})")
    for name, sel in (("kurtosis < 200", [i for i, k_ in enumerate(kurt) if k_ < 200]),
                      ("kurtosis >= 200", [i for i, k_ in enumerate(kurt) if k_ >= 200])):
        p(f"  {name}: n / med DSR / med E[max] / med best",
          f"{len(sel)} / {st.median([dsr[i] for i in sel]):.4f}"
          f" / {st.median([emax[i] for i in sel]):.2f}"
          f" / {st.median([best[i] for i in sel]):.3f}")

    L.append("")
    L.append("=== PBO ===")
    good = [x for x in pbo if x is not None]
    p("median PBO", f"{st.median(good):.3f}")
    hi_pbo = sorted(zip([r["id"] for r in scored], pbo),
                    key=lambda t: -(t[1] or 0))[:3]
    p("highest PBO", ", ".join(f"{i} {v:.3f}" for i, v in hi_pbo))

    L.append("")
    L.append("=== INTEGRITY ===")
    short = [(r["id"], int(r["pre"]["search_space"]["n_trials"]), r["res"]["n_trials"])
             for r in scored
             if r["res"]["n_trials"] != int(r["pre"]["search_space"]["n_trials"])]
    p("sweeps with fewer scored than declared", len(short))
    for sid, d_, s_ in short:
        p(f"  {sid}", f"declared {d_}, scored {s_}, shortfall {d_ - s_}")
    p("total shortfall", sum(d_ - s_ for _, d_, s_ in short))
    p("max DSR among those sweeps",
      f"{max(r['res']['deflated_sharpe_ratio'] for r in scored if r['id'] in {x[0] for x in short}):.6f}")
    nmis = [(r["id"], r["pre"]["planning"]["n_observations"], r["res"]["n_observations"])
            for r in scored
            if r["pre"]["planning"]["n_observations"] != r["res"]["n_observations"]]
    p("sweeps with observation-count drift", len(nmis))
    for sid, a, b in nmis:
        p(f"  {sid}", f"planned {a:,}, realised {b:,}")
    p("voided records", ", ".join(r["id"] for r in voided) or "none")
    p("sealed, not yet run", ", ".join(r["id"] for r in unrun) or "none")

    text = "\n".join(L)
    open(os.path.join(out, "stats.txt"), "w").write(text + "\n")
    print(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweeps", default="sweeps")
    ap.add_argument("--out", default="paper/build")
    ap.add_argument("--no-figure", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    scored, voided, unrun = load(a.sweeps)
    if not scored:
        raise SystemExit(f"no scored sweeps found under {a.sweeps!r}")

    table_a1(scored, a.out)
    table_a2(scored, a.out)
    table_a3(scored, a.out)
    if not a.no_figure:
        try:
            figure(scored, a.out)
        except ImportError:
            print("[warn] matplotlib unavailable; figure skipped")
    stats(scored, voided, unrun, a.out)
    print(f"\nwritten to {a.out}/")


if __name__ == "__main__":
    main()
