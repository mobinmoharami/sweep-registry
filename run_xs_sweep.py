#!/usr/bin/env python3
"""Run a cross-sectional sweep from its frozen pre-registration.

    python run_xs_sweep.py sweeps/SW-0029

Needs a universe file built by data/build_universe.py, named in the
pre-registration as data.universe. Assembles the price panel, marks which
assets were investable in which month, and runs every enumerated variant.

Writes returns.npy in the same (variant, observation) layout as the
time-series runner, so finalize.py and diagnose.py read it unchanged.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np

from srlab.canonical import canonical_sha256
from sweep.cross_sectional import SCORERS, CrossSectionalRunner
from sweep.engine import enumerate_variants

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def fail(msg: str) -> None:
    print(f"ABORT: {msg}", file=sys.stderr)
    sys.exit(1)


def load_series(symbol: str, timeframe: str) -> dict:
    path = os.path.join(DATA, f"{symbol}_{timeframe}.csv")
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        for row in reader:
            if row and row[0].isdigit():
                out[int(row[0])] = float(row[4])
    return out


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    if "--i-know-what-im-doing" in sys.argv:
        sys.argv.remove("--i-know-what-im-doing")
        os.environ["SWEEP_OVERRIDE_EMBARGO"] = "1"

    d = sys.argv[1].rstrip("/")
    frozen = os.path.join(d, "preregistration.frozen.json")
    out_path = os.path.join(d, "returns.npy")

    if not os.path.exists(frozen):
        fail("no frozen pre-registration — run register.py first")
    if os.path.exists(out_path):
        fail(f"{out_path} exists. Delete it deliberately if you mean to rerun.")

    with open(frozen, encoding="utf-8") as fh:
        prereg = json.load(fh)
    with open(os.path.join(d, "preregistration.sha256"), encoding="utf-8") as fh:
        stored = json.load(fh)["preregistration_sha256"]
    if canonical_sha256(prereg) != stored:
        fail("frozen pre-registration hash mismatch — this sweep is void")

    # A sweep may be frozen now and executed years later. Running a holdout
    # early is how a single-use test gets wasted.
    earliest = prereg.get("planning", {}).get("earliest_run_date")
    if earliest and not os.environ.get("SWEEP_OVERRIDE_EMBARGO"):
        import datetime as _dt
        today, due = _dt.date.today(), _dt.date.fromisoformat(earliest)
        if today < due:
            fail(f"embargoed until {earliest} (today is {today}, "
                 f"{(due - today).days} days to go).\n"
                 "  Frozen early on purpose; it can only be run once.\n"
                 "  Override with --i-know-what-im-doing, and record why.")

    data = prereg["data"]
    proto = prereg["protocol"]
    cost_bps = float(proto["costs_bps"]) + float(proto["slippage_bps"])

    uni_name = data.get("universe")
    if not uni_name:
        fail("data.universe is required for a cross-sectional sweep")
    uni_path = os.path.join(DATA, "universe", f"{uni_name}.json")
    if not os.path.exists(uni_path):
        fail(f"{uni_path} not found — build it with data/build_universe.py")
    with open(uni_path, encoding="utf-8") as fh:
        universe = json.load(fh)

    variants = enumerate_variants(prereg["search_space"])
    unknown = [v["family"] for v in variants if v["family"] not in SCORERS]
    if unknown:
        fail(f"unknown cross-sectional families: {sorted(set(unknown))}. "
             f"Known: {sorted(SCORERS)}")

    symbols = universe["all_symbols_ever"]
    tf = data["timeframe"]
    print(f"{prereg['sweep_id']} — {prereg['title']}")
    print(f"  universe: {uni_name} — {len(symbols)} symbols ever, "
          f"{len(universe['months'])} months")

    # ---- load every symbol that ever appeared ----------------------
    series = {}
    missing = []
    for s in symbols:
        ser = load_series(s, tf)
        if ser:
            series[s] = ser
        else:
            missing.append(s)
    if missing:
        print(f"  ! {len(missing)} symbols have no local data and are excluded:")
        print(f"    {', '.join(missing[:12])}{' ...' if len(missing) > 12 else ''}")
        print("    Excluding a symbol that WAS in the universe reintroduces "
              "survivorship bias — download them before trusting the result.")
    if len(series) < 5:
        fail("fewer than 5 symbols have data — nothing to rank")

    lo = int(datetime.fromisoformat(data["start"]).replace(
        tzinfo=timezone.utc).timestamp() * 1000)
    hi = int(datetime.fromisoformat(data["end"]).replace(
        tzinfo=timezone.utc).timestamp() * 1000)

    stamps = sorted({t for ser in series.values() for t in ser
                     if lo <= t <= hi})
    if len(stamps) < 500:
        fail(f"only {len(stamps)} timestamps in range")

    active = sorted(series)
    idx = {t: i for i, t in enumerate(stamps)}
    prices = np.full((len(stamps), len(active)), np.nan)
    for j, s in enumerate(active):
        for t, p in series[s].items():
            i = idx.get(t)
            if i is not None:
                prices[i, j] = p

    # ---- membership: which asset was investable when ---------------
    membership = np.zeros(prices.shape, dtype=bool)
    col = {s: j for j, s in enumerate(active)}
    for i, t in enumerate(stamps):
        month = datetime.fromtimestamp(t / 1000, timezone.utc).strftime("%Y-%m")
        entry = universe["months"].get(month)
        if not entry:
            continue
        for s in entry["symbols"]:
            j = col.get(s)
            if j is not None and not np.isnan(prices[i, j]):
                membership[i, j] = True

    per_bar = membership.sum(axis=1)
    print(f"  panel: {len(stamps):,} bars x {len(active)} symbols")
    print(f"  investable per bar: median {int(np.median(per_bar))}, "
          f"min {int(per_bar.min())}, max {int(per_bar.max())}")

    if np.median(per_bar) < 5:
        fail("median investable universe below 5 — download more symbols")

    # ---- run --------------------------------------------------------
    runner = CrossSectionalRunner(prices, membership, cost_bps)
    total = len(variants)
    matrix = np.lib.format.open_memmap(
        out_path, mode="w+", dtype=np.float32, shape=(total, len(stamps)))

    names, live = [], []
    for i, v in enumerate(variants):
        col_ret = runner.run(v)
        matrix[i, :] = col_ret
        if np.any(col_ret):
            live.append(i)
        names.append(f"{v['family']}|lb{v['lookback']}|frac{v['entry_threshold']}"
                     f"|{v['exit_rule']}|rebal{v['holding_cap_bars']}")
        if (i + 1) % 5 == 0 or i + 1 == total:
            print(f"  {i + 1:,}/{total:,}", end="\r", flush=True)

    matrix.flush()
    del matrix
    print()

    dropped = total - len(live)
    if dropped:
        print(f"  {dropped:,} variants never took a position — excluded from scoring")

    with open(os.path.join(d, "variant_names.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(names) + "\n")
    with open(os.path.join(d, "active_variants.json"), "w", encoding="utf-8") as fh:
        json.dump({"layout": "variants_by_observations",
                   "total_variants": total, "active": live}, fh)
    with open(os.path.join(d, "universe_used.json"), "w", encoding="utf-8") as fh:
        json.dump({"universe": uni_name,
                   "symbols_with_data": active,
                   "symbols_missing_data": missing,
                   "median_investable_per_bar": int(np.median(per_bar))},
                  fh, indent=2)

    print(f"  wrote {out_path}")
    print(f"\n  next: python finalize.py {d}")


if __name__ == "__main__":
    main()
