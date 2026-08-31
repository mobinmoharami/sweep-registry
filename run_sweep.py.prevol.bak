#!/usr/bin/env python3
"""Run a sweep exactly as its frozen pre-registration specifies.

    python run_sweep.py sweeps/SW-0001

Reads preregistration.frozen.json, loads the declared symbols and date
range from data/, runs every enumerated variant, and writes returns.csv
for finalize.py.

The pre-registration is the source of truth. This script takes no
parameters of its own — if you want to change the search space you write
a new sweep, you do not pass a flag.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np

from srlab.canonical import canonical_sha256
from sweep.engine import Runner, enumerate_variants

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def fail(msg: str) -> None:
    print(f"ABORT: {msg}", file=sys.stderr)
    sys.exit(1)


def load_bars(symbol: str, timeframe: str, start: str, end: str) -> dict:
    path = os.path.join(DATA, f"{symbol}_{timeframe}.csv")
    if not os.path.exists(path):
        fail(
            f"{path} not found.\n"
            f"  python data/fetch_binance.py {symbol} {timeframe} {start} {end}"
        )

    lo = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp() * 1000)
    hi = int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp() * 1000)

    t, o, h, l, c = [], [], [], [], []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        for row in reader:
            ms = int(row[0])
            if ms < lo or ms > hi:
                continue
            t.append(ms)
            o.append(float(row[1]))
            h.append(float(row[2]))
            l.append(float(row[3]))
            c.append(float(row[4]))

    if len(c) < 100:
        fail(f"{symbol}: only {len(c)} bars in range — refusing to run")

    times = np.array(t, dtype=np.int64)
    return {
        "time": times,
        "hour": ((times // 3_600_000) % 24).astype(np.int64),
        "open": np.array(o), "high": np.array(h),
        "low": np.array(l), "close": np.array(c),
    }


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    if "--i-know-what-im-doing" in sys.argv:
        sys.argv.remove("--i-know-what-im-doing")
        os.environ["SWEEP_OVERRIDE_EMBARGO"] = "1"

    d = sys.argv[1].rstrip("/")
    frozen = os.path.join(d, "preregistration.frozen.json")
    hash_path = os.path.join(d, "preregistration.sha256")
    out_path = os.path.join(d, "returns.npy")

    if not os.path.exists(frozen):
        fail("no frozen pre-registration — run register.py first")
    if os.path.exists(out_path):
        fail(f"{out_path} already exists. Delete it deliberately if you mean to rerun.")

    with open(frozen, encoding="utf-8") as fh:
        prereg = json.load(fh)
    with open(hash_path, encoding="utf-8") as fh:
        stored = json.load(fh)["preregistration_sha256"]
    if canonical_sha256(prereg) != stored:
        fail("frozen pre-registration hash mismatch — this sweep is void")

    # A sweep may be frozen now and executed later. If the pre-registration
    # names an earliest run date, honour it: running a holdout early is how a
    # single-use test gets wasted at low power.
    earliest = prereg.get("planning", {}).get("earliest_run_date")
    if earliest:
        import datetime as _dt
        today = _dt.date.today()
        due = _dt.date.fromisoformat(earliest)
        if today < due and not os.environ.get("SWEEP_OVERRIDE_EMBARGO"):
            fail(
                f"embargoed until {earliest} (today is {today}, "
                f"{(due - today).days} days to go).\n"
                "  This sweep was frozen early on purpose and can only be run once.\n"
                "  Override with --i-know-what-im-doing, and record why."
            )

    data = prereg["data"]
    proto = prereg["protocol"]
    cost_bps = float(proto["costs_bps"]) + float(proto["slippage_bps"])

    variants = enumerate_variants(prereg["search_space"])
    symbols = data["symbols"]
    declared = int(prereg["search_space"]["n_trials"])
    expected = len(variants) * len(symbols)

    print(f"{prereg['sweep_id']} — {prereg['title']}")
    print(f"  {len(variants):,} variants x {len(symbols)} symbols = {expected:,} trials")
    if expected != declared:
        print(
            f"  ! pre-registration declares {declared:,}. "
            "finalize.py will record this discrepancy."
        )

    # ---- load all symbols, align on the shortest ---------------------
    bars = {s: load_bars(s, data["timeframe"], data["start"], data["end"])
            for s in symbols}
    n_bars = min(len(b["close"]) for b in bars.values())
    for s in symbols:
        print(f"  {s}: {len(bars[s]['close']):,} bars")
    print(f"  aligned length: {n_bars:,}")

    for s in symbols:
        for k in ("open", "high", "low", "close", "time", "hour"):
            bars[s][k] = bars[s][k][-n_bars:]

    # ---- run ---------------------------------------------------------
    total = len(variants) * len(symbols)

    # Write straight into a memory-mapped .npy. Building the matrix in RAM
    # and stacking at the end needs several times this much and gets the
    # process OOM-killed on a small VPS. float32 is ample for bar returns.
    mem_mb = n_bars * total * 4 / 1e6
    print(f"  streaming {total:,} x {n_bars:,} float32 matrix "
          f"(~{mem_mb:,.0f} MB on disk, held as memmap)")

    # Stored as (variant, observation), NOT (observation, variant). Writing a
    # variant into a column of a row-major memmap touches every page of the
    # file on every single write; that alone made this step ~60x slower than
    # the arithmetic it was doing. One variant per row keeps writes sequential.
    matrix = np.lib.format.open_memmap(
        out_path, mode="w+", dtype=np.float32, shape=(total, n_bars)
    )

    names, active = [], []
    done = 0
    for symbol in symbols:
        runner = Runner(bars[symbol], cost_bps)   # caches live for one symbol
        for v in variants:
            col = runner.run(v)
            matrix[done, :] = col
            if np.any(col):
                active.append(done)      # variants that never traded carry
                                         # no information and must not count
                                         # towards the multiple-testing penalty
            names.append(
                f"{symbol}|{v['family']}|lb{v['lookback']}"
                f"|th{v['entry_threshold']}|{v['exit_rule']}|cap{v['holding_cap_bars']}"
            )
            done += 1
            if done % 50 == 0 or done == total:
                print(f"  {done:,}/{total:,}", end="\r", flush=True)

    matrix.flush()
    del matrix
    print()

    dropped = total - len(active)
    if dropped:
        print(f"  {dropped:,} variants never opened a position — excluded from scoring")
    print(f"  matrix: {n_bars:,} obs x {len(active):,} active variants")

    with open(os.path.join(d, "variant_names.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(names) + "\n")
    with open(os.path.join(d, "active_variants.json"), "w", encoding="utf-8") as fh:
        json.dump({"layout": "variants_by_observations",
                   "total_variants": total, "active": active}, fh)

    print(f"  wrote {out_path}")
    print(f"\n  next: python finalize.py {d}")


if __name__ == "__main__":
    main()
