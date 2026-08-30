#!/usr/bin/env python3
"""Attach notes to a finished record without touching what was frozen.

    python annotate.py sweeps/SW-0002 --note "..." --exploratory "..."
    python annotate.py sweeps/SW-0029 --status VOID --reason "..."
    python annotate.py sweeps/SW-0002 --rebuild

Everything written here lands in `annotations.json` and is rendered into
RECORD.md under headings that mark it as added after the fact. The frozen
pre-registration, its hash and result.json are never modified — if they
were, the timestamp would prove nothing.

The separation this enforces is the whole point of the registry:

  CONFIRMATORY  what the frozen document said would be tested, and the
                verdict the pre-registered rule produced
  EXPLORATORY   anything noticed by looking at the finished result

Both belong in the record. Presenting the second as the first is the exact
practice this project exists to document in other people.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

STATUSES = {"OK", "VOID", "SUPERSEDED", "INCONCLUSIVE"}


def load(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def render(d: str) -> None:
    """Rewrite RECORD.md from result.json plus annotations."""
    ann = load(os.path.join(d, "annotations.json"))
    if not ann:
        return

    record_path = os.path.join(d, "RECORD.md")
    if not os.path.exists(record_path):
        print(f"  no RECORD.md in {d} — nothing to render into", file=sys.stderr)
        return

    with open(record_path, encoding="utf-8") as fh:
        body = fh.read()

    marker = "\n<!-- annotations -->\n"
    body = body.split(marker)[0].rstrip() + "\n"

    parts = [marker]

    status = ann.get("status", "OK")
    if status != "OK":
        parts.append(f"\n## Status: {status}\n")
        if ann.get("reason"):
            parts.append(f"\n{ann['reason']}\n")

    if ann.get("confirmatory"):
        parts.append("\n## What was pre-registered\n")
        for n in ann["confirmatory"]:
            parts.append(f"\n{n}\n")

    if ann.get("exploratory"):
        parts.append("\n## Exploratory — NOT pre-registered\n")
        parts.append(
            "\nEverything in this section was noticed by looking at the "
            "finished result. It is a hypothesis, not a finding, and it "
            "carries no multiple-testing correction of its own.\n"
        )
        for n in ann["exploratory"]:
            parts.append(f"\n{n}\n")

    if ann.get("notes"):
        parts.append("\n## Notes\n")
        for n in ann["notes"]:
            parts.append(f"\n- {n}\n")

    if ann.get("supersedes") or ann.get("superseded_by"):
        parts.append("\n## Related records\n")
        for s in ann.get("supersedes", []):
            parts.append(f"\n- Supersedes {s}\n")
        for s in ann.get("superseded_by", []):
            parts.append(f"\n- Superseded by {s}\n")

    parts.append(
        f"\n---\n\n*Annotations added {ann.get('updated_utc', '')}. "
        "The frozen pre-registration, its hash and result.json are "
        "unmodified.*\n"
    )

    with open(record_path, "w", encoding="utf-8") as fh:
        fh.write(body + "".join(parts))
    print(f"  rendered {record_path}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sweep_dir")
    ap.add_argument("--status", choices=sorted(STATUSES))
    ap.add_argument("--reason")
    ap.add_argument("--note", action="append", default=[])
    ap.add_argument("--confirmatory", action="append", default=[])
    ap.add_argument("--exploratory", action="append", default=[])
    ap.add_argument("--supersedes", action="append", default=[])
    ap.add_argument("--superseded-by", action="append", default=[])
    ap.add_argument("--rebuild", action="store_true",
                    help="re-render RECORD.md from existing annotations")
    args = ap.parse_args()

    d = args.sweep_dir.rstrip("/")
    if not os.path.isdir(d):
        sys.exit(f"{d} not found")

    path = os.path.join(d, "annotations.json")
    ann = load(path)

    if args.rebuild:
        render(d)
        return

    if args.status:
        ann["status"] = args.status
    if args.reason:
        ann["reason"] = args.reason
    for key, vals in (("notes", args.note),
                      ("confirmatory", args.confirmatory),
                      ("exploratory", args.exploratory),
                      ("supersedes", args.supersedes),
                      ("superseded_by", args.superseded_by)):
        if vals:
            ann.setdefault(key, []).extend(vals)

    ann["updated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ann, fh, indent=2, ensure_ascii=False)
    print(f"  wrote {path}")
    render(d)


if __name__ == "__main__":
    main()
