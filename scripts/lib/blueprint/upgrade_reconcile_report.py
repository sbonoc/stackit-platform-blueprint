#!/usr/bin/env python3
"""Shared reconcile-report classification for blueprint consumer upgrades."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RECONCILE_REPORT_DEFAULT_PATH = "artifacts/blueprint/upgrade/upgrade_reconcile_report.json"
RECONCILE_BUCKET_ORDER = (
    "blueprint_managed_safe_to_take",
    "consumer_owned_manual_review",
    "generated_references_regenerate",
    "conflicts_unresolved",
)
_BLOCKING_BUCKETS = frozenset(
    (
        "consumer_owned_manual_review",
        "generated_references_regenerate",
        "conflicts_unresolved",
    )
)
_BUCKET_POLICY = {
    "blueprint_managed_safe_to_take": {
        "blocking": False,
        "hint": "Safe blueprint-managed updates can be applied with pinned source/ref.",
        "next_commands": (
            "BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer",
            "make blueprint-upgrade-consumer-postcheck",
        ),
    },
    "consumer_owned_manual_review": {
        "blocking": True,
        "hint": "Consumer-owned or protected paths require explicit manual reconciliation before postcheck.",
        "next_commands": (
            "make blueprint-upgrade-consumer-preflight",
            "make blueprint-upgrade-consumer-postcheck",
        ),
    },
    "generated_references_regenerate": {
        "blocking": True,
        "hint": "Generated reference docs require regeneration/sync before postcheck.",
        "next_commands": (
            "make quality-docs-sync-all",
            "make blueprint-upgrade-consumer-postcheck",
        ),
    },
    "conflicts_unresolved": {
        "blocking": True,
        "hint": "Resolve merge conflicts and conflict markers before postcheck.",
        "next_commands": (
            "BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer",
            "make blueprint-upgrade-consumer-postcheck",
        ),
    },
}


def find_merge_markers(repo_root: Path) -> set[str]:
    """Return relative paths of files in repo_root that contain active merge conflict markers.

    Scans the working tree at report-build time so that the result reflects
    current file state rather than stale plan/apply metadata.  (FR-001)

    Only text-readable files are scanned; binary and unreadable files are skipped.
    """
    active_paths: set[str] = set()
    try:
        for path in repo_root.rglob("*"):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "<<<<<<<" in content:
                active_paths.add(str(path.relative_to(repo_root)))
    except OSError:
        pass
    return active_paths


def _collect_entries(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict)]


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _is_generated_reference_path(path: str) -> bool:
    return path.startswith("docs/reference/generated/")


def _manual_reason(entry: dict[str, Any]) -> bool:
    reason = _as_str(entry.get("reason", "")).lower()
    if "consumer-owned" in reason:
        return True
    if "platform-owned" in reason:
        return True
    if "required-manual-action" in reason:
        return True
    return False


def _new_bucket_state() -> dict[str, list[dict[str, Any]]]:
    return {bucket: [] for bucket in RECONCILE_BUCKET_ORDER}


def _add_bucket_item(
    buckets: dict[str, list[dict[str, Any]]],
    *,
    seen: set[tuple[str, str, str, str, str]],
    bucket: str,
    path: str,
    source: str,
    action: str,
    reason: str,
) -> None:
    normalized_path = _as_str(path)
    if not normalized_path:
        return
    key = (bucket, normalized_path, source, action, reason)
    if key in seen:
        return
    seen.add(key)
    policy = _BUCKET_POLICY[bucket]
    buckets[bucket].append(
        {
            "path": normalized_path,
            "source": source,
            "action": action,
            "reason": reason,
            "blocking": bool(policy["blocking"]),
            "remediation_hint": str(policy["hint"]),
            "next_commands": list(policy["next_commands"]),
        }
    )


def _classify_plan_entries(
    plan_entries: list[dict[str, Any]],
    buckets: dict[str, list[dict[str, Any]]],
    seen: set[tuple[str, str, str, str, str]],
) -> None:
    for entry in plan_entries:
        path = _as_str(entry.get("path"))
        action = _as_str(entry.get("action"))
        reason = _as_str(entry.get("reason"))
        ownership = _as_str(entry.get("ownership"))
        target_exists = entry.get("target_exists")

        if not path:
            continue

        if action in {"conflict", "merge-required"}:
            if _is_generated_reference_path(path):
                _add_bucket_item(
                    buckets,
                    seen=seen,
                    bucket="generated_references_regenerate",
                    path=path,
                    source="plan-entry",
                    action=action,
                    reason=reason or "generated reference path requires regeneration",
                )
            _add_bucket_item(
                buckets,
                seen=seen,
                bucket="conflicts_unresolved",
                path=path,
                source="plan-entry",
                action=action,
                reason=reason or "plan indicates unresolved conflict state",
            )
            continue

        if _is_generated_reference_path(path) and action in {"skip", "update", "create"}:
            if action == "skip" or _manual_reason(entry):
                _add_bucket_item(
                    buckets,
                    seen=seen,
                    bucket="generated_references_regenerate",
                    path=path,
                    source="plan-entry",
                    action=action,
                    reason=reason or "generated reference path requires regeneration",
                )
                continue

        if action == "skip" and (_manual_reason(entry) or target_exists is False):
            _add_bucket_item(
                buckets,
                seen=seen,
                bucket="consumer_owned_manual_review",
                path=path,
                source="plan-entry",
                action=action,
                reason=reason or "manual review required for skipped path",
            )
            continue

        if action in {"create", "update"} and ownership != "consumer-seeded":
            _add_bucket_item(
                buckets,
                seen=seen,
                bucket="blueprint_managed_safe_to_take",
                path=path,
                source="plan-entry",
                action=action,
                reason=reason or "safe blueprint-managed action",
            )


def _classify_required_manual_actions(
    required_manual_actions: list[dict[str, Any]],
    buckets: dict[str, list[dict[str, Any]]],
    seen: set[tuple[str, str, str, str, str]],
) -> None:
    for action in required_manual_actions:
        path = _as_str(action.get("dependency_path"))
        dependency_of = _as_str(action.get("dependency_of"))
        reason = _as_str(action.get("reason"))
        if not path:
            continue
        bucket = "generated_references_regenerate" if _is_generated_reference_path(path) else "consumer_owned_manual_review"
        _add_bucket_item(
            buckets,
            seen=seen,
            bucket=bucket,
            path=path,
            source="required-manual-action",
            action="required-manual-action",
            reason=(f"{dependency_of}: {reason}" if dependency_of else reason),
        )


def _classify_apply_results(
    apply_results: list[dict[str, Any]],
    buckets: dict[str, list[dict[str, Any]]],
    seen: set[tuple[str, str, str, str, str]],
) -> None:
    for result in apply_results:
        result_type = _as_str(result.get("result"))
        path = _as_str(result.get("path"))
        reason = _as_str(result.get("reason"))
        if result_type != "conflict" or not path:
            continue
        _add_bucket_item(
            buckets,
            seen=seen,
            bucket="conflicts_unresolved",
            path=path,
            source="apply-result",
            action=result_type,
            reason=reason or "apply result reports unresolved conflict",
        )


def _classify_merge_markers(
    merge_markers: list[Any],
    buckets: dict[str, list[dict[str, Any]]],
    seen: set[tuple[str, str, str, str, str]],
) -> None:
    for value in merge_markers:
        path = _as_str(value)
        if not path:
            continue
        _add_bucket_item(
            buckets,
            seen=seen,
            bucket="conflicts_unresolved",
            path=path,
            source="merge-marker",
            action="merge-marker",
            reason="unresolved merge marker present in file",
        )


def _sorted_bucket_items(bucket_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        bucket_items,
        key=lambda item: (
            _as_str(item.get("path")),
            _as_str(item.get("source")),
            _as_str(item.get("action")),
            _as_str(item.get("reason")),
        ),
    )


def reconcile_report_stale_reasons(
    *,
    reconcile_report: dict[str, Any],
    plan_payload: dict[str, Any] | None = None,
    apply_payload: dict[str, Any] | None = None,
    reconcile_path: Path | None = None,
    plan_path: Path | None = None,
    apply_path: Path | None = None,
) -> list[str]:
    summary_raw = reconcile_report.get("summary", {})
    summary = summary_raw if isinstance(summary_raw, dict) else {}
    reasons: list[str] = []

    if isinstance(plan_payload, dict):
        expected_source = _as_str(plan_payload.get("source"))
        expected_upgrade_ref = _as_str(plan_payload.get("upgrade_ref"))
        expected_commit = _as_str(plan_payload.get("resolved_upgrade_commit"))
        expected_baseline = _as_str(plan_payload.get("baseline_ref"))

        if expected_source and _as_str(reconcile_report.get("source")) != expected_source:
            reasons.append("metadata-source-mismatch")
        if expected_upgrade_ref and _as_str(reconcile_report.get("upgrade_ref")) != expected_upgrade_ref:
            reasons.append("metadata-upgrade-ref-mismatch")
        if expected_commit and _as_str(reconcile_report.get("resolved_upgrade_commit")) != expected_commit:
            reasons.append("metadata-resolved-commit-mismatch")
        if expected_baseline != _as_str(reconcile_report.get("template_ref_from")):
            reasons.append("metadata-baseline-ref-mismatch")

        expected_plan_entry_count = len(_collect_entries(plan_payload, "entries"))
        expected_required_manual_action_count = len(_collect_entries(plan_payload, "required_manual_actions"))
        if "plan_entry_count" not in summary:
            reasons.append("summary-plan-entry-count-missing")
        elif _as_int(summary.get("plan_entry_count")) != expected_plan_entry_count:
            reasons.append("summary-plan-entry-count-mismatch")
        if "required_manual_action_count" not in summary:
            reasons.append("summary-required-manual-action-count-missing")
        elif _as_int(summary.get("required_manual_action_count")) != expected_required_manual_action_count:
            reasons.append("summary-required-manual-action-count-mismatch")

    if isinstance(apply_payload, dict):
        expected_apply_result_count = len(_collect_entries(apply_payload, "results"))
        if "apply_result_count" not in summary:
            reasons.append("summary-apply-result-count-missing")
        elif _as_int(summary.get("apply_result_count")) != expected_apply_result_count:
            reasons.append("summary-apply-result-count-mismatch")

    if (
        reconcile_path is not None
        and plan_path is not None
        and apply_path is not None
        and reconcile_path.is_file()
        and plan_path.is_file()
        and apply_path.is_file()
    ):
        try:
            reconcile_mtime = reconcile_path.stat().st_mtime
            latest_input_mtime = max(plan_path.stat().st_mtime, apply_path.stat().st_mtime)
        except OSError:
            pass
        else:
            if reconcile_mtime < latest_input_mtime:
                reasons.append("artifact-mtime-older-than-plan-apply")

    return sorted(set(reasons))


def build_upgrade_reconcile_report(
    *,
    repo_root: Path,
    plan_payload: dict[str, Any],
    apply_payload: dict[str, Any],
    repo_mode: str = "unknown",
    source: str = "",
    upgrade_ref: str = "",
    resolved_upgrade_commit: str = "",
    baseline_ref: str | None = None,
    command_plan: dict[str, str] | None = None,
) -> dict[str, Any]:
    plan_entries = _collect_entries(plan_payload, "entries")
    apply_results = _collect_entries(apply_payload, "results")
    required_manual_actions = _collect_entries(plan_payload, "required_manual_actions")
    merge_markers_raw = apply_payload.get("merge_markers", [])
    merge_markers = merge_markers_raw if isinstance(merge_markers_raw, list) else []

    buckets = _new_bucket_state()
    seen: set[tuple[str, str, str, str, str]] = set()
    _classify_plan_entries(plan_entries, buckets, seen)
    _classify_required_manual_actions(required_manual_actions, buckets, seen)
    _classify_apply_results(apply_results, buckets, seen)
    _classify_merge_markers(merge_markers, buckets, seen)

    # Rebuild conflicts_unresolved from the working-tree marker scan (FR-001–FR-004).
    # This replaces any stale plan/apply entries with the authoritative live state:
    # only files that currently contain <<<<<<< markers are blocking.  Double-counting
    # is eliminated because each path appears at most once in the scan result.
    active_marker_paths = find_merge_markers(repo_root)
    conflict_policy = _BUCKET_POLICY["conflicts_unresolved"]
    buckets["conflicts_unresolved"] = [
        {
            "path": p,
            "source": "working-tree-scan",
            "action": "merge-marker",
            "reason": "unresolved merge marker present in file",
            "blocking": bool(conflict_policy["blocking"]),
            "remediation_hint": str(conflict_policy["hint"]),
            "next_commands": list(conflict_policy["next_commands"]),
        }
        for p in sorted(active_marker_paths)
    ]

    for bucket in RECONCILE_BUCKET_ORDER:
        buckets[bucket] = _sorted_bucket_items(buckets[bucket])

    summary: dict[str, Any] = {
        "plan_entry_count": len(plan_entries),
        "apply_result_count": len(apply_results),
        "required_manual_action_count": len(required_manual_actions),
    }
    blocking_bucket_count = 0
    for bucket in RECONCILE_BUCKET_ORDER:
        count = len(buckets[bucket])
        summary[f"{bucket}_count"] = count
        if bucket in _BLOCKING_BUCKETS and count > 0:
            blocking_bucket_count += 1
    summary["blocking_bucket_count"] = blocking_bucket_count
    summary["blocked"] = blocking_bucket_count > 0

    resolved_source = source or _as_str(plan_payload.get("source"))
    resolved_upgrade_ref = upgrade_ref or _as_str(plan_payload.get("upgrade_ref"))
    resolved_commit = resolved_upgrade_commit or _as_str(plan_payload.get("resolved_upgrade_commit"))
    resolved_baseline_ref = baseline_ref if baseline_ref is not None else _as_str(plan_payload.get("baseline_ref")) or None
    resolved_command_plan = command_plan or {
        "preflight": "make blueprint-upgrade-consumer-preflight",
        "plan": "make blueprint-upgrade-consumer",
        "apply": "BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer",
        "validate": "make blueprint-upgrade-consumer-validate",
        "postcheck": "make blueprint-upgrade-consumer-postcheck",
    }

    return {
        "repo_root": str(repo_root),
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_mode": repo_mode,
        "source": resolved_source,
        "upgrade_ref": resolved_upgrade_ref,
        "resolved_upgrade_commit": resolved_commit,
        "template_ref_from": resolved_baseline_ref,
        "template_ref_to": resolved_upgrade_ref,
        "command_plan": resolved_command_plan,
        "bucket_policy": {
            bucket: {
                "blocking": bool(_BUCKET_POLICY[bucket]["blocking"]),
                "hint": str(_BUCKET_POLICY[bucket]["hint"]),
                "next_commands": list(_BUCKET_POLICY[bucket]["next_commands"]),
            }
            for bucket in RECONCILE_BUCKET_ORDER
        },
        "buckets": buckets,
        "required_manual_actions": required_manual_actions,
        "summary": summary,
    }


def build_merge_risk_classification(reconcile_report: dict[str, Any]) -> dict[str, Any]:
    buckets_raw = reconcile_report.get("buckets", {})
    bucket_policy = reconcile_report.get("bucket_policy", {})
    if not isinstance(buckets_raw, dict):
        buckets_raw = {}
    if not isinstance(bucket_policy, dict):
        bucket_policy = {}

    merged_bucket_rows: list[dict[str, Any]] = []
    blocking_buckets: list[str] = []
    for bucket in RECONCILE_BUCKET_ORDER:
        items = buckets_raw.get(bucket, [])
        if not isinstance(items, list):
            items = []
        policy = bucket_policy.get(bucket, {})
        blocking = bool(policy.get("blocking", bucket in _BLOCKING_BUCKETS))
        hint = _as_str(policy.get("hint")) or _as_str(_BUCKET_POLICY[bucket]["hint"])
        next_commands_raw = policy.get("next_commands", _BUCKET_POLICY[bucket]["next_commands"])
        next_commands = [str(value) for value in next_commands_raw] if isinstance(next_commands_raw, (list, tuple)) else []
        paths = sorted({_as_str(item.get("path")) for item in items if isinstance(item, dict) and _as_str(item.get("path"))})
        row = {
            "bucket": bucket,
            "count": len(items),
            "blocking": blocking,
            "hint": hint,
            "next_commands": next_commands,
            "paths": paths,
        }
        merged_bucket_rows.append(row)
        if blocking and len(items) > 0:
            blocking_buckets.append(bucket)

    return {
        "status": "blocked" if blocking_buckets else "safe-to-continue",
        "blocking_buckets": blocking_buckets,
        "blocking_bucket_count": len(blocking_buckets),
        "bucket_order": list(RECONCILE_BUCKET_ORDER),
        "buckets": merged_bucket_rows,
    }
