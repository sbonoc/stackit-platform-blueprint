#!/usr/bin/env python3
"""Validate repository test-pyramid ratios against the canonical contract."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = REPO_ROOT / "scripts/lib/quality/test_pyramid_contract.json"
SCOPES = ("unit", "integration", "e2e")


def count_tests_in_file(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    )


def load_contract(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_file_scopes(repo_root: Path, contract: dict[str, object]) -> dict[Path, str]:
    classifications = contract.get("classifications", [])
    if not isinstance(classifications, list):
        raise ValueError("classifications must be a list")

    test_files = sorted(path for path in (repo_root / "tests").rglob("test_*.py") if path.is_file())
    file_scopes: dict[Path, str] = {}
    duplicates: list[str] = []

    for entry in classifications:
        if not isinstance(entry, dict):
            raise ValueError("classification entry must be an object")
        scope = str(entry.get("scope", ""))
        if scope not in SCOPES:
            raise ValueError(f"unsupported scope in contract: {scope}")
        patterns = entry.get("patterns", [])
        if not isinstance(patterns, list):
            raise ValueError(f"patterns for scope {scope} must be a list")

        for pattern in patterns:
            for matched in repo_root.glob(str(pattern)):
                if not matched.is_file():
                    continue
                if matched in file_scopes and file_scopes[matched] != scope:
                    duplicates.append(str(matched.relative_to(repo_root)))
                    continue
                file_scopes[matched] = scope

    if duplicates:
        raise ValueError("test files classified in multiple scopes: " + ", ".join(sorted(set(duplicates))))

    uncategorized = [str(path.relative_to(repo_root)) for path in test_files if path not in file_scopes]
    if uncategorized:
        raise ValueError("uncategorized test files: " + ", ".join(uncategorized))

    return file_scopes


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate repository test-pyramid ratios.")
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=DEFAULT_CONTRACT,
        help="Path to the test-pyramid contract JSON file.",
    )
    args = parser.parse_args()

    try:
        contract_path = args.contract_path.resolve()
        contract = load_contract(contract_path)
        file_scopes = resolve_file_scopes(REPO_ROOT, contract)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    counts = {scope: 0 for scope in SCOPES}
    for path, scope in sorted(file_scopes.items()):
        counts[scope] += count_tests_in_file(path)

    total = sum(counts.values())
    if total == 0:
        print("no tests found in classified scopes", file=sys.stderr)
        return 1

    thresholds = contract.get("thresholds", {})
    if not isinstance(thresholds, dict):
        raise ValueError("thresholds must be an object")
    unit_min = float(thresholds["unit_min_exclusive"])
    integration_max = float(thresholds["integration_max_inclusive"])
    e2e_max = float(thresholds["e2e_max_inclusive"])

    unit_ratio = counts["unit"] / total
    integration_ratio = counts["integration"] / total
    e2e_ratio = counts["e2e"] / total

    print("[test-pyramid] scope counts")
    for scope in SCOPES:
        print(f"  - {scope:11s} {counts[scope]:>4d}")
    print(f"[test-pyramid] total tests: {total}")
    print(
        "[test-pyramid] ratios "
        f"unit={format_percent(unit_ratio)} "
        f"integration={format_percent(integration_ratio)} "
        f"e2e={format_percent(e2e_ratio)}"
    )

    failures: list[str] = []
    if unit_ratio <= unit_min:
        failures.append(f"unit ratio must be > {format_percent(unit_min)}")
    if integration_ratio > integration_max:
        failures.append(f"integration ratio must be <= {format_percent(integration_max)}")
    if e2e_ratio > e2e_max:
        failures.append(f"e2e ratio must be <= {format_percent(e2e_max)}")

    if failures:
        print("[test-pyramid] ERROR:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("[test-pyramid] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
