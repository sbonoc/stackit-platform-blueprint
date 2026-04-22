#!/usr/bin/env python3
"""Verify that app catalog artifacts reflect canonical version pin values.

Two modes:
  catalog-check   Compare tracked shell var values against catalog artifacts
                  (versions.lock and/or manifest.yaml). Called by audit_versions.sh.
  consistency     Verify that versions.lock and manifest.yaml agree with each other.
                  Called by smoke.sh when APP_CATALOG_SCAFFOLD_ENABLED=true.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# Shell var name → YAML key in manifest.yaml (under runtimePinnedVersions or
# frameworkPinnedVersions sections).
LOCK_VAR_TO_MANIFEST_KEY: dict[str, str] = {
    "PYTHON_RUNTIME_BASE_IMAGE_VERSION": "python",
    "NODE_RUNTIME_BASE_IMAGE_VERSION": "node",
    "NGINX_RUNTIME_BASE_IMAGE_VERSION": "nginx",
    "FASTAPI_VERSION": "fastapi",
    "PYDANTIC_VERSION": "pydantic",
    "VUE_VERSION": "vue",
    "VUE_ROUTER_VERSION": "vue_router",
    "PINIA_VERSION": "pinia",
}

# Ordered list of canonical tracked var names (matches audit_versions.sh tracked_vars).
TRACKED_VARS: tuple[str, ...] = tuple(LOCK_VAR_TO_MANIFEST_KEY.keys())


@dataclass(frozen=True)
class ContractCheckResult:
    check_id: str           # e.g. "lock:FASTAPI_VERSION" or "manifest:fastapi"
    file: str               # relative or absolute path string
    expected_snippet: str   # what should be present, e.g. "FASTAPI_VERSION=0.117.1"
    passed: bool
    detail: str             # actual value found or "not found" / "unreadable"


def parse_lock_file(lock_path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines from a versions.lock file.

    Returns an empty dict if the file is missing or unreadable.
    Lines that do not match KEY=VALUE are silently ignored.
    """
    if not lock_path.is_file():
        return {}
    try:
        text = lock_path.read_text(encoding="utf-8", errors="surrogateescape")
    except (OSError, UnicodeDecodeError):
        return {}
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            result[key.strip()] = value.strip()
    return result


def check_versions_lock(
    lock_path: Path,
    expected_vars: dict[str, str],
) -> list[ContractCheckResult]:
    """Verify that each expected var is present in the lock file with the correct value.

    Args:
        lock_path: Path to apps/catalog/versions.lock (may or may not exist).
        expected_vars: dict of {VAR_NAME: expected_value} from versions.sh.

    Returns one ContractCheckResult per var. If the file is missing, all checks
    are skipped (returned as skipped=passed=True with detail="file-not-present").
    """
    file_str = str(lock_path)
    if not lock_path.is_file():
        return [
            ContractCheckResult(
                check_id=f"lock:{var}",
                file=file_str,
                expected_snippet=f"{var}={value}",
                passed=True,
                detail="file-not-present",
            )
            for var, value in expected_vars.items()
        ]

    try:
        actual = parse_lock_file(lock_path)
    except Exception:  # noqa: BLE001
        return [
            ContractCheckResult(
                check_id=f"lock:{var}",
                file=file_str,
                expected_snippet=f"{var}={value}",
                passed=False,
                detail="unreadable",
            )
            for var, value in expected_vars.items()
        ]

    results: list[ContractCheckResult] = []
    for var, expected_value in expected_vars.items():
        actual_value = actual.get(var)
        if actual_value == expected_value:
            results.append(
                ContractCheckResult(
                    check_id=f"lock:{var}",
                    file=file_str,
                    expected_snippet=f"{var}={expected_value}",
                    passed=True,
                    detail=actual_value,
                )
            )
        else:
            results.append(
                ContractCheckResult(
                    check_id=f"lock:{var}",
                    file=file_str,
                    expected_snippet=f"{var}={expected_value}",
                    passed=False,
                    detail=actual_value if actual_value is not None else "not found",
                )
            )
    return results


def check_manifest_yaml(
    manifest_path: Path,
    expected_vars: dict[str, str],
) -> list[ContractCheckResult]:
    """Verify that each tracked var's version value appears under its canonical YAML key.

    Uses regex line-matching (no PyYAML dependency) against the known manifest schema.
    Pattern: ``^\\s+{yaml_key}:\\s+{expected_value}\\s*$``

    Args:
        manifest_path: Path to apps/catalog/manifest.yaml (may or may not exist).
        expected_vars: dict of {VAR_NAME: expected_value} from versions.sh.
                       Only vars with a LOCK_VAR_TO_MANIFEST_KEY entry are checked.

    Returns one ContractCheckResult per checked var. Vars with no YAML key mapping
    are silently skipped. If the file is missing, all checks are skipped (passed=True).
    """
    file_str = str(manifest_path)

    if not manifest_path.is_file():
        return [
            ContractCheckResult(
                check_id=f"manifest:{LOCK_VAR_TO_MANIFEST_KEY[var]}",
                file=file_str,
                expected_snippet=f"{LOCK_VAR_TO_MANIFEST_KEY[var]}: {value}",
                passed=True,
                detail="file-not-present",
            )
            for var, value in expected_vars.items()
            if var in LOCK_VAR_TO_MANIFEST_KEY
        ]

    try:
        manifest_text = manifest_path.read_text(encoding="utf-8", errors="surrogateescape")
    except (OSError, UnicodeDecodeError):
        return [
            ContractCheckResult(
                check_id=f"manifest:{LOCK_VAR_TO_MANIFEST_KEY[var]}",
                file=file_str,
                expected_snippet=f"{LOCK_VAR_TO_MANIFEST_KEY[var]}: {value}",
                passed=False,
                detail="unreadable",
            )
            for var, value in expected_vars.items()
            if var in LOCK_VAR_TO_MANIFEST_KEY
        ]

    results: list[ContractCheckResult] = []
    for var, expected_value in expected_vars.items():
        yaml_key = LOCK_VAR_TO_MANIFEST_KEY.get(var)
        if yaml_key is None:
            continue
        pattern = re.compile(
            rf"^\s+{re.escape(yaml_key)}:\s+{re.escape(expected_value)}\s*$",
            re.MULTILINE,
        )
        expected_snippet = f"{yaml_key}: {expected_value}"
        if pattern.search(manifest_text):
            results.append(
                ContractCheckResult(
                    check_id=f"manifest:{yaml_key}",
                    file=file_str,
                    expected_snippet=expected_snippet,
                    passed=True,
                    detail=expected_value,
                )
            )
        else:
            # Extract actual value from manifest for diagnostics
            actual_pattern = re.compile(
                rf"^\s+{re.escape(yaml_key)}:\s+(.+?)\s*$",
                re.MULTILINE,
            )
            actual_match = actual_pattern.search(manifest_text)
            detail = actual_match.group(1) if actual_match else "not found"
            results.append(
                ContractCheckResult(
                    check_id=f"manifest:{yaml_key}",
                    file=file_str,
                    expected_snippet=expected_snippet,
                    passed=False,
                    detail=detail,
                )
            )
    return results


