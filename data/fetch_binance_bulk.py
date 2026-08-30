#!/usr/bin/env python3
"""Bulk OHLCV from data.binance.vision — monthly zips, not paginated API calls.

    python data/fetch_binance_bulk.py BTCUSDT 1h 2017-08 2026-07

Tens of times faster than the REST endpoint, with no pagination gaps.
Every file is verified against Binance's own SHA256 checksum and recorded
in a manifest.

WHY THE MANIFEST MATTERS
------------------------
Binance silently rewrites historical klines. Their own `updates/` folder
lists the revisions. So "I downloaded BTCUSDT 1h" is not a reproducible
statement — "I downloaded these files, with these hashes, on this date"
is. Without the manifest a registry entry cannot be verified by anyone
later, including you.

    --market spot        (default) | um  (USD-M futures) | cm (COIN-M)
    --workers 6          parallel downloads
    --force              re-download and overwrite
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST_DIR = os.path.join(HERE, "manifest")
BASE = "https://data.binance.vision/data"

MARKET_PATH = {"spot": "spot", "um": "futures/um", "cm": "futures/cm"}

# Expected bar spacing in milliseconds. Derived from the requested interval,
# never inferred from the data: a single stray timestamp a few milliseconds
# out of line would otherwise make every ordinary bar look like a gap.
INTERVAL_MS = {
    "1s": 1_000, "1m": 60_000, "3m": 180_000, "5m": 300_000,
    "15m": 900_000, "30m": 1_800_000, "1h": 3_600_000, "2h": 7_200_000,
    "4h": 14_400_000, "6h": 21_600_000, "8h": 28_800_000,
    "12h": 43_200_000, "1d": 86_400_000, "3d": 259_200_000,
    "1w": 604_800_000,
}

# Binance switched SPOT timestamps to microseconds on 2025-01-01.
# Anything above this is microseconds; below, milliseconds.
MICROSECOND_THRESHOLD = 1e14


def month_range(start: str, end: str) -> list[str]:
    y0, m0 = (int(x) for x in start.split("-")[:2])
    y1, m1 = (int(x) for x in end.split("-")[:2])
    out, y, m = [], y0, m0
    while (y, m) <= (y1, m1):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def urls_for(market: str, symbol: str, interval: str, month: str) -> tuple[str, str]:
    root = f"{BASE}/{MARKET_PATH[market]}/monthly/klines/{symbol}/{interval}"
    zip_url = f"{root}/{symbol}-{interval}-{month}.zip"
    return zip_url, zip_url + ".CHECKSUM"


def fetch(session: requests.Session, url: str, tries: int = 4) -> bytes | None:
    for attempt in range(1, tries + 1):
        try:
            resp = session.get(url, timeout=60)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.content
        except Exception as exc:  # noqa: BLE001
            if attempt == tries:
                print(f"  ! {url.rsplit('/', 1)[-1]}: {exc}", file=sys.stderr)
                return None
            import time
            time.sleep(2 ** attempt)
    return None


def normalise_open_time(value: str) -> int:
    """Return milliseconds regardless of the source unit."""
    v = int(float(value))
    return v // 1000 if v > MICROSECOND_THRESHOLD else v


def parse_zip(blob: bytes) -> list[list[str]]:
    rows = []
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            for line in io.TextIOWrapper(fh, encoding="utf-8"):
                parts = line.strip().split(",")
                if len(parts) < 6:
                    continue
                if not parts[0].replace(".", "").isdigit():
                    continue  # header row, present in some newer files
                rows.append([
                    str(normalise_open_time(parts[0])),
                    parts[1], parts[2], parts[3], parts[4], parts[5],
                ])
    return rows


def download_month(session, market, symbol, interval, month, force):
    zip_url, sum_url = urls_for(market, symbol, interval, month)

    blob = fetch(session, zip_url)
    if blob is None:
        return {"month": month, "status": "missing"}

    digest = hashlib.sha256(blob).hexdigest()

    verified = False
    checksum_blob = fetch(session, sum_url)
    if checksum_blob:
        expected = checksum_blob.decode().split()[0].strip()
        if expected != digest:
            return {
                "month": month, "status": "checksum_mismatch",
                "expected": expected, "got": digest,
            }
        verified = True

    try:
        rows = parse_zip(blob)
    except zipfile.BadZipFile:
        return {"month": month, "status": "bad_zip"}

    return {
        "month": month,
        "status": "ok",
        "rows": rows,
        "record": {
            "url": zip_url,
            "sha256": digest,
            "bytes": len(blob),
            "rows": len(rows),
            "checksum_verified": verified,
            "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol")
    ap.add_argument("interval")
    ap.add_argument("start", help="YYYY-MM")
    ap.add_argument("end", help="YYYY-MM")
    ap.add_argument("--market", default="spot", choices=sorted(MARKET_PATH))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    out_path = os.path.join(HERE, f"{args.symbol}_{args.interval}.csv")
    if os.path.exists(out_path) and not args.force:
        sys.exit(f"{out_path} exists — pass --force to rebuild it")

    os.makedirs(MANIFEST_DIR, exist_ok=True)
    months = month_range(args.start, args.end)
    print(f"{args.symbol} {args.interval} [{args.market}] — {len(months)} months")

    session = requests.Session()
    results: dict[str, dict] = {}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(download_month, session, args.market, args.symbol,
                        args.interval, m, args.force): m
            for m in months
        }
        done = 0
        for fut, month in futures.items():
            res = fut.result()
            results[month] = res
            done += 1
            print(f"  {done}/{len(months)} {month} {res['status']}",
                  end="\r", flush=True)

    print()

    # ---- assemble in chronological order ----------------------------
    manifest, total_rows, problems = [], 0, []
    seen: set[int] = set()

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["open_time_ms", "open", "high", "low", "close", "volume"])
        for month in months:
            res = results.get(month, {"status": "missing"})
            if res["status"] != "ok":
                if res["status"] != "missing":
                    problems.append(f"{month}: {res['status']}")
                continue
            for row in res["rows"]:
                ts = int(row[0])
                if ts in seen:
                    continue          # overlap between adjacent files
                seen.add(ts)
                writer.writerow(row)
                total_rows += 1
            manifest.append(res["record"])

    manifest_path = os.path.join(
        MANIFEST_DIR, f"{args.symbol}_{args.interval}_{args.market}.json"
    )
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "symbol": args.symbol,
                "interval": args.interval,
                "market": args.market,
                "requested_range": [args.start, args.end],
                "total_rows": total_rows,
                "files": manifest,
                "problems": problems,
            },
            fh,
            indent=2,
            sort_keys=True,
        )

    unverified = sum(1 for f in manifest if not f["checksum_verified"])

    print(f"  {total_rows:,} bars -> {out_path}")
    print(f"  {len(manifest)} files, manifest -> {manifest_path}")
    if unverified:
        print(f"  ! {unverified} file(s) had no CHECKSUM available")
    for p in problems:
        print(f"  ! {p}")

    # ---- gap report -------------------------------------------------
    step = INTERVAL_MS.get(args.interval)
    if total_rows > 1 and step:
        stamps = sorted(seen)
        deltas = [stamps[i + 1] - stamps[i] for i in range(len(stamps) - 1)]
        tolerance = max(1, step // 100)
        gaps = [d for d in deltas if d > step + tolerance]
        misaligned = sum(1 for d in deltas if abs(d - step) > tolerance and d < step)
        if gaps:
            missing = sum(round(d / step) - 1 for d in gaps)
            longest = max(gaps) / step
            print(f"  ! {len(gaps)} gap(s), ~{missing:,} bars missing, "
                  f"longest {longest:.0f} bars "
                  f"(exchange downtime — recorded, not filled)")
        else:
            print("  no gaps")
        if misaligned:
            print(f"  ! {misaligned} timestamp(s) closer together than one bar")


if __name__ == "__main__":
    main()
