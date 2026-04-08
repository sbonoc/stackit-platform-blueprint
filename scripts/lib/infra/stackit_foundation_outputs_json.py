#!/usr/bin/env python3
"""Helpers to resolve STACKIT foundation Terraform outputs from JSON payload."""

from __future__ import annotations

import argparse
import json
import os


def _load_payload() -> dict[str, object]:
    payload_raw = os.environ.get("STACKIT_FOUNDATION_OUTPUTS_JSON", "")
    payload = json.loads(payload_raw)
    if not isinstance(payload, dict):
        raise ValueError("outputs payload must be a mapping")
    return payload


def _render_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    raise ValueError("output value must be scalar")


def cmd_value(args: argparse.Namespace) -> int:
    payload = _load_payload()
    entry = payload.get(args.output_name)
    if not isinstance(entry, dict) or entry.get("value") is None:
        return 1
    try:
        print(_render_scalar(entry["value"]))
    except ValueError:
        return 1
    return 0


def cmd_map_value(args: argparse.Namespace) -> int:
    payload = _load_payload()
    entry = payload.get(args.output_name)
    if not isinstance(entry, dict) or not isinstance(entry.get("value"), dict):
        return 1
    value = entry["value"].get(args.map_key)
    if value is None:
        return 1
    try:
        print(_render_scalar(value))
    except ValueError:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    value_parser = subparsers.add_parser("value")
    value_parser.add_argument("output_name")
    value_parser.set_defaults(func=cmd_value)

    map_parser = subparsers.add_parser("map-value")
    map_parser.add_argument("output_name")
    map_parser.add_argument("map_key")
    map_parser.set_defaults(func=cmd_map_value)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