def check_catalog_consistency(
    lock_path: Path,
    manifest_path: Path,
) -> list[ContractCheckResult]:
    """Verify that versions.lock and manifest.yaml agree on all mapped version pins.

    Parses the lock file to get expected values, then checks each against the manifest.
    Used by smoke.sh to validate catalog coherence without sourcing versions.sh.

    Both files must exist; if either is missing, one failing result is returned.
    """
    lock_file_str = str(lock_path)
    manifest_file_str = str(manifest_path)

    if not lock_path.is_file():
        return [
            ContractCheckResult(
                check_id="consistency:lock-missing",
                file=lock_file_str,
                expected_snippet="versions.lock must exist for consistency check",
                passed=False,
                detail="file-not-present",
            )
        ]

    if not manifest_path.is_file():
        return [
            ContractCheckResult(
                check_id="consistency:manifest-missing",
                file=manifest_file_str,
                expected_snippet="manifest.yaml must exist for consistency check",
                passed=False,
                detail="file-not-present",
            )
        ]

    lock_vars = parse_lock_file(lock_path)
    # Filter to only the vars that have a manifest key mapping
    expected_vars = {
        var: lock_vars[var]
        for var in LOCK_VAR_TO_MANIFEST_KEY
        if var in lock_vars
    }
    if not expected_vars:
        return [
            ContractCheckResult(
                check_id="consistency:no-tracked-vars",
                file=lock_file_str,
                expected_snippet="at least one tracked var must be present in versions.lock",
                passed=False,
                detail="no tracked vars found in lock file",
            )
        ]

    return check_manifest_yaml(manifest_path, expected_vars)


def _print_report(results: list[ContractCheckResult], mode: str) -> None:
    """Print a human-readable contract check report to stdout."""
    failed = [r for r in results if not r.passed]
    passed = [r for r in results if r.passed]

    print(f"\n[version-contract-check] mode={mode} checks={len(results)} failed={len(failed)}")
    if not results:
        print("  No checks ran.")
        return

    skipped = [r for r in passed if r.detail in ("file-not-present",)]
    effective_passed = [r for r in passed if r.detail not in ("file-not-present",)]

    if effective_passed:
        for r in effective_passed:
            print(f"  PASS  {r.check_id}  ({r.file}): {r.expected_snippet}")
    if skipped:
        print(f"  SKIP  {len(skipped)} check(s) — catalog file(s) not present")
    for r in failed:
        print(f"  FAIL  {r.check_id}  ({r.file})")
        print(f"        expected: {r.expected_snippet}")
        print(f"        actual:   {r.detail}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["catalog-check", "consistency"],
        required=True,
        help="catalog-check: compare shell vars against catalog files; "
             "consistency: verify lock and manifest agree",
    )
    parser.add_argument("--versions-lock", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument(
        "--var",
        action="append",
        dest="vars",
        default=[],
        metavar="NAME=VALUE",
        help="Expected var (catalog-check mode only); may be repeated",
    )
    args = parser.parse_args()

    if args.mode == "catalog-check":
        if not args.vars:
            print("[version-contract-check] catalog-check mode requires at least one --var", file=sys.stderr)
            return 1

        expected_vars: dict[str, str] = {}
        for entry in args.vars:
            if "=" not in entry:
                print(f"[version-contract-check] invalid --var format (expected NAME=VALUE): {entry!r}", file=sys.stderr)
                return 1
            name, _, value = entry.partition("=")
            expected_vars[name.strip()] = value.strip()

        results: list[ContractCheckResult] = []
        if args.versions_lock is not None:
            results.extend(check_versions_lock(args.versions_lock, expected_vars))
        if args.manifest is not None:
            results.extend(check_manifest_yaml(args.manifest, expected_vars))

        _print_report(results, "catalog-check")
        failed = [r for r in results if not r.passed]
        return 1 if failed else 0

    else:  # consistency
        if args.versions_lock is None or args.manifest is None:
            print("[version-contract-check] consistency mode requires --versions-lock and --manifest", file=sys.stderr)
            return 1

        results = check_catalog_consistency(args.versions_lock, args.manifest)
        _print_report(results, "consistency")
        failed = [r for r in results if not r.passed]
        return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
