"""Stage 1 pre-flight checks for the scripted upgrade pipeline.

Called by scripts/bin/blueprint/upgrade_consumer_pipeline.sh before any
mutation begins. Each check returns a PreflightResult; the entry wrapper
aborts on the first failure.

Requirements: FR-001 (dirty tree), FR-002 (invalid ref), FR-003 (bad contract).
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class PreflightResult:
    success: bool
    message: str

    def as_dict(self) -> dict:
        return {"success": self.success, "message": self.message}


def check_clean_working_tree(repo_root: Path) -> PreflightResult:
    """FR-001: Abort if the working tree has any unstaged, staged, or untracked changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    if result.returncode != 0:
        return PreflightResult(
            success=False,
            message=f"Working tree is not clean: git status failed: {result.stderr.strip()}",
        )
    dirty = result.stdout.strip()
    if dirty:
        return PreflightResult(
            success=False,
            message=(
                "Working tree is not clean. Commit or stash all changes before running the "
                f"upgrade pipeline.\n{dirty}"
            ),
        )
    return PreflightResult(success=True, message="Working tree is clean.")


def check_upgrade_ref(*, upgrade_ref: str, upgrade_source: str) -> PreflightResult:
    """FR-002: Abort if BLUEPRINT_UPGRADE_REF is unset or does not resolve in BLUEPRINT_UPGRADE_SOURCE."""
    if not upgrade_ref:
        return PreflightResult(
            success=False,
            message="BLUEPRINT_UPGRADE_REF is not set. Export it before running the upgrade pipeline.",
        )
    if not upgrade_source:
        return PreflightResult(
            success=False,
            message="BLUEPRINT_UPGRADE_SOURCE is not set. Export it before running the upgrade pipeline.",
        )
    # For local paths, verify the directory exists before shelling out.
    source_path = Path(upgrade_source)
    if source_path.is_absolute() and not source_path.exists():
        return PreflightResult(
            success=False,
            message=(
                f"BLUEPRINT_UPGRADE_SOURCE={upgrade_source!r} does not exist on disk. "
                "Verify the path is correct."
            ),
        )
    result = subprocess.run(
        ["git", "cat-file", "-t", upgrade_ref],
        capture_output=True,
        text=True,
        cwd=upgrade_source,
    )
    if result.returncode != 0:
        return PreflightResult(
            success=False,
            message=(
                f"BLUEPRINT_UPGRADE_REF={upgrade_ref!r} does not resolve in "
                f"BLUEPRINT_UPGRADE_SOURCE={upgrade_source!r}. "
                "Verify the ref is correct and the source repository is accessible."
            ),
        )
    obj_type = result.stdout.strip()
    return PreflightResult(
        success=True,
        message=f"BLUEPRINT_UPGRADE_REF={upgrade_ref!r} resolves to a {obj_type} in the upgrade source.",
    )


def check_contract(repo_root: Path) -> PreflightResult:
    """FR-003: Abort if blueprint/contract.yaml is absent, unparseable, or not a generated-consumer repo."""
    contract_path = repo_root / "blueprint" / "contract.yaml"
    if not contract_path.exists():
        return PreflightResult(
            success=False,
            message="blueprint/contract.yaml is absent. The upgrade pipeline requires a generated-consumer repository.",
        )
    try:
        with contract_path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception as exc:
        return PreflightResult(
            success=False,
            message=f"blueprint/contract.yaml is not parseable: {exc}",
        )
    repo_mode = (
        (data or {})
        .get("spec", {})
        .get("repository", {})
        .get("repo_mode", "")
    )
    if repo_mode != "generated-consumer":
        return PreflightResult(
            success=False,
            message=(
                f"blueprint/contract.yaml has repo_mode={repo_mode!r}; "
                "expected 'generated-consumer'. The pipeline only operates on consumer repositories."
            ),
        )
    return PreflightResult(success=True, message="blueprint/contract.yaml is valid.")


def run_pipeline_preflight(
    repo_root: Path,
    *,
    upgrade_ref: str,
    upgrade_source: str,
) -> list[PreflightResult]:
    """Run all pre-flight checks and return results in order.

    The entry wrapper should abort on the first unsuccessful result.
    """
    return [
        check_clean_working_tree(repo_root),
        check_upgrade_ref(upgrade_ref=upgrade_ref, upgrade_source=upgrade_source),
        check_contract(repo_root),
    ]


def main() -> int:
    """CLI entry point for upgrade_consumer_pipeline.sh Stage 1."""
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Stage 1 pre-flight checks for the scripted upgrade pipeline.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    upgrade_ref = os.environ.get("BLUEPRINT_UPGRADE_REF", "")
    upgrade_source = os.environ.get("BLUEPRINT_UPGRADE_SOURCE", "")

    results = run_pipeline_preflight(
        args.repo_root,
        upgrade_ref=upgrade_ref,
        upgrade_source=upgrade_source,
    )
    for r in results:
        if not r.success:
            print(f"[PIPELINE] Pre-flight FAILED: {r.message}", file=sys.stderr)
            return 1
    print("[PIPELINE] Pre-flight: all checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
