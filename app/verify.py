"""Verification layer: the chain of records and their Bitcoin anchors.

WHAT THIS IS AND IS NOT

It is not a new blockchain. A chain where only I run a node proves nothing —
I could rewrite it at any moment, so its security is exactly zero. What the
records are anchored to is Bitcoin itself, via OpenTimestamps: to forge a
date you would have to rewrite Bitcoin's history.

What this module adds on top is the missing half. Each record already has its
own hash and its own timestamp proof, but nothing ties record N to record
N-1. That means a record could be deleted quietly and the remaining ones
would still verify individually — which is precisely the failure mode a
registry of negative results has to rule out, because the temptation is
always to delete the inconvenient ones.

So each entry's chain hash covers the previous entry's chain hash. Remove or
alter anything and every later link breaks visibly.

    chain[0] = sha256("sweep-registry-genesis")
    chain[i] = sha256(chain[i-1] + sweep_id + preregistration_sha256)
"""
from __future__ import annotations

import hashlib
import json
import os
import struct

GENESIS = hashlib.sha256(b"sweep-registry-genesis").hexdigest()

# OpenTimestamps binary format markers. The full spec is a tree of operations;
# we only need enough to answer "is this anchored yet, and to which block".
_OTS_MAGIC = bytes.fromhex("004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294")
_ATTEST_BITCOIN = bytes.fromhex("0588960d73d71901")
_ATTEST_PENDING = bytes.fromhex("83dfe30d2ef90c8e")


def read_varuint(data: bytes, pos: int):
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
    return result, pos


def parse_ots(path: str) -> dict:
    """Extract anchor status from a .ots proof.

    Returns confirmed block height when the proof has been upgraded, or the
    calendar URLs it is still pending on. Deliberately tolerant: a proof we
    cannot parse is reported as unknown rather than treated as invalid, since
    the format has more operation types than are worth implementing here.
    """
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return {"status": "missing"}

    if not data.startswith(_OTS_MAGIC[:31]):
        return {"status": "unrecognised", "bytes": len(data)}

    heights = []
    calendars = []

    pos = 0
    while True:
        idx = data.find(_ATTEST_BITCOIN, pos)
        if idx < 0:
            break
        p = idx + len(_ATTEST_BITCOIN)
        _payload_len, p = read_varuint(data, p)
        height, p = read_varuint(data, p)
        heights.append(height)
        pos = idx + 1

    pos = 0
    while True:
        idx = data.find(_ATTEST_PENDING, pos)
        if idx < 0:
            break
        p = idx + len(_ATTEST_PENDING)
        _payload_len, p = read_varuint(data, p)
        url_len, p = read_varuint(data, p)
        url = data[p:p + url_len].decode("utf-8", "replace")
        if url.startswith("http"):
            calendars.append(url)
        pos = idx + 1

    if heights:
        return {"status": "confirmed", "block_height": min(heights),
                "bytes": len(data)}
    if calendars:
        return {"status": "pending", "calendars": sorted(set(calendars)),
                "bytes": len(data)}
    return {"status": "unknown", "bytes": len(data)}


def file_sha256(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def build_chain(root: str) -> list[dict]:
    """Walk every record in id order and link them into a verifiable chain."""
    sweeps_dir = os.path.join(root, "sweeps")
    if not os.path.isdir(sweeps_dir):
        return []

    entries = []
    prev = GENESIS

    for sid in sorted(os.listdir(sweeps_dir)):
        d = os.path.join(sweeps_dir, sid)
        hash_path = os.path.join(d, "preregistration.sha256")
        frozen_path = os.path.join(d, "preregistration.frozen.json")
        if not os.path.exists(hash_path):
            continue

        try:
            with open(hash_path, encoding="utf-8") as fh:
                stored = json.load(fh)["preregistration_sha256"]
        except Exception:
            continue

        # Recompute from the frozen document. If this disagrees with the
        # stored hash the record has been altered since it was sealed, which
        # voids it — and saying so loudly is the entire point.
        recomputed = None
        matches = None
        if os.path.exists(frozen_path):
            try:
                import sys
                sys.path.insert(0, root)
                from srlab.canonical import canonical_sha256
                with open(frozen_path, encoding="utf-8") as fh:
                    recomputed = canonical_sha256(json.load(fh))
                matches = (recomputed == stored)
            except Exception:
                recomputed = None

        ots_path = hash_path + ".ots"
        anchor = parse_ots(ots_path) if os.path.exists(ots_path) else {"status": "none"}

        link = hashlib.sha256(
            (prev + sid + stored).encode("utf-8")).hexdigest()

        title = None
        n_trials = None
        if os.path.exists(frozen_path):
            try:
                with open(frozen_path, encoding="utf-8") as fh:
                    doc = json.load(fh)
                title = doc.get("title")
                n_trials = doc.get("search_space", {}).get("n_trials")
            except Exception:
                pass

        mtime = os.path.getmtime(hash_path)

        entries.append({
            "index": len(entries),
            "sweep_id": sid,
            "title": title,
            "n_trials": n_trials,
            "prereg_sha256": stored,
            "recomputed_sha256": recomputed,
            "intact": matches,
            "prev_link": prev,
            "chain_hash": link,
            "anchor": anchor,
            "ots_sha256": file_sha256(ots_path) if os.path.exists(ots_path) else None,
            "sealed_at": mtime,
        })
        prev = link

    return entries


def chain_summary(entries: list[dict]) -> dict:
    confirmed = [e for e in entries if e["anchor"].get("status") == "confirmed"]
    pending = [e for e in entries if e["anchor"].get("status") == "pending"]
    broken = [e for e in entries if e["intact"] is False]
    heights = [e["anchor"]["block_height"] for e in confirmed
               if "block_height" in e["anchor"]]
    return {
        "length": len(entries),
        "head": entries[-1]["chain_hash"] if entries else GENESIS,
        "genesis": GENESIS,
        "confirmed": len(confirmed),
        "pending": len(pending),
        "unanchored": len(entries) - len(confirmed) - len(pending),
        "broken": len(broken),
        "first_block": min(heights) if heights else None,
        "last_block": max(heights) if heights else None,
    }
