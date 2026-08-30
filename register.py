#!/usr/bin/env python3
"""Freeze a pre-registration.

    python register.py examples/SW-0001-crypto-mean-reversion

Validates the document, computes the planned detection limit, writes a
frozen copy and its hash, and refuses to ever overwrite it.

After this, anchor the hash to Bitcoin — free, no account, only the hash
leaves your machine:

    ots stamp <dir>/preregistration.sha256

From that moment the search space, the protocol and the threshold are
fixed. Anything you change afterwards is a new sweep with a new id, not
an edit. That rule is not bureaucracy — it is the only thing standing
between this and marketing.
"""
from __future__ import annotations

import json
import os
import sys

from srlab.canonical import canonical_bytes, canonical_sha256
from statistics import NormalDist

from srlab.stats import annualise, expected_max_sharpe, min_detectable_sharpe

METRICS = {
    # best variant must clear a deflated-Sharpe threshold
    "deflated_sharpe_ratio",
    # the whole population's market-neutral gross Sharpe must sit far enough
    # from what shuffled data produces. Far weaker per-variant effects are
    # detectable this way, because the estimate pools every variant.
    "cross_sectional_residual_sharpe_z",
}

REQUIRED = {
    "sweep_id": str,
    "title": str,
    "hypothesis": str,
    "search_space": dict,
    "data": dict,
    "protocol": dict,
    "decision_rule": dict,
    "planning": dict,
}

REQUIRED_NESTED = {
    "search_space": ["families", "parameters", "n_trials"],
    "data": ["symbols", "start", "end", "timeframe", "source", "holdout"],
    "protocol": ["method", "costs_bps", "slippage_bps", "execution_model"],
    "decision_rule": ["metric", "alpha", "threshold"],
    "planning": ["periods_per_year", "n_observations", "assumed_var_trial_sharpes",
                 "power"],
}


def fail(msg: str) -> None:
    print(f"REJECTED: {msg}", file=sys.stderr)
    sys.exit(1)


