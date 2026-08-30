#!/usr/bin/env python3
"""Build a point-in-time symbol universe for cross-sectional sweeps.

    python data/build_universe.py --top 20 --start 2019-01 --end 2025-06

THE PROBLEM THIS SOLVES
-----------------------
Taking today's top 20 coins and backtesting them over the past six years is
the single most effective way to invent an edge that never existed. Every
coin that died has been removed from the list, so the sample contains only
survivors. Ammann, Burdorf, Liebi and Stockl (SSRN 4287573) measured this
across 3,904 coins and found an annualised survivorship bias of 62.19% for
equal-weighted portfolios.

So the universe has to be rebuilt as of each date, using only information
available on that date:

  - membership is decided monthly, from the PREVIOUS month's quote volume
  - a coin that was delisted later is still in the universe before it was
  - a coin that had not yet listed is absent, not backfilled

Binance's public archive keeps delisted pairs, which is what makes this
possible at all. Kraken's CSV export does not.

OUTPUT
------
data/universe/<name>.json — for each month, the ranked symbols and the volume
they were ranked on, plus the full download manifest so the selection can be
reproduced or audited later.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UNIVERSE_DIR = os.path.join(HERE, "universe")
BASE = "https://data.binance.vision/data/spot/monthly/klines"
LISTING = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"

# Stablecoin and wrapped pairs: mechanically pegged, so ranking them by
# momentum is meaningless and they crowd out real assets in the top N.
EXCLUDE = re.compile(
    r"^(USDC|BUSD|TUSD|USDP|DAI|FDUSD|EUR|GBP|AUD|TRY|BRL|RUB|UAH|NGN|ZAR|"
    r"IDRT|BIDR|VAI|USDS|SUSD|PAX|WBTC|WBETH|BETH|STETH)USDT$"
)


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


def list_symbols(session: requests.Session) -> list[str]:
    """Every USDT spot pair the archive has ever held, including dead ones."""
    symbols: list[str] = []
    token = None
    while True:
        params = {"delimiter": "/", "prefix": "data/spot/monthly/klines/",
                  "list-type": "2"}
        if token:
            params["continuation-token"] = token
        resp = session.get(LISTING, params=params, timeout=60)
        resp.raise_for_status()
        body = resp.text
        for m in re.finditer(r"<Prefix>data/spot/monthly/klines/([^/]+)/</Prefix>", body):
            sym = m.group(1)
            if sym.endswith("USDT") and not EXCLUDE.match(sym):
                symbols.append(sym)
        tok = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", body)
        if not tok:
            break
        token = tok.group(1)
        print(f"  listing... {len(symbols):,} USDT pairs", end="\r", flush=True)
    print(f"  {len(symbols):,} USDT pairs in the archive (delisted included)")
    return sorted(set(symbols))


def monthly_volume(session: requests.Session, symbol: str, month: str):
    """Quote volume for one symbol-month, or None if it did not trade."""
    url = f"{BASE}/{symbol}/1d/{symbol}-1d-{month}.zip"
    try:
        resp = session.get(url, timeout=45)
        if resp.status_code == 404:
            return symbol, month, None, None
        resp.raise_for_status()
    except Exception:
        return symbol, month, None, None

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            with zf.open(zf.namelist()[0]) as fh:
                total = 0.0
                days = 0
                for line in io.TextIOWrapper(fh, encoding="utf-8"):
                    parts = line.strip().split(",")
                    if len(parts) < 8 or not parts[0].replace(".", "").isdigit():
                        continue
                    total += float(parts[7])      # quote asset volume
                    days += 1
    except Exception:
        return symbol, month, None, None

    if days < 20:      # a partial month is not evidence of liquidity
        return symbol, month, None, days
    return symbol, month, total, days


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--start", default="2019-01")
    ap.add_argument("--end", default="2025-06")
    ap.add_argument("--name", default=None)
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    name = args.name or f"top{args.top}_{args.start}_{args.end}"
    os.makedirs(UNIVERSE_DIR, exist_ok=True)
    out_path = os.path.join(UNIVERSE_DIR, f"{name}.json")
    if os.path.exists(out_path):
        sys.exit(f"{out_path} exists — delete it deliberately to rebuild")

    session = requests.Session()
    session.headers["User-Agent"] = "sweep-registry/0.1 (research)"

    print("listing every USDT pair the archive has ever held")
    symbols = list_symbols(session)

    months = month_range(args.start, args.end)
    print(f"reading daily volume for {len(symbols):,} symbols x {len(months)} months")
    print("  (most combinations 404 — that is a pair not trading yet, or already dead)")

    volumes: dict[str, dict[str, float]] = {m: {} for m in months}
    jobs = [(s, m) for m in months for s in symbols]
    done = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        CHUNK = 4000
        for i in range(0, len(jobs), CHUNK):
            batch = jobs[i:i + CHUNK]
            for sym, month, vol, _days in pool.map(
                lambda j: monthly_volume(session, j[0], j[1]), batch
            ):
                done += 1
                if vol is not None and vol > 0:
                    volumes[month][sym] = vol
            print(f"  {done:,}/{len(jobs):,}", end="\r", flush=True)

    print()

    # ---- rank, with a one-month lag ---------------------------------
    universe = {}
    for i, month in enumerate(months):
        if i == 0:
            continue                      # nothing to rank on yet
        prev = months[i - 1]
        ranked = sorted(volumes[prev].items(), key=lambda kv: kv[1], reverse=True)
        chosen = ranked[:args.top]
        universe[month] = {
            "ranked_on": prev,
            "symbols": [s for s, _ in chosen],
            "quote_volume": {s: round(v, 2) for s, v in chosen},
            "candidates": len(ranked),
        }

    all_symbols = sorted({s for m in universe.values() for s in m["symbols"]})
    turnover = []
    keys = sorted(universe)
    for a, b in zip(keys, keys[1:]):
        prev_set = set(universe[a]["symbols"])
        new = [s for s in universe[b]["symbols"] if s not in prev_set]
        turnover.append(len(new))

    doc = {
        "name": name,
        "top_n": args.top,
        "months": universe,
        "all_symbols_ever": all_symbols,
        "n_symbols_ever": len(all_symbols),
        "mean_monthly_entrants": round(sum(turnover) / max(len(turnover), 1), 2),
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": (
            "Membership for each month is the top N by quote volume over the "
            "PREVIOUS month, computed from Binance daily klines. A symbol needs "
            "at least 20 trading days in the ranking month to be eligible. "
            "Delisted pairs remain in the archive and are therefore included "
            "for the months in which they actually traded. No symbol is "
            "selected using information from after its membership date."
        ),
        "source": "https://data.binance.vision spot monthly 1d klines",
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)

    print(f"  {len(universe)} months, {len(all_symbols)} distinct symbols ever held")
    print(f"  mean new entrants per month: {doc['mean_monthly_entrants']}")
    print(f"  -> {out_path}")
    print()
    print("  symbols that appear and later vanish are the point: they are what")
    print("  a naive 'top coins today' universe silently deletes.")


if __name__ == "__main__":
    main()
