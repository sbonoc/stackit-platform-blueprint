#!/usr/bin/env python3
"""Run post-upgrade validation for generated-consumer blueprint upgrades."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402
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
MAX_CAPTURE_CHARS = 20000


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
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        _ensure_git_repo(repo_root)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    merge_markers_pre = find_merge_markers(repo_root)
    command_results = [_run_make_target(repo_root, target) for target in VALIDATION_TARGETS]
    merge_markers_post = find_merge_markers(repo_root)
    missing_runtime_dependencies = _detect_missing_runtime_dependency_edges(repo_root)

    failed_targets = [result.target for result in command_results if result.returncode != 0]
    status = "success"
    if failed_targets or merge_markers_pre or merge_markers_post or missing_runtime_dependencies:
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
        "command_results": [result.as_dict() for result in command_results],
        "summary": {
            "status": status,
            "failed_targets": failed_targets,
            "merge_markers_pre_count": len(merge_markers_pre),
            "merge_markers_post_count": len(merge_markers_post),
            "runtime_dependency_missing_count": len(missing_runtime_dependencies),
            "commands_total": len(command_results),
        },
    }
    _write_json(report_path, payload)
    print(f"upgrade-validate: {display_repo_path(repo_root, report_path)}")

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

    return 0 if status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
