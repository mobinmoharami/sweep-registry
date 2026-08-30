#!/usr/bin/env bash
# Register, timestamp, run and score every template that is not done yet.
#
# Each family gets its OWN sweep id and its OWN pre-registration. They are
# never merged into one space: variants raise the multiple-testing bar for
# everything they share a sweep with, so ten clean sweeps beat one huge one.
set -uo pipefail
cd "$(dirname "$0")"

mkdir -p sweeps
for tpl in examples/templates/*.json; do
    sid=$(python3 -c "import json;print(json.load(open('$tpl'))['sweep_id'])")
    dir="sweeps/$sid"

    if [ -f "$dir/RECORD.md" ]; then
        echo "== $sid already scored, skipping"
        continue
    fi

    echo "== $sid"
    mkdir -p "$dir"
    [ -f "$dir/preregistration.json" ] || cp "$tpl" "$dir/preregistration.json"

    if [ ! -f "$dir/preregistration.frozen.json" ]; then
        python3 register.py "$dir" || { echo "   register failed"; continue; }
        if command -v ots >/dev/null 2>&1; then
            ots stamp "$dir/preregistration.sha256" 2>&1 | tail -1
        else
            echo "   ! ots not installed — no timestamp. pip install opentimestamps-client"
        fi
    fi

    [ -f "$dir/returns.npy" ] || python3 run_sweep.py "$dir" | tail -2
    python3 finalize.py "$dir" | grep -E "^SW|verdict|DSR|detection" | head -5
    python3 diagnose.py "$dir" --null 10 2>&1 | grep -E "z =|MECHANISM|NO SIGNAL|ARTEFACT|SIGNAL|DIRECTIONAL|MIXED" | head -3
    echo
done

echo "done. records:"
ls -1 sweeps/*/RECORD.md 2>/dev/null | sed 's|sweeps/||;s|/RECORD.md||' | tr '\n' ' '
echo
