"""Stage 5: Coverage gap detection and file fetch for the scripted upgrade pipeline.

Compares files referenced in blueprint/contract.yaml against files on disk.
For each referenced file that is absent, attempts to fetch it from the
already-cloned local BLUEPRINT_UPGRADE_SOURCE repository using `git show`.

No external HTTP fetches are performed (NFR-SEC-001).

Requirements: FR-009 (gap detection), FR-010 (local git fetch), NFR-SEC-001.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CoverageFetchResult:
    success: bool
    message: str
    gaps_detected: list[str] = field(default_factory=list)
    fetched_paths: list[str] = field(default_factory=list)
    unfetchable_paths: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "success": self.success,
            "message": self.message,
            "gaps_detected": self.gaps_detected,
            "fetched_paths": self.fetched_paths,
            "unfetchable_paths": self.unfetchable_paths,
        }


def _collect_contract_referenced_paths(contract_data: dict) -> list[str]:
    """Return all file paths referenced in the contract that should exist on disk.

    Scans:
    - spec.repository.required_files (paths relative to repo root)
    - spec.docs_contract.blueprint_docs.template_sync_allowlist (relative to blueprint_docs.root)
    """
    paths: list[str] = []

    # required_files: absolute from repo root
    repo_spec = (contract_data.get("spec") or {}).get("repository") or {}
    required = repo_spec.get("required_files") or []
    paths.extend(str(p) for p in required)

    # template_sync_allowlist: relative to blueprint_docs.root
    docs_contract = (contract_data.get("spec") or {}).get("docs_contract") or {}
    blueprint_docs = docs_contract.get("blueprint_docs") or {}
    docs_root = blueprint_docs.get("root", "docs/blueprint")
    allowlist = blueprint_docs.get("template_sync_allowlist") or []
    for entry in allowlist:
        paths.append(f"{docs_root}/{entry}")

    return paths


def _detect_gaps(repo_root: Path, referenced_paths: list[str]) -> list[str]:
    """Return the subset of referenced paths that do not exist on disk."""
    return [p for p in referenced_paths if not (repo_root / p).exists()]


def _fetch_file_from_source(
    repo_root: Path,
    path: str,
    upgrade_source: str,
    upgrade_ref: str,
) -> bool:
    """Fetch a single file from the local git source using `git show`.

    Returns True on success, False if the file does not exist in the source at the ref.
    No HTTP is used — only local git operations.
    """
    dest = repo_root / path
    dest.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["git", "show", f"{upgrade_ref}:{path}"],
        capture_output=True,
        cwd=upgrade_source,
    )
    if result.returncode != 0:
        return False

    dest.write_bytes(result.stdout)
    return True


def run_coverage_fetch(
    repo_root: Path,
    *,
    upgrade_source: str,
    upgrade_ref: str,
) -> CoverageFetchResult:
    """Detect coverage gaps and fetch absent files from the local git source."""
    contract_path = repo_root / "blueprint" / "contract.yaml"
    if not contract_path.exists():
        return CoverageFetchResult(
            success=False,
            message="blueprint/contract.yaml not found; cannot determine coverage gaps",
        )

    try:
        contract_data = yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return CoverageFetchResult(
            success=False,
            message=f"failed to parse blueprint/contract.yaml: {exc}",
        )

    referenced = _collect_contract_referenced_paths(contract_data)
    gaps = _detect_gaps(repo_root, referenced)

    fetched: list[str] = []
    unfetchable: list[str] = []

    for path in gaps:
        if _fetch_file_from_source(repo_root, path, upgrade_source, upgrade_ref):
            fetched.append(path)
        else:
            unfetchable.append(path)

    return CoverageFetchResult(
        success=True,
        message=(
            f"coverage check complete: {len(gaps)} gap(s) detected, "
            f"{len(fetched)} fetched, {len(unfetchable)} unfetchable"
        ),
        gaps_detected=gaps,
        fetched_paths=fetched,
        unfetchable_paths=unfetchable,
    )


def main() -> int:
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Stage 5: detect coverage gaps and fetch absent files from local git.",
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    upgrade_source = os.environ.get("BLUEPRINT_UPGRADE_SOURCE", "")
    upgrade_ref = os.environ.get("BLUEPRINT_UPGRADE_REF", "")

    if not upgrade_source or not upgrade_ref:
        print(
            "[PIPELINE] Stage 5: FAILED — BLUEPRINT_UPGRADE_SOURCE and BLUEPRINT_UPGRADE_REF are required",
            file=sys.stderr,
        )
        return 1

    result = run_coverage_fetch(
        args.repo_root, upgrade_source=upgrade_source, upgrade_ref=upgrade_ref
    )
    if result.success:
        print(f"[PIPELINE] Stage 5: {result.message}")
        if result.unfetchable_paths:
            print(
                f"[PIPELINE] Stage 5: WARNING — {len(result.unfetchable_paths)} gap(s) "
                f"could not be fetched from source: {result.unfetchable_paths}",
                file=sys.stderr,
            )
        return 0
    print(f"[PIPELINE] Stage 5: FAILED — {result.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
