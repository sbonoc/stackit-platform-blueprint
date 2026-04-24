#!/usr/bin/env python3
"""Run post-upgrade validation for generated-consumer blueprint upgrades."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from pathlib import PurePosixPath
import subprocess
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import BlueprintContract, load_blueprint_contract  # noqa: E402
from scripts.lib.blueprint.merge_markers import find_merge_markers  # noqa: E402
from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES  # noqa: E402


VALIDATION_TARGETS = (
    "quality-hooks-fast",
    "infra-validate",
    "quality-docs-check-core-targets-sync",
    "quality-docs-check-contract-metadata-sync",
    "quality-docs-check-runtime-identity-summary-sync",
    "quality-docs-check-module-contract-summaries-sync",
)
REQUIRED_FILES_STATUS_DEFAULT_PATH = "artifacts/blueprint/upgrade/required_files_status.json"
MAX_CAPTURE_CHARS = 20000
GENERATED_REFERENCE_DOC_TARGETS = (
    (
        "docs/reference/generated/core_targets.generated.md",
        "quality-docs-check-core-targets-sync",
        "make quality-docs-sync-core-targets",
    ),
    (
        "docs/reference/generated/contract_metadata.generated.md",
        "quality-docs-check-contract-metadata-sync",
        "make quality-docs-sync-contract-metadata",
    ),
)


@dataclass(frozen=True)
class ValidationCommandResult:
    target: str
    command: list[str]
    returncode: int
    duration_seconds: float
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "command": self.command,
            "returncode": self.returncode,
            "duration_seconds": round(self.duration_seconds, 3),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "stdout_truncated": self.stdout_truncated,
            "stderr_truncated": self.stderr_truncated,
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None, help="Repository root path.")
    parser.add_argument(
        "--report-path",
        default="artifacts/blueprint/upgrade_validate.json",
        help="Validation report output path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--required-files-status-path",
        default=REQUIRED_FILES_STATUS_DEFAULT_PATH,
        help="Required-files status report path (absolute or repo-relative).",
    )
    return parser.parse_args()


def _resolve_repo_scoped_path(repo_root: Path, value: str, arg_name: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    resolved = (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"{arg_name} must stay within the repository root when using a relative path") from exc
    return resolved


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=repo_root)


def _ensure_git_repo(repo_root: Path) -> None:
    result = _run_git(repo_root, "rev-parse", "--is-inside-work-tree")
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise RuntimeError(f"repository is not a git worktree: {repo_root}")


def _truncate_output(value: str) -> tuple[str, bool]:
    if len(value) <= MAX_CAPTURE_CHARS:
        return value, False
    return value[-MAX_CAPTURE_CHARS:], True


def _run_make_target(repo_root: Path, target: str) -> ValidationCommandResult:
    cmd = ["make", "--no-print-directory", "-C", str(repo_root), target]
    started = time.monotonic()
    result = _run(cmd)
    duration = time.monotonic() - started
    stdout, stdout_truncated = _truncate_output(result.stdout)
    stderr, stderr_truncated = _truncate_output(result.stderr)
    return ValidationCommandResult(
        target=target,
        command=cmd,
        returncode=result.returncode,
        duration_seconds=duration,
        stdout=stdout,
        stderr=stderr,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")


def _path_is_same_or_child(path: str, parent: str) -> bool:
    path_parts = PurePosixPath(path).parts
    parent_parts = PurePosixPath(parent).parts
    if not parent_parts:
        return False
    if len(path_parts) < len(parent_parts):
        return False
    return path_parts[: len(parent_parts)] == parent_parts


def _required_files_for_repo_mode(contract: BlueprintContract) -> tuple[list[str], list[str]]:
    required_files = list(contract.repository.required_files)
    repository = contract.repository
    if repository.repo_mode != repository.consumer_init.mode_to:
        return sorted(required_files), []

    source_only_paths = repository.source_only_paths
    filtered: list[str] = []
    excluded: list[str] = []
    for relative_path in required_files:
        if any(_path_is_same_or_child(relative_path, source_only_path) for source_only_path in source_only_paths):
            excluded.append(relative_path)
            continue
        filtered.append(relative_path)
    return sorted(filtered), sorted(excluded)


def _path_matches_contract_class(path: str, entries: list[str]) -> bool:
    return any(_path_is_same_or_child(path, entry) for entry in entries)


def _missing_required_file_remediation(path: str, contract: BlueprintContract) -> dict[str, str]:
    if path == "docs/reference/generated/core_targets.generated.md":
        return {
            "action": "render",
            "hint": "Regenerate tracked core Make-target reference documentation.",
            "command": "make quality-docs-sync-core-targets",
        }
    if path == "docs/reference/generated/contract_metadata.generated.md":
        return {
            "action": "render",
            "hint": "Regenerate tracked contract metadata reference documentation.",
            "command": "make quality-docs-sync-contract-metadata",
        }
    if path.startswith("docs/reference/generated/"):
        return {
            "action": "render",
            "hint": "Regenerate generated documentation artifacts before validation rerun.",
            "command": "make quality-docs-sync-all",
        }
    if _path_matches_contract_class(path, contract.repository.consumer_seeded_paths):
        return {
            "action": "sync",
            "hint": "Path is consumer-seeded; synchronize the seeded template surface before rerunning validation.",
            "command": "make blueprint-resync-consumer-seeds",
        }
    if _path_matches_contract_class(path, contract.repository.init_managed_paths):
        return {
            "action": "restore",
            "hint": "Path is init-managed; re-run bootstrap with force to restore missing managed file(s).",
            "command": "make blueprint-init-repo BLUEPRINT_INIT_FORCE=true",
        }
    if _path_matches_contract_class(path, contract.repository.source_only_paths):
        return {
            "action": "manual-review",
            "hint": "Path is source-only for this contract; verify repo mode and ownership before restoring manually.",
            "command": "make infra-validate",
        }
    return {
        "action": "restore",
        "hint": "Re-run upgrade apply with pinned source/ref to restore required blueprint-managed file(s).",
        "command": "make blueprint-upgrade-consumer BLUEPRINT_UPGRADE_APPLY=true",
    }


def _build_required_file_reconciliation(
    *,
    repo_root: Path,
    contract: BlueprintContract,
) -> dict[str, Any]:
    required_files, excluded_by_repo_mode = _required_files_for_repo_mode(contract)

    entries: list[dict[str, Any]] = []
    for relative_path in required_files:
        exists = (repo_root / relative_path).is_file()
        entry: dict[str, Any] = {
            "path": relative_path,
            "status": "present" if exists else "missing",
            "exists": exists,
        }
        if not exists:
            entry["remediation"] = _missing_required_file_remediation(relative_path, contract)
        entries.append(entry)

    missing_entries = [entry for entry in entries if entry["status"] == "missing"]
    missing_paths = [str(entry["path"]) for entry in missing_entries]
    present_count = len(entries) - len(missing_entries)
    return {
        "repo_mode": contract.repository.repo_mode,
        "expected_count": len(required_files),
        "present_count": present_count,
        "missing_count": len(missing_entries),
        "missing_paths": sorted(missing_paths),
        "excluded_by_repo_mode": excluded_by_repo_mode,
        "entries": entries,
    }


def _build_generated_reference_contract_check(
    *,
    repo_root: Path,
    command_results: list[ValidationCommandResult],
) -> dict[str, Any]:
    command_results_by_target = {result.target: result for result in command_results}
    required_checks: list[dict[str, Any]] = []
    missing_paths: list[str] = []
    failed_targets: list[str] = []
    missing_targets: list[str] = []
    for path, target, remediation_command in GENERATED_REFERENCE_DOC_TARGETS:
        path_exists = (repo_root / path).is_file()
        if not path_exists:
            missing_paths.append(path)
        command_result = command_results_by_target.get(target)
        target_returncode: int | None = None
        if command_result is None:
            missing_targets.append(target)
        else:
            target_returncode = command_result.returncode
            if command_result.returncode != 0:
                failed_targets.append(target)
        required_checks.append(
            {
                "path": path,
                "target": target,
                "path_exists": path_exists,
                "target_returncode": target_returncode,
                "remediation_command": remediation_command,
            }
        )

    status = "success"
    if missing_paths or failed_targets or missing_targets:
        status = "failure"
    return {
        "status": status,
        "missing_paths": sorted(missing_paths),
        "missing_targets": sorted(missing_targets),
        "failed_targets": sorted(failed_targets),
        "required_checks": required_checks,
    }


def _empty_required_file_reconciliation(*, contract_load_error: str) -> dict[str, Any]:
    return {
        "repo_mode": "unknown",
        "expected_count": 0,
        "present_count": 0,
        "missing_count": 0,
        "missing_paths": [],
        "excluded_by_repo_mode": [],
        "entries": [],
        "contract_load_error": contract_load_error,
    }


def _scan_prune_glob_violations(
    *,
    repo_root: Path,
    contract: BlueprintContract,
) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    """Scan the working tree for files matching source_artifact_prune_globs_on_init.

    Returns (prune_glob_check, violations_with_glob) where violations_with_glob is a list
    of (path, glob_pattern) pairs used for stderr emission (NFR-OBS-001).
    """
    repo_mode = contract.repository.repo_mode
    generated_consumer_mode = contract.repository.consumer_init.mode_to

    if repo_mode != generated_consumer_mode:
        skipped: dict[str, Any] = {
            "status": "skipped",
            "globs_checked": [],
            "violations": [],
            "violation_count": 0,
            "remediation_hint": "",
        }
        return skipped, []

    globs = list(contract.repository.consumer_init.source_artifact_prune_globs_on_init)
    repo_root_resolved = repo_root.resolve()
    violations_with_glob: list[tuple[str, str]] = []
    seen: set[str] = set()

    for pattern in globs:
        for path in sorted(repo_root.rglob(pattern)):
            # NFR-SEC-001: skip symlinks that resolve outside repo root
            try:
                path.resolve().relative_to(repo_root_resolved)
            except ValueError:
                continue
            rel_posix = path.relative_to(repo_root).as_posix()
            if rel_posix not in seen:
                seen.add(rel_posix)
                violations_with_glob.append((rel_posix, pattern))

    violations = sorted(seen)
    violation_count = len(violations)
    status = "failure" if violation_count > 0 else "success"
    remediation_hint = (
        f"Remove the following files: {', '.join(violations)}. "
        "Then re-run: make blueprint-upgrade-consumer-validate"
        if violation_count > 0
        else ""
    )
    prune_glob_check: dict[str, Any] = {
        "status": status,
        "globs_checked": globs,
        "violations": violations,
        "violation_count": violation_count,
        "remediation_hint": remediation_hint,
    }
    return prune_glob_check, violations_with_glob


def _detect_missing_runtime_dependency_edges(repo_root: Path) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for consumer_path, dependency_path in RUNTIME_DEPENDENCY_EDGES:
        consumer_file = repo_root / consumer_path
        if not consumer_file.is_file():
            continue
        content = consumer_file.read_text(encoding="utf-8", errors="surrogateescape")
        if dependency_path not in content:
            continue
        if (repo_root / dependency_path).is_file():
            continue
        missing.append(
            {
                "consumer_path": consumer_path,
                "dependency_path": dependency_path,
                "reason": "consumer path references dependency path but dependency file is missing",
            }
        )
    return missing


def main() -> int:
    args = _parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    try:
        report_path = _resolve_repo_scoped_path(repo_root, args.report_path, "--report-path")
        required_files_status_path = _resolve_repo_scoped_path(
            repo_root,
            args.required_files_status_path,
            "--required-files-status-path",
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        _ensure_git_repo(repo_root)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    merge_markers_pre = find_merge_markers(repo_root)
    contract: BlueprintContract | None = None
    contract_load_error = ""
    try:
        contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    except Exception as exc:
        contract_load_error = f"unable to load blueprint contract for required-files reconciliation: {exc}"

    command_results: list[ValidationCommandResult] = []
    if not contract_load_error:
        command_results = [_run_make_target(repo_root, target) for target in VALIDATION_TARGETS]
    merge_markers_post = find_merge_markers(repo_root)
    missing_runtime_dependencies = _detect_missing_runtime_dependency_edges(repo_root)
    prune_glob_violations_with_glob: list[tuple[str, str]] = []
    if contract is None:
        required_file_reconciliation = _empty_required_file_reconciliation(contract_load_error=contract_load_error)
        prune_glob_check: dict[str, Any] = {
            "status": "skipped",
            "globs_checked": [],
            "violations": [],
            "violation_count": 0,
            "remediation_hint": "",
        }
    else:
        required_file_reconciliation = _build_required_file_reconciliation(repo_root=repo_root, contract=contract)
        prune_glob_check, prune_glob_violations_with_glob = _scan_prune_glob_violations(
            repo_root=repo_root, contract=contract
        )
    generated_reference_contract = _build_generated_reference_contract_check(
        repo_root=repo_root,
        command_results=command_results,
    )
    if contract_load_error:
        generated_reference_contract["status"] = "failure"
        generated_reference_contract["contract_load_error"] = contract_load_error

    failed_targets = [result.target for result in command_results if result.returncode != 0]
    status = "success"
    if (
        contract_load_error
        or failed_targets
        or merge_markers_pre
        or merge_markers_post
        or missing_runtime_dependencies
        or required_file_reconciliation["missing_count"] > 0
        or generated_reference_contract["status"] != "success"
        or prune_glob_check["violation_count"] > 0
    ):
        status = "failure"

    payload = {
        "repo_root": str(repo_root),
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "required_validation_targets": list(VALIDATION_TARGETS),
        "merge_marker_check": {
            "pre": merge_markers_pre,
            "post": merge_markers_post,
        },
        "runtime_dependency_edge_check": {
            "required_edges": [
                {"consumer_path": consumer_path, "dependency_path": dependency_path}
                for consumer_path, dependency_path in RUNTIME_DEPENDENCY_EDGES
            ],
            "missing": missing_runtime_dependencies,
        },
        "required_file_reconciliation": required_file_reconciliation,
        "generated_reference_contract_check": generated_reference_contract,
        "prune_glob_check": prune_glob_check,
        "contract_load_error": contract_load_error or None,
        "command_results": [result.as_dict() for result in command_results],
        "summary": {
            "status": status,
            "failed_targets": failed_targets,
            "merge_markers_pre_count": len(merge_markers_pre),
            "merge_markers_post_count": len(merge_markers_post),
            "runtime_dependency_missing_count": len(missing_runtime_dependencies),
            "required_files_expected_count": required_file_reconciliation["expected_count"],
            "required_files_missing_count": required_file_reconciliation["missing_count"],
            "generated_reference_missing_path_count": len(generated_reference_contract["missing_paths"]),
            "generated_reference_missing_target_count": len(generated_reference_contract["missing_targets"]),
            "generated_reference_failed_target_count": len(generated_reference_contract["failed_targets"]),
            "contract_load_error_count": 1 if contract_load_error else 0,
            "commands_total": len(command_results),
            "prune_glob_violation_count": prune_glob_check["violation_count"],
        },
    }
    required_files_status_payload = {
        "repo_root": str(repo_root),
        "report_generated_at": payload["report_generated_at"],
        "required_file_reconciliation": required_file_reconciliation,
        "generated_reference_contract_check": generated_reference_contract,
        "contract_load_error": payload["contract_load_error"],
    }

    _write_json(required_files_status_path, required_files_status_payload)
    _write_json(report_path, payload)
    print(f"upgrade-validate: {display_repo_path(repo_root, report_path)}")
    print(f"required-files-status: {display_repo_path(repo_root, required_files_status_path)}")

    if merge_markers_pre:
        print(
            "merge markers detected before validation; remove unresolved conflict markers and rerun",
            file=sys.stderr,
        )
    if merge_markers_post and not merge_markers_pre:
        print(
            "merge markers detected after validation; remove unresolved conflict markers and rerun",
            file=sys.stderr,
        )
    if failed_targets:
        print(
            "upgrade validation failed targets: " + ", ".join(failed_targets),
            file=sys.stderr,
        )
    if missing_runtime_dependencies:
        diagnostics = ", ".join(
            f"{entry['consumer_path']} -> {entry['dependency_path']}"
            for entry in missing_runtime_dependencies
        )
        print(
            "upgrade validation runtime dependency edges missing required files: " + diagnostics,
            file=sys.stderr,
        )
    if contract_load_error:
        print(contract_load_error, file=sys.stderr)
    if required_file_reconciliation["missing_count"] > 0:
        missing_entries = [
            entry
            for entry in required_file_reconciliation["entries"]
            if isinstance(entry, dict) and entry.get("status") == "missing"
        ]
        diagnostics = ", ".join(
            f"{entry.get('path')} ({entry.get('remediation', {}).get('action', 'manual-review')})"
            for entry in missing_entries
        )
        print(
            "upgrade validation missing required files for active repo_mode: " + diagnostics,
            file=sys.stderr,
        )
    if generated_reference_contract["status"] != "success":
        diagnostics: list[str] = []
        if generated_reference_contract["missing_paths"]:
            diagnostics.append("missing paths=" + ",".join(generated_reference_contract["missing_paths"]))
        if generated_reference_contract["missing_targets"]:
            diagnostics.append("missing targets=" + ",".join(generated_reference_contract["missing_targets"]))
        if generated_reference_contract["failed_targets"]:
            diagnostics.append("failed targets=" + ",".join(generated_reference_contract["failed_targets"]))
        print(
            "upgrade validation generated reference contract check failed: " + "; ".join(diagnostics),
            file=sys.stderr,
        )
    for path, glob in prune_glob_violations_with_glob:
        print(f"prune-glob violation: {path} (matches: {glob})", file=sys.stderr)

    return 0 if status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
