#!/usr/bin/env python3
"""JSON helpers for STACKIT Workflows API shell wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pick_key(value: object, dotted: str) -> object | None:
    current = value
    for part in dotted.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None
            current = current[part]
            continue
        if isinstance(current, list):
            if not part.isdigit():
                return None
            idx = int(part)
            if idx < 0 or idx >= len(current):
                return None
            current = current[idx]
            continue
        return None
    return current


def cmd_pick(args: argparse.Namespace) -> int:
    payload = _load_json(Path(args.json_file))
    if payload is None:
        print(args.default)
        return 0

    for key in args.keys:
        value = _pick_key(payload, key)
        if value is None:
            continue
        if isinstance(value, str):
            if value.strip() == "":
                continue
            print(value)
            return 0
        if isinstance(value, (int, float, bool)):
            print(str(value))
            return 0

    print(args.default)
    return 0


def _items_from_payload(payload: object) -> list[object]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("instances") or payload.get("data") or []
        return items if isinstance(items, list) else []
    return []


def cmd_count_status(args: argparse.Namespace) -> int:
    payload = _load_json(Path(args.json_file))
    if payload is None:
        print("0")
        return 0

    expected = args.expected_status.strip().lower()
    count = 0
    for item in _items_from_payload(payload):
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        if status is None and isinstance(item.get("state"), str):
            status = item.get("state")
        if isinstance(status, str) and status.strip().lower() == expected:
            count += 1

    print(str(count))
    return 0


def cmd_find_instance_id(args: argparse.Namespace) -> int:
    payload = _load_json(Path(args.json_file))
    if payload is None:
        print("")
        return 0

    for item in _items_from_payload(payload):
        if not isinstance(item, dict):
            continue
        actual_name = item.get("displayName") or item.get("name") or item.get("instanceName")
        if actual_name != args.display_name:
            continue
        for key in ("id", "instanceId", "instance_id"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                print(value)
                return 0

    print("")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    pick_parser = subparsers.add_parser("pick")
    pick_parser.add_argument("json_file")
    pick_parser.add_argument("default")
    pick_parser.add_argument("keys", nargs="+")
    pick_parser.set_defaults(func=cmd_pick)

    count_parser = subparsers.add_parser("count-status")
    count_parser.add_argument("json_file")
    count_parser.add_argument("expected_status")
    count_parser.set_defaults(func=cmd_count_status)

    find_parser = subparsers.add_parser("find-instance-id")
    find_parser.add_argument("json_file")
    find_parser.add_argument("display_name")
    find_parser.set_defaults(func=cmd_find_instance_id)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
