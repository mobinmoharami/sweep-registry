#!/usr/bin/env python3
"""Score a sweep against its frozen pre-registration.

    python finalize.py examples/SW-0001-crypto-mean-reversion

Expects one of these in the sweep directory:

    returns.npy   (T x N float array, written by run_sweep.py)
                  -> full analysis including PBO. Preferred.
    returns.csv   (same, as text — slower and far larger)
    sharpes.csv   (one per-observation Sharpe per line, one per variant)
                  -> DSR only. PBO impossible. Weaker evidence, and the
                     record will say so.

Refuses to run if the frozen pre-registration hash does not match.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import os
import sys

from srlab.canonical import canonical_bytes, canonical_sha256
from srlab.stats import (
    annualise,
    critical_sharpe,
    deflated_sharpe,
    expected_max_sharpe,
    kurtosis,
    min_detectable_sharpe,
    sharpe,
    skewness,
    variance,
)

try:
    import numpy as np
except ImportError:
    np = None


def fail(msg: str) -> None:
    print(f"ABORT: {msg}", file=sys.stderr)
    sys.exit(1)


def load_matrix(path: str):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for i, row in enumerate(reader):
            if not row:
                continue
            try:
                rows.append([float(x) for x in row])
            except ValueError:
                if i == 0:
                    continue  # header
                raise
    if not rows:
        fail(f"{path} is empty")
    width = len(rows[0])
    if any(len(r) != width for r in rows):
        fail(f"{path} has ragged rows")
    return rows


def percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return sorted_vals[int(k)]
    return sorted_vals[lo] * (hi - k) + sorted_vals[hi] * (k - lo)


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    d = sys.argv[1].rstrip("/")
    frozen_path = os.path.join(d, "preregistration.frozen.json")
    hash_path = os.path.join(d, "preregistration.sha256")

    if not os.path.exists(frozen_path):
        fail("no frozen pre-registration — run register.py first")

    with open(frozen_path, encoding="utf-8") as fh:
        prereg = json.load(fh)
    with open(hash_path, encoding="utf-8") as fh:
        stored = json.load(fh)["preregistration_sha256"]

    recomputed = canonical_sha256(prereg)
    if recomputed != stored:
        fail(
            "PRE-REGISTRATION HASH MISMATCH.\n"
            f"  stored     : {stored}\n"
            f"  recomputed : {recomputed}\n"
            "  The frozen document was modified. This sweep cannot be published."
        )

    plan = prereg["planning"]
    ppy = int(plan["periods_per_year"])
    alpha = float(prereg["decision_rule"]["alpha"])
    threshold = float(prereg["decision_rule"]["threshold"])
    power = float(plan["power"])
    declared_trials = int(prereg["search_space"]["n_trials"])

    npy_path = os.path.join(d, "returns.npy")
    returns_path = os.path.join(d, "returns.csv")
    sharpes_path = os.path.join(d, "sharpes.csv")

    pbo_result = None
    integrity = []

    # ---- load ------------------------------------------------------
    if os.path.exists(npy_path) or os.path.exists(returns_path):
        if np is None:
            fail("numpy is required to score a returns matrix — pip install numpy")

        if os.path.exists(npy_path):
            matrix = np.load(npy_path, mmap_mode="r")   # never fully resident
        else:
            matrix = np.asarray(load_matrix(returns_path), dtype=np.float32).T

        # variants that never traded were recorded at sweep time; excluding
        # them keeps the multiple-testing penalty honest
        active_path = os.path.join(d, "active_variants.json")
        if os.path.exists(active_path):
            with open(active_path, encoding="utf-8") as fh:
                cols = np.asarray(json.load(fh)["active"], dtype=np.int64)
        else:
            cols = np.arange(matrix.shape[0], dtype=np.int64)

        # stored as (variant, observation)
        t_obs = matrix.shape[1]
        n_trials = int(cols.size)

        # per-column Sharpe in column chunks — looping in Python over thousands
        # of columns takes hours, and casting the whole matrix to float64 at
        # once doubles peak memory for no benefit
        sr_arr = np.empty(n_trials, dtype=np.float64)
        CHUNK = 256
        for lo in range(0, n_trials, CHUNK):
            hi = min(lo + CHUNK, n_trials)
            block = np.asarray(matrix[cols[lo:hi], :], dtype=np.float64)
            mean = block.mean(axis=1)
            sd = block.std(axis=1, ddof=1)
            sr = np.divide(mean, sd, out=np.zeros_like(mean), where=sd > 0)
            sr_arr[lo:hi] = np.nan_to_num(sr, nan=0.0, posinf=0.0, neginf=0.0)
        trial_sharpes = sr_arr.tolist()

        best_idx = int(np.argmax(sr_arr))
        best = np.asarray(matrix[int(cols[best_idx]), :], dtype=np.float64)
        dev = best - best.mean()
        m2 = float((dev ** 2).mean())
        skew = float((dev ** 3).mean() / m2 ** 1.5) if m2 > 0 else 0.0
        kurt = float((dev ** 4).mean() / m2 ** 2) if m2 > 0 else 3.0
        evidence = "returns_matrix"

        try:
            from srlab.pbo import cscv_pbo

            pbo_result = cscv_pbo(
                matrix, n_splits=int(plan.get("cscv_splits", 16)), columns=cols
            )
        except Exception as exc:  # noqa: BLE001
            integrity.append(f"PBO could not be computed: {exc}")

    elif os.path.exists(sharpes_path):
        rows = load_matrix(sharpes_path)
        trial_sharpes = [r[0] for r in rows]
        n_trials = len(trial_sharpes)
        t_obs = int(plan["n_observations"])
        best_idx = max(range(n_trials), key=lambda i: trial_sharpes[i])
        skew = float(plan.get("assumed_skewness", 0.0))
        kurt = float(plan.get("assumed_kurtosis", 3.0))
        evidence = "sharpes_only"
        integrity.append(
            "Only per-trial Sharpes supplied. Skew/kurtosis are the planning "
            "assumptions, not measured, and PBO is impossible. Weaker evidence."
        )
    else:
        fail("need returns.npy, returns.csv or sharpes.csv in the sweep directory")

    if n_trials != declared_trials:
        integrity.append(
            f"Trial count differs from pre-registration: declared "
            f"{declared_trials:,}, supplied {n_trials:,}. Explain this in the record."
        )

    # ---- statistics ------------------------------------------------
    sr_best = trial_sharpes[best_idx]
    var_sr = variance(trial_sharpes)

    # A matrix of all zeros scores as DSR exactly 0.5 and prints "NO EDGE
    # FOUND", which is indistinguishable from a real null result. That is the
    # worst output this registry can produce: a record that looks like a
    # finding and is actually a crashed run. Refuse it.
    if var_sr <= 0 or all(s == 0 for s in trial_sharpes):
        fail(
            "every variant has Sharpe exactly zero — nothing traded.\n"
            "  This is a broken run, not a null result, and it must not be\n"
            "  scored. Check that run_sweep/run_xs_sweep completed: the\n"
            "  active_variants.json file should exist alongside returns.npy."
        )
    sr_null = expected_max_sharpe(n_trials, var_sr)

    try:
        dsr = deflated_sharpe(sr_best, sr_null, t_obs, skew, kurt)
        crit = critical_sharpe(sr_null, t_obs, skew, kurt, alpha)
    except ValueError as exc:
        fail(str(exc))

    mds = min_detectable_sharpe(n_trials, var_sr, t_obs, skew, kurt, alpha, power)
    metric = prereg["decision_rule"].get("metric", "deflated_sharpe_ratio")
    passed = dsr >= threshold
    cross_sectional = None

    if metric == "cross_sectional_residual_sharpe_z":
        diag_path = os.path.join(d, "diagnostics.json")
        if not os.path.exists(diag_path):
            fail(
                "this sweep pre-registered the cross-sectional test, so it must "
                f"be scored from diagnostics:\n  python diagnose.py {d} --null "
                f"{int(plan.get('null_runs', 10))}"
            )
        with open(diag_path, encoding="utf-8") as fh:
            diag = json.load(fh)
        if diag.get("preregistration_sha256") != stored:
            fail("diagnostics.json was produced from a different pre-registration")
        nullc = diag.get("null_calibration")
        if not nullc or nullc.get("z_score") is None:
            fail("diagnostics.json has no null calibration — rerun with --null")
        if int(nullc["n_runs"]) < int(plan.get("null_runs", 5)):
            fail(f"null calibration used {nullc['n_runs']} runs, "
                 f"pre-registration requires {plan.get('null_runs')}")

        z = float(nullc["z_score"])
        passed = abs(z) >= threshold
        cross_sectional = {
            "observed_mean_residual_sharpe": nullc["observed"],
            "null_mean": nullc["residual_sharpe_mean"],
            "null_sd": nullc["residual_sharpe_sd"],
            "null_runs": nullc["n_runs"],
            "z_score": z,
            "z_threshold": threshold,
            "direction": "positive" if nullc["observed"] > nullc["residual_sharpe_mean"]
                         else "negative",
        }

    ordered = sorted(trial_sharpes)
    distribution = {
        "min": round(annualise(ordered[0], ppy), 4),
        "p05": round(annualise(percentile(ordered, 0.05), ppy), 4),
        "p25": round(annualise(percentile(ordered, 0.25), ppy), 4),
        "median": round(annualise(percentile(ordered, 0.50), ppy), 4),
        "p75": round(annualise(percentile(ordered, 0.75), ppy), 4),
        "p95": round(annualise(percentile(ordered, 0.95), ppy), 4),
        "max": round(annualise(ordered[-1], ppy), 4),
        "share_positive": round(
            sum(1 for s in trial_sharpes if s > 0) / n_trials, 4
        ),
    }

    result = {
        "sweep_id": prereg["sweep_id"],
        "preregistration_sha256": stored,
        "finalised_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "evidence_type": evidence,
        "n_trials": n_trials,
        "n_observations": t_obs,
        "best_sharpe_annual": round(annualise(sr_best, ppy), 4),
        "expected_max_sharpe_under_null_annual": round(annualise(sr_null, ppy), 4),
        "critical_sharpe_annual": round(annualise(crit, ppy), 4),
        "min_detectable_sharpe_annual": round(annualise(mds, ppy), 4),
        "deflated_sharpe_ratio": round(dsr, 6),
        "threshold": threshold,
        "primary_metric": metric,
        "cross_sectional_test": cross_sectional,
        "verdict": (
            ("EFFECT DETECTED" if passed else "NO EFFECT DETECTED")
            if cross_sectional else
            ("EDGE CLEARED THRESHOLD" if passed else "NO EDGE FOUND")
        ),
        "measured_skewness": round(skew, 6),
        "measured_kurtosis": round(kurt, 6),
        "distribution_annualised": distribution,
        "pbo": pbo_result,
        "integrity_notes": integrity,
    }
    result["result_sha256"] = canonical_sha256(result)

    with open(os.path.join(d, "result.json"), "wb") as fh:
        fh.write(canonical_bytes(result))

    write_record(d, prereg, result)

    print(f"{result['sweep_id']}: {result['verdict']}")
    print(f"  best Sharpe (annual)  : {result['best_sharpe_annual']}")
    print(f"  E[max | null]         : {result['expected_max_sharpe_under_null_annual']}")
    print(f"  needed to clear       : {result['critical_sharpe_annual']}")
    print(f"  detection limit       : {result['min_detectable_sharpe_annual']}")
    print(f"  DSR                   : {result['deflated_sharpe_ratio']}")
    if pbo_result:
        print(f"  PBO                   : {pbo_result['pbo']:.4f}")
    for note in integrity:
        print(f"  ! {note}")
    print(f"\n  wrote {d}/result.json and {d}/RECORD.md")


def write_record(d: str, prereg: dict, r: dict) -> None:
    dist = r["distribution_annualised"]
    pbo = r["pbo"]
    lines = [
        f"# {prereg['sweep_id']} — {prereg['title']}",
        "",
        f"**Verdict: {r['verdict']}**",
        "",
        prereg["hypothesis"],
        "",
        "## What was searched",
        "",
        f"- Families: {', '.join(prereg['search_space']['families'])}",
        f"- Variants tested: {r['n_trials']:,}",
        f"- Symbols: {', '.join(prereg['data']['symbols'])}",
        f"- Period: {prereg['data']['start']} to {prereg['data']['end']} "
        f"({prereg['data']['timeframe']}, {r['n_observations']:,} observations)",
        f"- Costs: {prereg['protocol']['costs_bps']} bps, "
        f"slippage {prereg['protocol']['slippage_bps']} bps",
        f"- Protocol: {prereg['protocol']['method']}",
        f"- Holdout: {prereg['data']['holdout']}",
        "",
        "## Result",
        "",
        "| | annualised Sharpe |",
        "|---|---|",
        f"| Best variant found | {r['best_sharpe_annual']} |",
        f"| Expected best if nothing works | {r['expected_max_sharpe_under_null_annual']} |",
        f"| Needed to clear threshold | {r['critical_sharpe_annual']} |",
        f"| **Detection limit** | **{r['min_detectable_sharpe_annual']}** |",
        "",
        f"Deflated Sharpe Ratio: **{r['deflated_sharpe_ratio']}** "
        f"(threshold {r['threshold']})",
        "",
    ]

    cs = r.get("cross_sectional_test")
    if cs:
        lines += [
            "## Pre-registered test: cross-sectional residual Sharpe",
            "",
            "The registered hypothesis concerns the whole population of variants, "
            "not the best one. Pooling across variants detects far smaller effects "
            "than a maximum ever could — but says nothing about any single rule.",
            "",
            f"- Observed mean market-neutral gross Sharpe: **{cs['observed_mean_residual_sharpe']}**",
            f"- Shuffled null: {cs['null_mean']} ± {cs['null_sd']} "
            f"over {cs['null_runs']} runs",
            f"- **z = {cs['z_score']}** (threshold {cs['z_threshold']}), "
            f"direction {cs['direction']}",
            "",
        ]

    if pbo:
        lines += [
            f"Probability of Backtest Overfitting: **{pbo['pbo']:.4f}** "
            f"({pbo['n_combinations']:,} CSCV splits)",
            "",
        ]

    lines += [
        "## Distribution across all variants",
        "",
        "Publishing only the best result is how noise gets sold as skill. "
        "The whole distribution:",
        "",
        "| min | p05 | p25 | median | p75 | p95 | max |",
        "|---|---|---|---|---|---|---|",
        f"| {dist['min']} | {dist['p05']} | {dist['p25']} | {dist['median']} "
        f"| {dist['p75']} | {dist['p95']} | {dist['max']} |",
        "",
        f"Share of variants with positive Sharpe: {dist['share_positive']:.1%}",
        "",
        "## How to read this",
        "",
        f"This sweep could have detected a true annualised Sharpe of "
        f"**{r['min_detectable_sharpe_annual']}** or larger with "
        f"{int(float(prereg['planning']['power']) * 100)}% power. "
        "It says nothing about smaller edges, and nothing about strategy "
        "families outside the search space above.",
        "",
        "## Integrity",
        "",
        f"- Pre-registration sha256: `{r['preregistration_sha256']}`",
        f"- Result sha256: `{r['result_sha256']}`",
        f"- Finalised: {r['finalised_utc']}",
        f"- Evidence: {r['evidence_type']}",
    ]
    for note in r["integrity_notes"]:
        lines.append(f"- NOTE: {note}")
    lines.append("")

    with open(os.path.join(d, "RECORD.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    main()
