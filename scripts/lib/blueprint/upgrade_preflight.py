#!/usr/bin/env python3
"""Build a machine-readable preflight report from upgrade plan/apply artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402


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


def _build_report(
    *,
    repo_root: Path,
    plan_path: Path,
    apply_path: Path,
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
    }

    return {
        "plan_path": display_repo_path(repo_root, plan_path),
        "apply_path": display_repo_path(repo_root, apply_path),
        "summary": summary,
        "auto_apply": auto_apply,
        "manual_merge": manual_merge,
        "conflicts": conflicts,
        "skipped": skipped,
        "required_manual_actions": required_manual_actions,
        "required_follow_up_commands": required_follow_up_commands,
        "blocking_paths": blocking_paths,
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
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    try:
        plan_path = _resolve_repo_scoped_path(repo_root, args.plan_path, "--plan-path")
        apply_path = _resolve_repo_scoped_path(repo_root, args.apply_path, "--apply-path")
        output_path = _resolve_repo_scoped_path(repo_root, args.output_path, "--output-path")
        report = _build_report(repo_root=repo_root, plan_path=plan_path, apply_path=apply_path)
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
        f"required_manual_actions={summary.get('required_manual_action_count', 0)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
