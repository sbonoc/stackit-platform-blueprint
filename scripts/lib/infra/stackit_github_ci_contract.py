#!/usr/bin/env python3
"""Read STACKIT GitHub CI contract lists for shell wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_KEYS = {"default_environments", "required_repository_secrets"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract_path")
    parser.add_argument("key", choices=sorted(ALLOWED_KEYS))
    args = parser.parse_args()

    payload = json.loads(Path(args.contract_path).read_text(encoding="utf-8"))
    values = payload.get(args.key, [])
    if not isinstance(values, list):
        return 0
    for value in values:
        print(str(value).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
