#!/usr/bin/env python3
"""Bulk FX bars from Dukascopy. Free, no account, no API key.

    python data/fetch_dukascopy.py EURUSD 1h 2017-09 2025-06

Dukascopy publishes one LZMA-compressed file per instrument per hour, each
holding that hour's ticks. We fetch them in parallel and aggregate to bars.

MEMORY
------
Ticks are aggregated into bars as each file arrives and then discarded.
Keeping the ticks first is the obvious implementation and it does not work:
1,500 hours of EURUSD is already ~4 million ticks, and eight years is ~68,000
hours. Bars are bounded at roughly 50,000 for the same period.

A .partial checkpoint is written after every 2,000 hours, so an interrupted
download resumes instead of starting over.

WEEKENDS
--------
FX does not trade from Friday ~22:00 UTC to Sunday ~22:00 UTC. Those hours
are simply absent, and that is correct — they must NOT be forward-filled.
A filled weekend bar has zero return and zero range, which every mean
reversion rule reads as a signal and every volatility rule reads as calm.
This writer emits only hours that actually traded, and reports the Sunday
gaps separately from real outages so the two are never confused.

Bars are indexed by open time in milliseconds, matching the Binance files,
so the same sweep engine reads both without changes.
"""
from __future__ import annotations

import argparse
import csv
import json
import lzma
import os
import struct
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST_DIR = os.path.join(HERE, "manifest")
BASE = "https://datafeed.dukascopy.com/datafeed"

# Dukascopy stores prices as integers; the scale depends on the instrument.
# JPY crosses quote to 3 decimals, most others to 5.
POINT_SCALE = {"JPY": 1e3}
DEFAULT_SCALE = 1e5

INTERVAL_MS = {
    "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000,
}

TICK_STRUCT = struct.Struct(">3I2f")   # ms offset, ask, bid, ask vol, bid vol


def scale_for(symbol: str) -> float:
    return POINT_SCALE.get(symbol[3:6].upper(), DEFAULT_SCALE)


def hour_url(symbol: str, dt: datetime) -> str:
    # months are ZERO-indexed in Dukascopy paths. January is 00.
    return (f"{BASE}/{symbol.upper()}/{dt.year:04d}/{dt.month - 1:02d}/"
            f"{dt.day:02d}/{dt.hour:02d}h_ticks.bi5")


def fetch_hour(session: requests.Session, symbol: str, dt: datetime,
               tries: int = 3):
    url = hour_url(symbol, dt)
    for attempt in range(1, tries + 1):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 404:
                return dt, None, "absent"
            resp.raise_for_status()
            return dt, resp.content, "ok"
        except Exception as exc:  # noqa: BLE001
            if attempt == tries:
                return dt, None, f"error: {type(exc).__name__}"
            import time
            time.sleep(2 ** attempt)
    return dt, None, "error"


