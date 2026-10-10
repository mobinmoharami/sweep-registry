#!/usr/bin/env python3
"""
Records, in each affected sweep's annotations.json, why its scored trial
count is lower than the count declared at pre-registration.

finalize.py already emits an integrity note for these sweeps saying
"Explain this in the record." This writes that explanation.

Usage:
    cd /opt/sweep-registry
    python3 paper/annotate_shortfall.py --dry-run
    python3 paper/annotate_shortfall.py
"""
import argparse
import datetime
import glob
import json
import os

KEY = "trial_count_shortfall"

TEXT = (
    "{missing:,} of the {declared:,} enumerated variants produced no trade at "
    "any point in the sample. The Sharpe ratio of an identically zero return "
    "series is undefined, so those columns were excluded at scoring time and "
    "n_trials records the {scored:,} that remain. "
    "This exclusion is not neutral: the Deflated Sharpe Ratio penalises by "
    "trial count, so scoring {scored:,} trials instead of {declared:,} applies "
    "a lighter multiple-testing penalty and biases this sweep's DSR upward. "
    "The error runs in the permissive direction and is recorded for that "
    "reason. No variant was removed on the basis of its performance; the "
    "excluded set is determined entirely by whether the parameter combination "
    "ever fired."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweeps", default="sweeps")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    touched = 0

    for d in sorted(glob.glob(os.path.join(a.sweeps, "SW-*"))):
        pre_p = os.path.join(d, "preregistration.json")
        res_p = os.path.join(d, "result.json")
        if not (os.path.exists(pre_p) and os.path.exists(res_p)):
            continue

        pre = json.load(open(pre_p, encoding="utf-8"))
        res = json.load(open(res_p, encoding="utf-8"))
        declared = int(pre["search_space"]["n_trials"])
        scored = int(res["n_trials"])
        if scored >= declared:
            continue

        ann_p = os.path.join(d, "annotations.json")
        ann = {}
        if os.path.exists(ann_p):
            try:
                ann = json.load(open(ann_p, encoding="utf-8"))
            except json.JSONDecodeError:
                print(f"[skip] {os.path.basename(d)}: annotations.json is not valid JSON")
                continue

        if KEY in ann:
            print(f"[ok]   {os.path.basename(d)}: already annotated")
            continue

        ann[KEY] = {
            "declared_trials": declared,
            "scored_trials": scored,
            "never_traded": declared - scored,
            "explanation": TEXT.format(
                declared=declared, scored=scored, missing=declared - scored),
            "direction_of_bias": "permissive (DSR overstated)",
            "recorded_utc": now,
        }
        ann["updated_utc"] = now

        print(f"[write] {os.path.basename(d)}: {scored:,} of {declared:,} "
              f"({declared - scored:,} never traded)")
        touched += 1
        if not a.dry_run:
            with open(ann_p, "w", encoding="utf-8") as fh:
                json.dump(ann, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

    print(f"\n{touched} sweep(s) {'would be' if a.dry_run else ''} annotated")


if __name__ == "__main__":
    main()
