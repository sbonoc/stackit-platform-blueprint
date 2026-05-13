#!/usr/bin/env python3
"""Apply conflict resolutions produced by the blueprint upgrade triage step."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402

_TRIAGE_PATH = "artifacts/blueprint/upgrade_triage.json"
_RESOLVE_PATH = "artifacts/blueprint/upgrade_resolve.json"
_CONFLICTS_DIR = "artifacts/blueprint/conflicts"
_TRIAGE_SCHEMA_PATH = Path(__file__).parent / "schemas" / "upgrade_triage.schema.json"
_RESIDUAL_TABLE_MAX_ROWS = 20


def _load_triage(repo_root: Path) -> dict[str, Any] | None:
    triage_path = repo_root / _TRIAGE_PATH
    if not triage_path.exists():
        print(
            f"upgrade-resolve: ERROR: triage file not found at {triage_path}; "
            "run the upgrade engine with apply enabled first",
            file=sys.stderr,
        )
        return None
    try:
        data = json.loads(triage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"upgrade-resolve: ERROR: triage file is not valid JSON: {exc}", file=sys.stderr)
        return None

    schema_path = _TRIAGE_SCHEMA_PATH
    if schema_path.exists():
        try:
            from tests._shared.json_schema import assert_json_matches_schema, load_json_schema
            schema = load_json_schema(schema_path)
            assert_json_matches_schema(data, schema)
        except AssertionError as exc:
            print(f"upgrade-resolve: ERROR: triage file failed schema validation: {exc}", file=sys.stderr)
            return None
        except ImportError:
            pass

    return data


def _read_conflict_artifact(repo_root: Path, rel_path: str) -> dict[str, Any] | None:
    artifact_path = repo_root / _CONFLICTS_DIR / f"{rel_path}.conflict.json"
    if not artifact_path.exists():
        return None
    try:
        return json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _apply_take(
    repo_root: Path,
    rel_path: str,
    content: str,
    *,
    dry_run: bool,
) -> str:
    target_path = repo_root / rel_path
    if target_path.exists() and target_path.read_text(encoding="utf-8") == content:
        return "already-resolved"
    if dry_run:
        return "dry-run"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")
    artifact_path = repo_root / _CONFLICTS_DIR / f"{rel_path}.conflict.json"
    if artifact_path.exists():
        artifact_path.unlink()
    return "applied"


def _resolve(
    repo_root: Path,
    *,
    dry_run: bool = False,
    accept_source_all: bool = False,
    accept_target_all: bool = False,
    interactive: bool = False,
) -> int:
    triage = _load_triage(repo_root)
    if triage is None:
        return 1

    conflicts: list[dict[str, Any]] = triage.get("conflicts", [])
    actions: list[dict[str, Any]] = []
    residual: list[dict[str, Any]] = []

    for entry in conflicts:
        rel_path = entry["path"]
        recommended = entry.get("recommended_action", "human_required")
        ownership_class = entry.get("ownership_class", "blueprint-managed")

        effective_action = recommended
        if recommended == "human_required":
            if accept_source_all:
                effective_action = "take_source"
            elif accept_target_all:
                effective_action = "take_target"
            elif interactive:
                effective_action = _prompt_interactive(rel_path, entry)
            else:
                residual.append(entry)
                actions.append({
                    "path": rel_path,
                    "action_taken": "skipped",
                    "result": "human_required",
                    "ownership_class": ownership_class,
                })
                continue

        artifact = _read_conflict_artifact(repo_root, rel_path)

        if effective_action == "take_source":
            if artifact is None:
                result = "already-resolved"
            else:
                content = artifact.get("source_content") or ""
                result = _apply_take(repo_root, rel_path, content, dry_run=dry_run)
            print(f"upgrade-resolve: take_source {rel_path}")
        elif effective_action == "take_target":
            if artifact is None:
                result = "already-resolved"
            else:
                content = artifact.get("target_content") or ""
                result = _apply_take(repo_root, rel_path, content, dry_run=dry_run)
            print(f"upgrade-resolve: take_target {rel_path}")
        elif effective_action == "delete":
            if dry_run:
                result = "dry-run"
            else:
                target_path = repo_root / rel_path
                if target_path.exists():
                    target_path.unlink()
                artifact_path = repo_root / _CONFLICTS_DIR / f"{rel_path}.conflict.json"
                if artifact_path.exists():
                    artifact_path.unlink()
                result = "applied"
            print(f"upgrade-resolve: delete {rel_path}")
        else:
            result = "skipped"

        actions.append({
            "path": rel_path,
            "action_taken": effective_action,
            "result": result,
            "ownership_class": ownership_class,
        })

    _print_residual_table(residual, repo_root)

    if not dry_run:
        resolve_path = repo_root / _RESOLVE_PATH
        resolve_path.parent.mkdir(parents=True, exist_ok=True)
        resolve_payload: dict[str, Any] = {
            "schema_version": 1,
            "triage_ref": _TRIAGE_PATH,
            "actions": actions,
            "summary": {
                "total": len(actions),
                "applied": sum(1 for a in actions if a["result"] == "applied"),
                "already_resolved": sum(1 for a in actions if a["result"] == "already-resolved"),
                "human_required": len(residual),
            },
        }
        resolve_path.write_text(f"{json.dumps(resolve_payload, indent=2, sort_keys=True)}\n", encoding="utf-8")
        print(f"upgrade-resolve: {display_repo_path(repo_root, resolve_path)}")

    return 0


def _prompt_interactive(rel_path: str, entry: dict[str, Any]) -> str:
    ownership_class = entry.get("ownership_class", "unknown")
    source_diff = entry.get("source_diff_summary", "?")
    target_diff = entry.get("target_diff_from_baseline", "?")
    print(f"\nConflict: {rel_path}")
    print(f"  ownership: {ownership_class}  source: {source_diff}  target vs baseline: {target_diff}")
    print("  [s]ource / [t]arget / [k]eep (human_required): ", end="", flush=True)
    try:
        choice = input().strip().lower()
    except EOFError:
        choice = "k"
    if choice in ("s", "source"):
        return "take_source"
    if choice in ("t", "target"):
        return "take_target"
    return "human_required"


def _print_residual_table(residual: list[dict[str, Any]], repo_root: Path) -> None:
    if not residual:
        return
    sorted_residual = sorted(residual, key=lambda e: (e.get("ownership_class", ""), e.get("path", "")))
    display = sorted_residual[:_RESIDUAL_TABLE_MAX_ROWS]
    truncated = len(sorted_residual) - len(display)

    print(f"\nResidual conflicts requiring human review ({len(sorted_residual)} total):")
    print(f"  {'PATH':<55} {'OWNERSHIP':<25} {'SRC DIFF':<15} {'TGT DIFF'}")
    print(f"  {'-'*55} {'-'*25} {'-'*15} {'-'*15}")
    for entry in display:
        path = entry.get("path", "")
        oc = entry.get("ownership_class", "")
        src = entry.get("source_diff_summary", "")
        tgt = entry.get("target_diff_from_baseline", "")
        print(f"  {path:<55} {oc:<25} {src:<15} {tgt}")
    if truncated > 0:
        triage_path = repo_root / _TRIAGE_PATH
        print(
            f"\n  ... and {truncated} more rows. "
            f"Full triage at: {display_repo_path(repo_root, triage_path)}"
        )
        print(f"  Total human_required: {len(sorted_residual)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply blueprint upgrade conflict resolutions.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without writing files.")
    parser.add_argument(
        "--accept-source",
        metavar="ALL",
        help="Batch-apply source content for all human_required rows (pass ALL).",
    )
    parser.add_argument(
        "--accept-target",
        metavar="ALL",
        help="Batch-apply target content for all human_required rows (pass ALL).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=os.environ.get("INTERACTIVE", "").lower() in ("true", "1", "yes"),
        help="Prompt for each human_required row (or set INTERACTIVE=true).",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root()
    return _resolve(
        repo_root,
        dry_run=args.dry_run,
        accept_source_all=(args.accept_source or "").upper() == "ALL",
        accept_target_all=(args.accept_target or "").upper() == "ALL",
        interactive=args.interactive,
    )


if __name__ == "__main__":
    sys.exit(main())