def decode(blob: bytes, hour_start: datetime, scale: float):
    """Yield (timestamp_ms, mid_price) from one .bi5 file."""
    if not blob:
        return
    try:
        raw = lzma.decompress(blob)
    except lzma.LZMAError:
        return

    base_ms = int(hour_start.timestamp() * 1000)
    size = TICK_STRUCT.size
    for off in range(0, len(raw) - size + 1, size):
        ms, ask, bid, _, _ = TICK_STRUCT.unpack_from(raw, off)
        # mid price: the sweep engine expects a single price series, and
        # using bid or ask alone would bake a constant drift into every result
        yield base_ms + ms, (ask + bid) / 2.0 / scale


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol", help="e.g. EURUSD, GBPUSD, USDJPY, XAUUSD")
    ap.add_argument("interval", choices=sorted(INTERVAL_MS))
    ap.add_argument("start", help="YYYY-MM")
    ap.add_argument("end", help="YYYY-MM")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    symbol = args.symbol.upper()
    out_path = os.path.join(HERE, f"{symbol}_{args.interval}.csv")
    if os.path.exists(out_path) and not args.force:
        sys.exit(f"{out_path} exists — pass --force to rebuild it")

    y0, m0 = (int(x) for x in args.start.split("-")[:2])
    y1, m1 = (int(x) for x in args.end.split("-")[:2])
    start = datetime(y0, m0, 1, tzinfo=timezone.utc)
    end = datetime(y1 + (m1 // 12), (m1 % 12) + 1, 1, tzinfo=timezone.utc)

    hours = []
    cur = start
    while cur < end:
        hours.append(cur)
        cur += timedelta(hours=1)

    print(f"{symbol} {args.interval} — {len(hours):,} hourly files "
          f"({args.start} to {args.end})")
    print("  weekend hours will 404; that is expected, not an error")

    scale = scale_for(symbol)
    step = INTERVAL_MS[args.interval]
    session = requests.Session()
    session.headers["User-Agent"] = "sweep-registry/0.1 (research)"

    # Aggregate into bars AS FILES ARRIVE and discard the ticks. Holding every
    # tick first needs tens of GB for a multi-year request — 1,500 hours of
    # EURUSD alone is ~4 million ticks — and the process gets OOM-killed long
    # before it finishes. Bars are bounded: ~50k of them for eight years.
    bars: dict[int, list[float]] = {}
    # Resume from a partial file. Eight years is ~68,000 requests; a dropped
    # connection an hour in should not mean starting over.
    partial = out_path + ".partial"
    resume_from = 0
    if os.path.exists(partial) and not args.force:
        with open(partial, newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh):
                if row and row[0].isdigit():
                    bars[int(row[0])] = [float(row[1]), float(row[2]),
                                         float(row[3]), float(row[4])]
        if bars:
            last = max(bars)
            resume_from = last
            del bars[last]          # that bar may be incomplete — refetch it
            hours = [h for h in hours
                     if int(h.timestamp() * 1000) >= last]
            print(f"  resuming: {len(bars):,} bars kept, "
                  f"{len(hours):,} hours left")

    absent = 0
    errors: list[str] = []
    done = 0
    n_ticks = 0

    def absorb(blob, dt):
        nonlocal n_ticks
        for ms, price in decode(blob, dt, scale):
            n_ticks += 1
            key = (ms // step) * step
            b = bars.get(key)
            if b is None:
                bars[key] = [price, price, price, price]
            else:
                if price > b[1]:
                    b[1] = price
                if price < b[2]:
                    b[2] = price
                b[3] = price

    # Submit in chunks so the executor does not hold 68,000 pending futures.
    CHUNK = 2000
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i in range(0, len(hours), CHUNK):
            batch = hours[i:i + CHUNK]
            for dt, blob, status in pool.map(
                lambda h: fetch_hour(session, symbol, h), batch
            ):
                done += 1
                if status == "absent":
                    absent += 1
                elif status.startswith("error"):
                    errors.append(f"{dt.isoformat()}: {status}")
                else:
                    absorb(blob, dt)
                if done % 500 == 0 or done == len(hours):
                    print(f"  {done:,}/{len(hours):,}  bars {len(bars):,}",
                          end="\r", flush=True)

            # checkpoint after every chunk
            with open(partial, "w", newline="", encoding="utf-8") as fh:
                cw = csv.writer(fh)
                cw.writerow(["open_time_ms", "open", "high", "low", "close"])
                for k in sorted(bars):
                    o, h, l, c = bars[k]
                    cw.writerow([k, f"{o:.6f}", f"{h:.6f}", f"{l:.6f}", f"{c:.6f}"])

    print()
    if not bars:
        sys.exit("no data retrieved — check the symbol name and date range")

    keys = sorted(bars)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["open_time_ms", "open", "high", "low", "close", "volume"])
        for k in keys:
            o, h, l, c = bars[k]
            w.writerow([k, f"{o:.6f}", f"{h:.6f}", f"{l:.6f}", f"{c:.6f}", "0"])

    # ---- gap report: weekends vs real outages ----------------------
    weekend_gaps = real_gaps = 0
    missing_bars = 0
    for i in range(len(keys) - 1):
        delta = keys[i + 1] - keys[i]
        if delta <= step:
            continue
        n_missing = delta // step - 1
        # a gap that starts Friday evening and ends Sunday evening is the
        # market being shut, not data loss
        gap_start = datetime.fromtimestamp(keys[i] / 1000, timezone.utc)
        gap_end = datetime.fromtimestamp(keys[i + 1] / 1000, timezone.utc)
        if gap_start.weekday() in (4, 5) and gap_end.weekday() in (6, 0):
            weekend_gaps += 1
        else:
            real_gaps += 1
            missing_bars += n_missing

    manifest = {
        "symbol": symbol, "interval": args.interval, "source": "dukascopy",
        "requested_range": [args.start, args.end],
        "hours_requested": len(hours), "hours_absent": absent,
        "ticks": n_ticks, "bars": len(keys),
        "first_bar_ms": keys[0], "last_bar_ms": keys[-1],
        "weekend_gaps": weekend_gaps,
        "non_weekend_gaps": real_gaps,
        "non_weekend_missing_bars": missing_bars,
        "price": "mid of bid and ask",
        "point_scale": scale,
        "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "errors": errors[:50],
        "note": ("Weekend hours are absent, never filled. Filling them would "
                 "create zero-return zero-range bars that mean reversion rules "
                 "read as signal and volatility rules read as calm."),
    }
    os.makedirs(MANIFEST_DIR, exist_ok=True)
    mpath = os.path.join(MANIFEST_DIR, f"{symbol}_{args.interval}_dukascopy.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)

    if os.path.exists(partial):
        os.remove(partial)

    print(f"  {len(keys):,} bars from {n_ticks:,} ticks -> {out_path}")
    print(f"  manifest -> {mpath}")
    print(f"  {weekend_gaps:,} weekend gaps (expected)")
    if real_gaps:
        print(f"  ! {real_gaps:,} non-weekend gaps, ~{missing_bars:,} bars missing")
    if errors:
        print(f"  ! {len(errors)} fetch errors — see manifest")


if __name__ == "__main__":
    main()
