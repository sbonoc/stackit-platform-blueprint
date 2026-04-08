#!/usr/bin/env python3
"""Discover pnpm package script lanes deterministically."""

from __future__ import annotations

import json
import os
import pathlib
import sys


EXCLUDED_DIRS = {
    "node_modules",
    ".pnpm",
    ".git",
    ".turbo",
    ".next",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
}


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "usage: pnpm_script_discovery.py <root_path> <script_name> [<script_name> ...]",
            file=sys.stderr,
        )
        return 2

    root_path = pathlib.Path(sys.argv[1])
    script_candidates = sys.argv[2:]

    for current_root, dirs, files in os.walk(root_path, topdown=True):
        dirs[:] = sorted([directory for directory in dirs if directory not in EXCLUDED_DIRS])
        if "package.json" not in files:
            continue

        package_json = pathlib.Path(current_root) / "package.json"
        try:
            payload = json.loads(package_json.read_text(encoding="utf-8"))
        except Exception:
            continue

        scripts = payload.get("scripts")
        if not isinstance(scripts, dict):
            continue

        selected_script = ""
        for script_candidate in script_candidates:
            if isinstance(scripts.get(script_candidate), str):
                selected_script = script_candidate
                break

        if selected_script:
            print(f"{package_json.parent}\t{selected_script}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
