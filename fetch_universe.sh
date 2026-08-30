#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")"
total=$(wc -l < universe_symbols.txt); i=0
while read -r sym; do
    i=$((i+1))
    [ -f "data/${sym}_1h.csv" ] && continue
    echo "[$i/$total] $sym"
    python3 data/fetch_binance_bulk.py "$sym" 1h 2017-08 2026-07 2>&1 | tail -1
done < universe_symbols.txt
echo "done: $(ls data/*_1h.csv | wc -l) files"
