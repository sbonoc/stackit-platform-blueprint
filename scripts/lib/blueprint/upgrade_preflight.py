#!/usr/bin/env python3
"""Build a machine-readable preflight report from upgrade plan/apply artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from pathlib import PurePosixPath
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import BlueprintContract, load_blueprint_contract  # noqa: E402
from scripts.lib.blueprint.upgrade_reconcile_report import (  # noqa: E402
    RECONCILE_REPORT_DEFAULT_PATH,
    build_merge_risk_classification,
    build_upgrade_reconcile_report,
)


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


def _collect_entries(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, dict)]


def _skip_action_is_required_surface_risk(entry: dict[str, Any]) -> bool:
    # Skip actions are noisy by default because many are benign no-ops
    # (`path already matches upgrade source content`). Treat them as risky
    # only when the required surface is absent and therefore unreconciled.
    target_exists = entry.get("target_exists")
    if isinstance(target_exists, bool):
        return not target_exists
    return False


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


def _required_files_contract_context(repo_root: Path) -> dict[str, Any]:
    contract_path = repo_root / "blueprint/contract.yaml"
    if not contract_path.is_file():
        return {
            "contract_available": False,
            "contract_error": f"missing blueprint contract: {contract_path}",
            "repo_mode": "unknown",
            "required_files": [],
            "excluded_by_repo_mode": [],
        }

    try:
        contract = load_blueprint_contract(contract_path)
    except Exception as exc:
        return {
            "contract_available": False,
            "contract_error": f"unable to load blueprint contract: {exc}",
            "repo_mode": "unknown",
            "required_files": [],
            "excluded_by_repo_mode": [],
        }

    required_files, excluded_by_repo_mode = _required_files_for_repo_mode(contract)
    return {
        "contract_available": True,
        "contract_error": "",
        "repo_mode": contract.repository.repo_mode,
        "required_files": required_files,
        "excluded_by_repo_mode": excluded_by_repo_mode,
    }


def _build_report(
    *,
    repo_root: Path,
    plan_path: Path,
    apply_path: Path,
    reconcile_path: Path,
) -> dict[str, Any]:
    plan_payload = _load_json(plan_path, label="upgrade plan report")
    apply_payload = _load_json(apply_path, label="upgrade apply report")
    plan_entries = _collect_entries(plan_payload, "entries")
    required_manual_actions = _collect_entries(plan_payload, "required_manual_actions")
    apply_results = _collect_entries(apply_payload, "results")

    auto_apply: list[dict[str, Any]] = []
    manual_merge: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for entry in plan_entries:
        action = str(entry.get("action", "")).strip()
        if action in {"create", "update"}:
            auto_apply.append(entry)
            continue
        if action == "merge-required":
            manual_merge.append(entry)
            continue
        if action == "conflict":
            conflicts.append(entry)
            continue
        if action == "skip":
            skipped.append(entry)

    required_follow_up_commands = sorted(
        {
            str(command)
            for action in required_manual_actions
            for command in action.get("required_follow_up_commands", [])
            if isinstance(command, str) and command.strip()
        }
    )
    blocking_paths = sorted(
        {
            str(entry.get("path", "")).strip()
            for entry in [*manual_merge, *conflicts]
            if isinstance(entry.get("path"), str) and str(entry.get("path", "")).strip()
        }
        | {
            str(action.get("dependency_path", "")).strip()
            for action in required_manual_actions
            if isinstance(action.get("dependency_path"), str) and str(action.get("dependency_path", "")).strip()
        }
    )
    contract_context = _required_files_contract_context(repo_root)
    required_files_set = set(contract_context["required_files"])

    required_surface_deltas: list[dict[str, Any]] = []
    for entry in plan_entries:
        path = str(entry.get("path", "")).strip()
        if not path or path not in required_files_set:
            continue
        required_surface_deltas.append(entry)

    manual_dependency_paths = {
        str(action.get("dependency_path", "")).strip()
        for action in required_manual_actions
        if isinstance(action.get("dependency_path"), str) and str(action.get("dependency_path", "")).strip()
    }

    required_surfaces_at_risk: list[dict[str, Any]] = []
    for entry in required_surface_deltas:
        path = str(entry.get("path", "")).strip()
        action = str(entry.get("action", "")).strip()
        risk_reasons: list[str] = []
        if action in {"merge-required", "conflict"}:
            risk_reasons.append(f"plan-action:{action}")
        elif action == "skip" and _skip_action_is_required_surface_risk(entry):
            risk_reasons.append("plan-action:skip-missing-target")
        if path in manual_dependency_paths:
            risk_reasons.append("required-manual-action")
        if risk_reasons:
            required_surfaces_at_risk.append(
                {
                    "path": path,
                    "action": action,
                    "risk_reasons": risk_reasons,
                }
            )

    required_surface_paths = {str(entry.get("path", "")).strip() for entry in required_surface_deltas}
    for dependency_path in sorted(manual_dependency_paths & required_files_set):
        if dependency_path in required_surface_paths:
            continue
        required_surfaces_at_risk.append(
            {
                "path": dependency_path,
                "action": "required-manual-action",
                "risk_reasons": ["required-manual-action"],
            }
        )

    required_surfaces_auto_apply = [
        str(entry.get("path", "")).strip()
        for entry in required_surface_deltas
        if str(entry.get("action", "")).strip() in {"create", "update"}
    ]
    required_surfaces_auto_apply = sorted(path for path in required_surfaces_auto_apply if path)
    required_surfaces_at_risk = sorted(required_surfaces_at_risk, key=lambda entry: str(entry.get("path", "")))

    if reconcile_path.is_file():
        reconcile_report = _load_json(reconcile_path, label="upgrade reconcile report")
    else:
        reconcile_report = build_upgrade_reconcile_report(
            repo_root=repo_root,
            plan_payload=plan_payload,
            apply_payload=apply_payload,
            repo_mode=str(contract_context.get("repo_mode", "unknown")),
        )
    merge_risk_classification = build_merge_risk_classification(reconcile_report)

    summary = {
        "plan_entry_count": len(plan_entries),
        "apply_result_count": len(apply_results),
        "auto_apply_count": len(auto_apply),
        "manual_merge_count": len(manual_merge),
        "conflict_count": len(conflicts),
        "skip_count": len(skipped),
        "required_manual_action_count": len(required_manual_actions),
        "required_follow_up_command_count": len(required_follow_up_commands),
        "blocking_path_count": len(blocking_paths),
        "required_surface_delta_count": len(required_surface_deltas),
        "required_surface_auto_apply_count": len(required_surfaces_auto_apply),
        "required_surface_at_risk_count": len(required_surfaces_at_risk),
        "merge_risk_blocking_bucket_count": int(merge_risk_classification.get("blocking_bucket_count", 0)),
    }

    return {
        "plan_path": display_repo_path(repo_root, plan_path),
        "apply_path": display_repo_path(repo_root, apply_path),
        "reconcile_report_path": display_repo_path(repo_root, reconcile_path),
        "summary": summary,
        "auto_apply": auto_apply,
        "manual_merge": manual_merge,
        "conflicts": conflicts,
        "skipped": skipped,
        "required_manual_actions": required_manual_actions,
        "required_follow_up_commands": required_follow_up_commands,
        "blocking_paths": blocking_paths,
        "merge_risk_classification": merge_risk_classification,
        "required_surface_reconciliation": {
            "contract_available": contract_context["contract_available"],
            "contract_error": contract_context["contract_error"],
            "repo_mode": contract_context["repo_mode"],
            "required_files_expected_count": len(contract_context["required_files"]),
            "required_files_excluded_by_repo_mode": contract_context["excluded_by_repo_mode"],
            "required_surface_deltas": required_surface_deltas,
            "required_surfaces_auto_apply": required_surfaces_auto_apply,
            "required_surfaces_at_risk": required_surfaces_at_risk,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root used to resolve relative artifact paths.",
    )
    parser.add_argument(
        "--plan-path",
        default="artifacts/blueprint/upgrade_plan.json",
        help="Upgrade plan JSON path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--apply-path",
        default="artifacts/blueprint/upgrade_apply.json",
        help="Upgrade apply JSON path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--output-path",
        default="artifacts/blueprint/upgrade_preflight.json",
        help="Preflight report output path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--reconcile-report-path",
        default=RECONCILE_REPORT_DEFAULT_PATH,
        help="Upgrade reconcile report path (absolute or repo-relative).",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    try:
        plan_path = _resolve_repo_scoped_path(repo_root, args.plan_path, "--plan-path")
        apply_path = _resolve_repo_scoped_path(repo_root, args.apply_path, "--apply-path")
        output_path = _resolve_repo_scoped_path(repo_root, args.output_path, "--output-path")
        reconcile_path = _resolve_repo_scoped_path(
            repo_root,
            args.reconcile_report_path,
            "--reconcile-report-path",
        )
        report = _build_report(
            repo_root=repo_root,
            plan_path=plan_path,
            apply_path=apply_path,
            reconcile_path=reconcile_path,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = report.get("summary", {})
    print(
        "upgrade preflight report: "
        f"{display_repo_path(repo_root, output_path)} "
        f"(auto_apply={summary.get('auto_apply_count', 0)} "
        f"manual_merge={summary.get('manual_merge_count', 0)} "
        f"conflicts={summary.get('conflict_count', 0)} "
        f"required_manual_actions={summary.get('required_manual_action_count', 0)} "
        f"required_surfaces_at_risk={summary.get('required_surface_at_risk_count', 0)} "
        f"merge_risk_blocking_buckets={summary.get('merge_risk_blocking_bucket_count', 0)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
