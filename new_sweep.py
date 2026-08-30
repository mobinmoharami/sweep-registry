#!/usr/bin/env python3
"""Start a new sweep from an existing one, without dragging its seal along.

    python new_sweep.py SW-0002
    python new_sweep.py SW-0002 --from examples/SW-0001-crypto-mean-reversion

Copying a sweep directory by hand carries over `preregistration.frozen.json`
and its hash, and then register.py correctly refuses to touch it. This copies
only the editable document and stamps in the new id.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TEMPLATE = os.path.join(HERE, "examples", "SW-0001-crypto-mean-reversion")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sweep_id")
    ap.add_argument("--from", dest="template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--dir", default=os.path.join(HERE, "sweeps"))
    args = ap.parse_args()

    src = os.path.join(args.template, "preregistration.json")
    if not os.path.exists(src):
        sys.exit(f"template not found: {src}")

    dest_dir = os.path.join(args.dir, args.sweep_id)
    if os.path.exists(dest_dir):
        sys.exit(f"{dest_dir} already exists")

    os.makedirs(dest_dir)
    shutil.copy(src, dest_dir)

    path = os.path.join(dest_dir, "preregistration.json")
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    doc["sweep_id"] = args.sweep_id
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)

    print(f"created {path}")
    print()
    print("  1. edit it — search space, symbols, dates, n_observations")
    print(f"  2. python register.py {dest_dir}")
    print(f"  3. ots stamp {dest_dir}/preregistration.sha256")
    print(f"  4. python run_sweep.py {dest_dir}")
    print(f"  5. python finalize.py {dest_dir}")


if __name__ == "__main__":
    main()
