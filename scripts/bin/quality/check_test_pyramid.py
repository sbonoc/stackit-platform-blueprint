#!/usr/bin/env python3
"""Validate repository test-pyramid ratios against the canonical contract.

Classification contract: scripts/lib/quality/test_pyramid_contract.json

Every test_*.py file under tests/ must appear in exactly one scope bucket
(unit, integration, e2e).  The script fails with a clear error message and
a non-zero exit code when:
  - any test file is not listed in the contract (classification gap), OR
  - the unit/integration/e2e ratio thresholds are violated.

Exit codes:
  0 — all files classified, all ratios within thresholds
  1 — classification gap or ratio violation (details printed to stderr)

Blueprint metric emitted on exit:
  [METRIC] name=test_pyramid_check files=N tests=N unit=N integration=N e2e=N status=success|failure
"""

from __future__ import annotations

import argparse
import ast
import datetime
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402

DEFAULT_CONTRACT = REPO_ROOT / "scripts/lib/quality/test_pyramid_contract.json"
SCOPES = ("unit", "integration", "e2e")

# Blueprint logging format mirrors scripts/lib/shell/logging.sh conventions so
# [METRIC] lines appear consistently alongside shell-emitted metrics in CI logs.
_LOG_NAMESPACE = "blueprint"


def _now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log_metric(name: str, value: int, labels: dict[str, str | int]) -> None:
    """Emit a structured metric line compatible with blueprint log format."""
    label_str = " ".join(f"{k}={v}" for k, v in labels.items())
    print(f"[{_now_utc()}] [{_LOG_NAMESPACE}] [METRIC] name={name} value={value} {label_str}")


def count_tests_in_file(path: Path) -> int:
    """Count test functions (test_*) in a Python file using AST parsing."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def load_contract(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_file_scopes(repo_root: Path, contract: dict[str, object]) -> dict[Path, str]:
    """Map every classified test file to its declared scope.

    Raises ValueError when:
    - a file appears in more than one scope bucket (duplicate),
    - any test_*.py file under tests/ is not listed in any scope bucket (gap).
    """
    classifications = contract.get("classifications", [])
    if not isinstance(classifications, list):
        raise ValueError("classifications must be a list")

    # Collect all physical test files in the repo tree.
    test_files = sorted(
        path for path in (repo_root / "tests").rglob("test_*.py") if path.is_file()
    )

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
        raise ValueError(
            "test files classified in multiple scopes: " + ", ".join(sorted(set(duplicates)))
        )

    # Any file present on disk but not matched by any pattern is a classification gap.
    uncategorized = [
        str(path.relative_to(repo_root)) for path in test_files if path not in file_scopes
    ]
    if uncategorized:
        raise ValueError(
            "uncategorized test files: "
            + ", ".join(uncategorized)
            + " (update scripts/lib/quality/test_pyramid_contract.json classifications)"
        )

    return file_scopes


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=DEFAULT_CONTRACT,
        help="Path to the test-pyramid contract JSON file.",
    )
    args = parser.parse_args()

    # Track counts for the final metric even on failure paths.
    file_counts: dict[str, int] = {s: 0 for s in SCOPES}
    test_counts: dict[str, int] = {s: 0 for s in SCOPES}

    try:
        contract_path = args.contract_path.resolve()
        contract = load_contract(contract_path)
        blueprint_contract = load_blueprint_contract(REPO_ROOT / "blueprint/contract.yaml")
        if blueprint_contract.repository.repo_mode == "generated-consumer":
            print("[test-pyramid] skipped for generated-consumer repo")
            return 0

        file_scopes = resolve_file_scopes(REPO_ROOT, contract)

    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        _log_metric(
            "test_pyramid_check",
            0,
            {**{f"{s}_files": 0 for s in SCOPES}, **{f"{s}_tests": 0 for s in SCOPES}, "status": "failure"},
        )
        return 1

    # Count classified files and tests per scope.
    for path, scope in sorted(file_scopes.items()):
        file_counts[scope] += 1
        test_counts[scope] += count_tests_in_file(path)

    total_files = sum(file_counts.values())
    total_tests = sum(test_counts.values())

    # Per-scope summary (files + tests).
    print("[test-pyramid] scope breakdown")
    for scope in SCOPES:
        print(
            f"  - {scope:11s}  files={file_counts[scope]:>3d}  tests={test_counts[scope]:>4d}"
        )
    print(f"[test-pyramid] total  files={total_files}  tests={total_tests}")

    if total_tests == 0:
        print("no tests found in classified scopes", file=sys.stderr)
        _log_metric(
            "test_pyramid_check",
            0,
            {**{f"{s}_files": file_counts[s] for s in SCOPES}, **{f"{s}_tests": 0 for s in SCOPES}, "status": "failure"},
        )
        return 1

    thresholds = contract.get("thresholds", {})
    if not isinstance(thresholds, dict):
        raise ValueError("thresholds must be an object")
    unit_min = float(thresholds["unit_min_exclusive"])
    integration_max = float(thresholds["integration_max_inclusive"])
    e2e_max = float(thresholds["e2e_max_inclusive"])

    unit_ratio = test_counts["unit"] / total_tests
    integration_ratio = test_counts["integration"] / total_tests
    e2e_ratio = test_counts["e2e"] / total_tests

    print(
        f"[test-pyramid] ratios "
        f"unit={format_percent(unit_ratio)} (min>{format_percent(unit_min)}) "
        f"integration={format_percent(integration_ratio)} (max<={format_percent(integration_max)}) "
        f"e2e={format_percent(e2e_ratio)} (max<={format_percent(e2e_max)})"
    )

    failures: list[str] = []
    if unit_ratio <= unit_min:
        failures.append(
            f"unit ratio {format_percent(unit_ratio)} must be > {format_percent(unit_min)}"
        )
    if integration_ratio > integration_max:
        failures.append(
            f"integration ratio {format_percent(integration_ratio)} must be <= {format_percent(integration_max)}"
        )
    if e2e_ratio > e2e_max:
        failures.append(
            f"e2e ratio {format_percent(e2e_ratio)} must be <= {format_percent(e2e_max)}"
        )

    metric_labels: dict[str, str | int] = {
        "files": total_files,
        **{f"{s}_files": file_counts[s] for s in SCOPES},
        "tests": total_tests,
        **{f"{s}_tests": test_counts[s] for s in SCOPES},
        "status": "failure" if failures else "success",
    }

    if failures:
        print("[test-pyramid] ratio violations:")
        for failure in failures:
            print(f"  - {failure}")
        _log_metric("test_pyramid_check", 0, metric_labels)
        return 1

    print("[test-pyramid] OK")
    _log_metric("test_pyramid_check", 1, metric_labels)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
