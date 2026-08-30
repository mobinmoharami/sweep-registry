#!/usr/bin/env bash
# Download the FX pairs the SW-0011..0016 templates expect.
# Slow: one file per instrument per hour. Roughly an hour per pair for 8 years.
# Resumable in the sense that each pair writes its own file; rerun what failed.
set -uo pipefail
cd "$(dirname "$0")"

START="${1:-2017-09}"
END="${2:-2025-06}"

for pair in EURUSD GBPUSD USDJPY; do
    if [ -f "data/${pair}_1h.csv" ]; then
        echo "== ${pair} already downloaded, skipping"
        continue
    fi
    echo "== ${pair} ${START} -> ${END}"
    # One HTTP request per instrument-hour: ~68,000 for eight years, so expect
    # this to take a while. Ticks are folded into bars as they arrive and a
    # .partial checkpoint is written after every chunk, so an interruption
    # costs minutes rather than the whole download — just rerun this script.
    python3 data/fetch_dukascopy.py "$pair" 1h "$START" "$END" || \
        echo "   ! ${pair} failed — rerun to resume from the checkpoint"
done

echo
echo "verify before freezing — n_observations in the templates is an estimate:"
for pair in EURUSD GBPUSD USDJPY; do
    [ -f "data/${pair}_1h.csv" ] && \
        printf "  %-8s %s bars\n" "$pair" "$(( $(wc -l < "data/${pair}_1h.csv") - 1 ))"
done
