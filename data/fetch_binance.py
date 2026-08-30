#!/usr/bin/env python3
"""Download OHLCV from Binance public endpoints. No API key, no account.

    python data/fetch_binance.py BTCUSDT 1h 2019-01-01 2025-06-30

Writes data/BTCUSDT_1h.csv with columns:
    open_time_ms,open,high,low,close,volume

Resumable: if the file exists it continues from the last bar instead of
starting over. Kill it and rerun as often as you like.
"""
from __future__ import annotations

import csv
import os
import sys
import time
from datetime import datetime, timezone

import requests

BASE = "https://api.binance.com/api/v3/klines"
LIMIT = 1000
HERE = os.path.dirname(os.path.abspath(__file__))

INTERVAL_MS = {
    "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000,
    "1d": 86_400_000,
}


def to_ms(date_str: str) -> int:
    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def last_open_time(path: str) -> int | None:
    if not os.path.exists(path):
        return None
    last = None
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh):
            if row and row[0].isdigit():
                last = int(row[0])
    return last


def main() -> None:
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)

    symbol, interval, start_s, end_s = sys.argv[1:5]
    if interval not in INTERVAL_MS:
        sys.exit(f"unsupported interval — pick from {sorted(INTERVAL_MS)}")

    step = INTERVAL_MS[interval]
    start_ms, end_ms = to_ms(start_s), to_ms(end_s)
    path = os.path.join(HERE, f"{symbol}_{interval}.csv")

    resume = last_open_time(path)
    if resume is not None:
        start_ms = resume + step
        print(f"resuming from {datetime.fromtimestamp(start_ms / 1000, timezone.utc)}")
        fh = open(path, "a", newline="", encoding="utf-8")
        writer = csv.writer(fh)
    else:
        fh = open(path, "w", newline="", encoding="utf-8")
        writer = csv.writer(fh)
        writer.writerow(["open_time_ms", "open", "high", "low", "close", "volume"])

    total = 0
    cursor = start_ms
    session = requests.Session()

    try:
        while cursor < end_ms:
            for attempt in range(1, 6):
                try:
                    resp = session.get(
                        BASE,
                        params={
                            "symbol": symbol,
                            "interval": interval,
                            "startTime": cursor,
                            "endTime": end_ms,
                            "limit": LIMIT,
                        },
                        timeout=20,
                    )
                    if resp.status_code == 429:
                        wait = int(resp.headers.get("Retry-After", 30))
                        print(f"rate limited — sleeping {wait}s")
                        time.sleep(wait)
                        continue
                    resp.raise_for_status()
                    rows = resp.json()
                    break
                except Exception as exc:  # noqa: BLE001
                    if attempt == 5:
                        raise
                    print(f"  retry {attempt}: {exc}")
                    time.sleep(2 ** attempt)

            if not rows:
                break

            for k in rows:
                writer.writerow([k[0], k[1], k[2], k[3], k[4], k[5]])
            fh.flush()

            total += len(rows)
            cursor = rows[-1][0] + step
            stamp = datetime.fromtimestamp(rows[-1][0] / 1000, timezone.utc).date()
            print(f"  {total:,} bars — through {stamp}", end="\r", flush=True)

            if len(rows) < LIMIT:
                break
            time.sleep(0.25)  # stay well inside the public rate limit
    finally:
        fh.close()

    print(f"\nwrote {total:,} new bars to {path}")


if __name__ == "__main__":
    main()
