#!/usr/bin/env python3
"""Run deterministic post-upgrade convergence checks for consumer upgrades."""

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
from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402
from scripts.lib.blueprint.merge_markers import find_merge_markers  # noqa: E402
from scripts.lib.blueprint.upgrade_reconcile_report import RECONCILE_REPORT_DEFAULT_PATH  # noqa: E402


MAX_CAPTURE_CHARS = 20000
POSTCHECK_REPORT_DEFAULT_PATH = "artifacts/blueprint/upgrade_postcheck.json"
VALIDATE_REPORT_DEFAULT_PATH = "artifacts/blueprint/upgrade_validate.json"


@dataclass(frozen=True)
class PostcheckCommandResult:
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
        "--validate-report-path",
        default=VALIDATE_REPORT_DEFAULT_PATH,
        help="Upgrade validate report path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--reconcile-report-path",
        default=RECONCILE_REPORT_DEFAULT_PATH,
        help="Upgrade reconcile report path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--output-path",
        default=POSTCHECK_REPORT_DEFAULT_PATH,
        help="Postcheck report output path (absolute or repo-relative).",
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


def _run_make_target(repo_root: Path, target: str) -> PostcheckCommandResult:
    cmd = ["make", "--no-print-directory", "-C", str(repo_root), target]
    started = time.monotonic()
    result = _run(cmd)
    duration = time.monotonic() - started
    stdout, stdout_truncated = _truncate_output(result.stdout)
    stderr, stderr_truncated = _truncate_output(result.stderr)
    return PostcheckCommandResult(
        target=target,
        command=cmd,
        returncode=result.returncode,
        duration_seconds=duration,
        stdout=stdout,
        stderr=stderr,
        stdout_truncated=stdout_truncated,
        stderr_truncated=stderr_truncated,
    )


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"missing {label}: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _docs_hook_targets_for_repo_mode(repo_mode: str) -> tuple[list[str], str]:
    if repo_mode == "template-source":
        return ["quality-docs-check-blueprint-template-sync"], "template-source docs hooks executed"
    if repo_mode == "generated-consumer":
        return [], "generated-consumer mode skips template-sync docs hooks"
    return [], "repo mode unknown; docs hooks skipped"


def main() -> int:
    args = _parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    try:
        validate_report_path = _resolve_repo_scoped_path(
            repo_root,
            args.validate_report_path,
            "--validate-report-path",
        )
        reconcile_report_path = _resolve_repo_scoped_path(
            repo_root,
            args.reconcile_report_path,
            "--reconcile-report-path",
        )
        output_path = _resolve_repo_scoped_path(repo_root, args.output_path, "--output-path")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        _ensure_git_repo(repo_root)
        validate_payload = _load_json(validate_report_path, label="upgrade validate report")
        reconcile_payload = _load_json(reconcile_report_path, label="upgrade reconcile report")
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    contract_load_error = ""
    repo_mode = "unknown"
    try:
        contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
        repo_mode = contract.repository.repo_mode
    except Exception as exc:
        contract_load_error = f"unable to load blueprint contract for postcheck repo-mode hooks: {exc}"

    validate_status = str(validate_payload.get("summary", {}).get("status", "unknown"))
    reconcile_summary_raw = reconcile_payload.get("summary", {})
    reconcile_summary = reconcile_summary_raw if isinstance(reconcile_summary_raw, dict) else {}
    conflicts_unresolved_count = _as_int(reconcile_summary.get("conflicts_unresolved_count", 0))
    merge_markers = find_merge_markers(repo_root)

    docs_hook_targets, docs_hook_reason = _docs_hook_targets_for_repo_mode(repo_mode)
    docs_hook_results: list[PostcheckCommandResult] = []
    if docs_hook_targets:
        docs_hook_results = [_run_make_target(repo_root, target) for target in docs_hook_targets]
    docs_hook_failed_targets = [result.target for result in docs_hook_results if result.returncode != 0]

    blocked_reasons: list[str] = []
    if validate_status != "success":
        blocked_reasons.append("validate-status-failure")
    if merge_markers:
        blocked_reasons.append("merge-markers-present")
    if conflicts_unresolved_count > 0:
        blocked_reasons.append("reconcile-conflicts-unresolved")
    if docs_hook_failed_targets:
        blocked_reasons.append("docs-hook-target-failure")
    if contract_load_error:
        blocked_reasons.append("contract-load-error")

    status = "failure" if blocked_reasons else "success"
    payload = {
        "repo_root": str(repo_root),
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "validate_report_path": display_repo_path(repo_root, validate_report_path),
        "reconcile_report_path": display_repo_path(repo_root, reconcile_report_path),
        "repo_mode": repo_mode,
        "validate_status": validate_status,
        "merge_marker_check": {
            "count": len(merge_markers),
            "paths": merge_markers,
        },
        "reconcile_summary": {
            "conflicts_unresolved_count": conflicts_unresolved_count,
            "blocking_bucket_count": _as_int(reconcile_summary.get("blocking_bucket_count", 0)),
            "blocked": bool(reconcile_summary.get("blocked", False)),
        },
        "docs_hook_checks": {
            "mode": repo_mode,
            "targets": docs_hook_targets,
            "reason": docs_hook_reason,
            "failed_targets": docs_hook_failed_targets,
            "command_results": [result.as_dict() for result in docs_hook_results],
        },
        "contract_load_error": contract_load_error or None,
        "summary": {
            "status": status,
            "blocked_reason_count": len(blocked_reasons),
            "blocked_reasons": blocked_reasons,
            "commands_total": len(docs_hook_results),
            "merge_marker_count": len(merge_markers),
            "conflicts_unresolved_count": conflicts_unresolved_count,
            "docs_hook_failed_target_count": len(docs_hook_failed_targets),
            "validate_failure_count": 0 if validate_status == "success" else 1,
            "contract_load_error_count": 1 if contract_load_error else 0,
        },
    }
    _write_json(output_path, payload)
    print(
        "upgrade postcheck report: "
        f"{display_repo_path(repo_root, output_path)} "
        f"(status={status} blocked_reasons={len(blocked_reasons)})"
    )

    if blocked_reasons:
        print(
            "upgrade postcheck blocked: " + ", ".join(blocked_reasons),
            file=sys.stderr,
        )
    if docs_hook_failed_targets:
        print(
            "upgrade postcheck docs hooks failed: " + ", ".join(docs_hook_failed_targets),
            file=sys.stderr,
        )
    if contract_load_error:
        print(contract_load_error, file=sys.stderr)
    return 0 if status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
