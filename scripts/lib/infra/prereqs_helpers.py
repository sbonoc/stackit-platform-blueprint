#!/usr/bin/env python3
"""Helper entrypoints for infra prereqs shell wrapper."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import zipfile


def cmd_extract_zip(args: argparse.Namespace) -> int:
    archive = Path(args.archive)
    destination = Path(args.destination)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(destination)
    return 0


def cmd_python_module_available(args: argparse.Namespace) -> int:
    return 0 if importlib.util.find_spec(args.module) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract-zip")
    extract_parser.add_argument("archive")
    extract_parser.add_argument("destination")
    extract_parser.set_defaults(func=cmd_extract_zip)

    module_parser = subparsers.add_parser("python-module-available")
    module_parser.add_argument("module")
    module_parser.set_defaults(func=cmd_python_module_available)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
