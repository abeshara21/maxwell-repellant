#!/usr/bin/env python3
"""Set behavior_label on a clip sidecar JSON (clawing | normal | unknown)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Label a captured clip for training")
    parser.add_argument("clip_json", type=Path, help="Path to clip_*.json sidecar")
    parser.add_argument(
        "label",
        choices=("clawing", "normal", "unknown"),
        help="Behavior class for this clip",
    )
    parser.add_argument("--notes", default="", help="Optional free-text note")
    args = parser.parse_args(argv)

    if not args.clip_json.exists():
        print(f"not found: {args.clip_json}", file=sys.stderr)
        return 1

    data = json.loads(args.clip_json.read_text(encoding="utf-8"))
    data["behavior_label"] = args.label
    if args.notes:
        data["notes"] = args.notes
    args.clip_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"labeled {args.clip_json.name} -> {args.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())