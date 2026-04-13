#!/usr/bin/env python3
"""Helpers for runtime ESO target secret JSON verification."""

from __future__ import annotations

import argparse
import json
import sys


def _parse_json_candidate(candidate: str) -> dict[str, object] | None:
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _parse_secret_payload(raw_payload: str) -> dict[str, object] | None:
    payload = _parse_json_candidate(raw_payload)
    if payload is not None:
        return payload

    compact = raw_payload.strip()
    start = compact.find("{")
    end = compact.rfind("}")
    if start == -1 or end <= start:
        return None
    return _parse_json_candidate(compact[start : end + 1])


def cmd_verify_required_keys(args: argparse.Namespace) -> int:
    raw_payload = sys.stdin.read()
    if raw_payload.strip() == "":
        print("__verify_error__:empty-secret-json")
        return 2

    payload = _parse_secret_payload(raw_payload)
    if payload is None:
        print("__verify_error__:invalid-secret-json")
        return 2

    data = payload.get("data")
    if not isinstance(data, dict):
        print("__verify_error__:missing-secret-data-map")
        return 2

    keys = [item.strip() for item in args.keys_csv.split(",") if item.strip()]
    missing: list[str] = []
    for key in keys:
        value = data.get(key)
        if value is None or str(value).strip() == "":
            missing.append(key)

    if missing:
        print(" ".join(missing))
        return 1

    print("ok")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify-required-keys")
    verify_parser.add_argument("keys_csv")
    verify_parser.set_defaults(func=cmd_verify_required_keys)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