def validate(doc: dict) -> None:
    for key, kind in REQUIRED.items():
        if key not in doc:
            fail(f"missing required field '{key}'")
        if not isinstance(doc[key], kind):
            fail(f"field '{key}' must be {kind.__name__}")

    for parent, children in REQUIRED_NESTED.items():
        for child in children:
            if child not in doc[parent]:
                fail(f"missing required field '{parent}.{child}'")

    metric = doc["decision_rule"]["metric"]
    if metric not in METRICS:
        fail(f"decision_rule.metric must be one of {sorted(METRICS)}")
    if metric == "cross_sectional_residual_sharpe_z":
        if "assumed_null_residual_sharpe_sd" not in doc["planning"]:
            fail("planning.assumed_null_residual_sharpe_sd is required for this metric")
        if int(doc["planning"].get("null_runs", 0)) < 5:
            fail("planning.null_runs must be at least 5 for this metric")

    n = doc["search_space"]["n_trials"]
    if not isinstance(n, int) or n < 1:
        fail("search_space.n_trials must be a positive integer")

    if doc["data"]["holdout"] in (None, "", []):
        fail(
            "data.holdout is empty. A slice you never look at until the "
            "final verdict is not optional."
        )

    try:
        from sweep.families import FAMILIES
        from sweep.cross_sectional import SCORERS
        FAMILIES = dict(FAMILIES) | dict(SCORERS)
    except ImportError:
        FAMILIES = None
    if FAMILIES is not None:
        unknown = [f for f in doc["search_space"]["families"] if f not in FAMILIES]
        if unknown:
            fail(
                f"unknown strategy families: {unknown}. "
                f"Known: {sorted(FAMILIES)}. Declare the code identifier, and put "
                "prose in search_space.family_descriptions."
            )

    if "derived" in doc:
        fail("document already contains a 'derived' block — is it already frozen?")


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    directory = sys.argv[1].rstrip("/")
    src = os.path.join(directory, "preregistration.json")
    frozen_path = os.path.join(directory, "preregistration.frozen.json")
    hash_path = os.path.join(directory, "preregistration.sha256")

    if not os.path.exists(src):
        fail(f"{src} not found")
    if os.path.exists(frozen_path):
        fail(
            f"{frozen_path} already exists. A frozen pre-registration is "
            "never edited. Create a new sweep_id instead."
        )

    with open(src, encoding="utf-8") as fh:
        doc = json.load(fh)

    validate(doc)

    p = doc["planning"]
    n_trials = doc["search_space"]["n_trials"]
    t_obs = int(p["n_observations"])
    var_sr = float(p["assumed_var_trial_sharpes"])
    ppy = int(p["periods_per_year"])
    alpha = float(doc["decision_rule"]["alpha"])
    power = float(p["power"])
    skew = float(p.get("assumed_skewness", 0.0))
    kurt = float(p.get("assumed_kurtosis", 3.0))

    metric = doc["decision_rule"]["metric"]
    sr_null = expected_max_sharpe(n_trials, var_sr)
    mds = min_detectable_sharpe(n_trials, var_sr, t_obs, skew, kurt, alpha, power)

    if metric == "cross_sectional_residual_sharpe_z":
        nd = NormalDist()
        sd_null = float(p["assumed_null_residual_sharpe_sd"])
        z_thresh = float(doc["decision_rule"]["threshold"])
        mde = (z_thresh + nd.inv_cdf(power)) * sd_null
        doc["derived"] = {
            "assumed_null_sd": sd_null,
            "z_threshold": z_thresh,
            "min_detectable_residual_sharpe_annual": round(mde, 6),
            "note": (
                "Detection limit for the population test: the smallest TRUE "
                "mean market-neutral gross Sharpe, across the whole search "
                f"space, that this design could distinguish from shuffled data "
                f"with {int(power * 100)}% power. Says nothing about any "
                "individual variant."
            ),
        }
        digest = canonical_sha256(doc)
        with open(frozen_path, "wb") as fh:
            fh.write(canonical_bytes(doc))
        with open(hash_path, "w", encoding="utf-8") as fh:
            json.dump({"sweep_id": doc["sweep_id"],
                       "preregistration_sha256": digest}, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"frozen: {doc['sweep_id']} — {doc['title']}")
        print(f"  metric                 : {metric}")
        print(f"  trials in search space : {n_trials:,}")
        print(f"  observations           : {t_obs:,}")
        print(f"  assumed null sd        : {sd_null}")
        print(f"  DETECTION LIMIT        : {mde:.3f} mean residual Sharpe")
        print(f"  sha256                 : {digest}")
        print()
        print(f"  next: ots stamp {hash_path}")
        return

    doc["derived"] = {
        "expected_max_sharpe_under_null_per_obs": round(sr_null, 8),
        "expected_max_sharpe_under_null_annual": round(annualise(sr_null, ppy), 6),
        "min_detectable_sharpe_per_obs": round(mds, 8),
        "min_detectable_sharpe_annual": round(annualise(mds, ppy), 6),
        "note": (
            "Detection limit: the smallest TRUE annualised Sharpe this design "
            f"could find with {int(power * 100)}% power at alpha={alpha}. A null "
            "result from this sweep says nothing about edges smaller than this."
        ),
    }

    digest = canonical_sha256(doc)

    with open(frozen_path, "wb") as fh:
        fh.write(canonical_bytes(doc))

    with open(hash_path, "w", encoding="utf-8") as fh:
        json.dump(
            {"sweep_id": doc["sweep_id"], "preregistration_sha256": digest},
            fh,
            indent=2,
            sort_keys=True,
        )
        fh.write("\n")

    print(f"frozen: {doc['sweep_id']} — {doc['title']}")
    print(f"  trials in search space : {n_trials:,}")
    print(f"  observations           : {t_obs:,}")
    print(f"  E[max SR | null]       : {annualise(sr_null, ppy):.3f} annualised")
    print(f"  DETECTION LIMIT        : {annualise(mds, ppy):.3f} annualised Sharpe")
    print(f"  sha256                 : {digest}")
    print()
    print(f"  next: ots stamp {hash_path}")


if __name__ == "__main__":
    main()
