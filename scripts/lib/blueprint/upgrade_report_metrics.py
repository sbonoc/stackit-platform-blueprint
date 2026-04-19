#!/usr/bin/env python3
"""Emit key/value metric summaries from blueprint upgrade report artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Iterable


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"expected object JSON payload at {path}")


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _emit_plan_apply_metrics(plan_path: Path, apply_path: Path, reconcile_path: Path | None = None) -> Iterable[str]:
    plan = _load_json(plan_path)
    if isinstance(plan, dict):
        summary = plan.get("summary", {})
        if isinstance(summary, dict):
            yield f"plan_total={_as_int(summary.get('total', 0))}"
            yield f"plan_create={_as_int(summary.get('create', 0))}"
            yield f"plan_update={_as_int(summary.get('update', 0))}"
            yield f"plan_merge_required={_as_int(summary.get('merge-required', 0))}"
            yield f"plan_skip={_as_int(summary.get('skip', 0))}"
            yield f"plan_conflict={_as_int(summary.get('conflict', 0))}"
            yield f"plan_required_manual_actions={_as_int(summary.get('required_manual_action_count', 0))}"

    apply = _load_json(apply_path)
    if isinstance(apply, dict):
        status = str(apply.get("status", "unknown"))
        yield f"apply_status={status}"
        summary = apply.get("summary", {})
        if isinstance(summary, dict):
            yield f"apply_total={_as_int(summary.get('total', 0))}"
            yield f"apply_applied_count={_as_int(summary.get('applied_count', 0))}"
            yield f"apply_conflict={_as_int(summary.get('conflict', 0))}"
            yield f"apply_merged={_as_int(summary.get('merged', 0))}"
            yield f"apply_applied={_as_int(summary.get('applied', 0))}"
            yield f"apply_deleted={_as_int(summary.get('deleted', 0))}"
            yield f"apply_skipped={_as_int(summary.get('skipped', 0))}"
            yield f"apply_planned_only={_as_int(summary.get('planned-only', 0))}"
            yield f"apply_required_manual_actions={_as_int(summary.get('required_manual_action_count', 0))}"

    if reconcile_path is not None:
        reconcile = _load_json(reconcile_path)
        if isinstance(reconcile, dict):
            summary = reconcile.get("summary", {})
            if isinstance(summary, dict):
                yield (
                    "reconcile_blueprint_managed_safe_to_take_total="
                    + str(_as_int(summary.get("blueprint_managed_safe_to_take_count", 0)))
                )
                yield (
                    "reconcile_consumer_owned_manual_review_total="
                    + str(_as_int(summary.get("consumer_owned_manual_review_count", 0)))
                )
                yield (
                    "reconcile_generated_references_regenerate_total="
                    + str(_as_int(summary.get("generated_references_regenerate_count", 0)))
                )
                yield (
                    "reconcile_conflicts_unresolved_total="
                    + str(_as_int(summary.get("conflicts_unresolved_count", 0)))
                )
                yield f"reconcile_blocking_bucket_count={_as_int(summary.get('blocking_bucket_count', 0))}"
                yield f"reconcile_blocked={1 if bool(summary.get('blocked', False)) else 0}"


def _emit_validate_metrics(report_path: Path) -> Iterable[str]:
    report = _load_json(report_path)
    if not isinstance(report, dict):
        return []
    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        return []
    failed_targets = summary.get("failed_targets", [])
    if not isinstance(failed_targets, list):
        failed_targets = []
    status = str(summary.get("status", "unknown"))
    return [
        f"validate_status={status}",
        f"validate_commands_total={_as_int(summary.get('commands_total', 0))}",
        f"validate_failed_targets_total={len(failed_targets)}",
        f"validate_merge_markers_pre_total={_as_int(summary.get('merge_markers_pre_count', 0))}",
        f"validate_merge_markers_post_total={_as_int(summary.get('merge_markers_post_count', 0))}",
        f"validate_runtime_dependency_missing_total={_as_int(summary.get('runtime_dependency_missing_count', 0))}",
        f"validate_required_files_expected_total={_as_int(summary.get('required_files_expected_count', 0))}",
        f"validate_required_files_missing_total={_as_int(summary.get('required_files_missing_count', 0))}",
        (
            "validate_generated_reference_missing_paths_total="
            + str(_as_int(summary.get("generated_reference_missing_path_count", 0)))
        ),
        (
            "validate_generated_reference_missing_targets_total="
            + str(_as_int(summary.get("generated_reference_missing_target_count", 0)))
        ),
        (
            "validate_generated_reference_failed_targets_total="
            + str(_as_int(summary.get("generated_reference_failed_target_count", 0)))
        ),
        f"validate_contract_load_error_total={_as_int(summary.get('contract_load_error_count', 0))}",
    ]


def _emit_postcheck_metrics(report_path: Path) -> Iterable[str]:
    report = _load_json(report_path)
    if not isinstance(report, dict):
        return []
    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        return []
    status = str(summary.get("status", "unknown"))
    return [
        f"postcheck_status={status}",
        f"postcheck_commands_total={_as_int(summary.get('commands_total', 0))}",
        f"postcheck_merge_markers_total={_as_int(summary.get('merge_marker_count', 0))}",
        f"postcheck_conflicts_unresolved_total={_as_int(summary.get('conflicts_unresolved_count', 0))}",
        f"postcheck_docs_hook_failed_targets_total={_as_int(summary.get('docs_hook_failed_target_count', 0))}",
        f"postcheck_blocked_reasons_total={_as_int(summary.get('blocked_reason_count', 0))}",
        f"postcheck_validate_failure_total={_as_int(summary.get('validate_failure_count', 0))}",
        f"postcheck_contract_load_error_total={_as_int(summary.get('contract_load_error_count', 0))}",
    ]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    plan_apply = subparsers.add_parser("plan-apply", help="emit metrics for plan/apply artifacts")
    plan_apply.add_argument("--plan-path", required=True)
    plan_apply.add_argument("--apply-path", required=True)
    plan_apply.add_argument("--reconcile-path", required=False)

    validate = subparsers.add_parser("validate", help="emit metrics for validate artifact")
    validate.add_argument("--report-path", required=True)

    postcheck = subparsers.add_parser("postcheck", help="emit metrics for postcheck artifact")
    postcheck.add_argument("--report-path", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.mode == "plan-apply":
            reconcile_path = Path(args.reconcile_path) if getattr(args, "reconcile_path", None) else None
            lines = _emit_plan_apply_metrics(Path(args.plan_path), Path(args.apply_path), reconcile_path)
        elif args.mode == "validate":
            lines = _emit_validate_metrics(Path(args.report_path))
        else:
            lines = _emit_postcheck_metrics(Path(args.report_path))
    except Exception as exc:  # pragma: no cover - wrapper handles failure logging
        print(str(exc), file=sys.stderr)
        return 1

    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
