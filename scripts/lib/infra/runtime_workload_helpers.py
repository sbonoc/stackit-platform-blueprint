#!/usr/bin/env python3
"""Runtime workload helper utilities for app smoke shell wrapper."""

from __future__ import annotations

import json
import sys


def main() -> int:
    payload = json.load(sys.stdin)
    items = payload.get("items")
    if not isinstance(items, list):
        print("0")
        return 0
    print(len(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
