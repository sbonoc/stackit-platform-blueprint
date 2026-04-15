#!/usr/bin/env python3
"""Orchestrate docs sync/check flows and optionally limit execution to changed-scope steps."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import resolve_repo_root  # noqa: E402


@dataclass(frozen=True)
class Step:
    name: str
    sync_cmd: tuple[str, ...]
    check_cmd: tuple[str, ...]
    triggers: tuple[str, ...]


PYTHON = sys.executable

STEPS: tuple[Step, ...] = (
    Step(
        name="blueprint-template",
        sync_cmd=(PYTHON, "scripts/lib/docs/sync_blueprint_template_docs.py"),
        check_cmd=(PYTHON, "scripts/lib/docs/sync_blueprint_template_docs.py", "--check"),
        triggers=("docs/README.md", "docs/blueprint/", "scripts/lib/docs/sync_blueprint_template_docs.py"),
    ),
    Step(
        name="platform-seed",
        sync_cmd=(PYTHON, "scripts/lib/docs/sync_platform_seed_docs.py"),
        check_cmd=(PYTHON, "scripts/lib/docs/sync_platform_seed_docs.py", "--check"),
        triggers=("docs/platform/", "scripts/lib/docs/sync_platform_seed_docs.py"),
    ),
    Step(
        name="core-targets",
        sync_cmd=(PYTHON, "scripts/bin/quality/render_core_targets_doc.py"),
        check_cmd=(PYTHON, "scripts/bin/quality/render_core_targets_doc.py", "--check"),
        triggers=(
            "make/blueprint.generated.mk",
            "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl",
            "scripts/bin/quality/render_core_targets_doc.py",
            "docs/reference/generated/core_targets.generated.md",
        ),
    ),
    Step(
        name="contract-metadata",
        sync_cmd=(
            PYTHON,
            "scripts/lib/docs/generate_contract_docs.py",
            "--contract",
            "blueprint/contract.yaml",
            "--modules-dir",
            "blueprint/modules",
            "--output",
            "docs/reference/generated/contract_metadata.generated.md",
        ),
        check_cmd=(
            PYTHON,
            "scripts/lib/docs/generate_contract_docs.py",
            "--contract",
            "blueprint/contract.yaml",
            "--modules-dir",
            "blueprint/modules",
            "--output",
            "docs/reference/generated/contract_metadata.generated.md",
            "--check",
        ),
        triggers=(
            "blueprint/contract.yaml",
            "blueprint/modules/",
            "scripts/lib/docs/generate_contract_docs.py",
            "docs/reference/generated/contract_metadata.generated.md",
        ),
    ),
    Step(
        name="runtime-identity-summary",
        sync_cmd=(PYTHON, "scripts/lib/docs/sync_runtime_identity_contract_summary.py"),
        check_cmd=(PYTHON, "scripts/lib/docs/sync_runtime_identity_contract_summary.py", "--check"),
        triggers=(
            "blueprint/runtime_identity_contract.yaml",
            "scripts/lib/docs/sync_runtime_identity_contract_summary.py",
            "docs/platform/consumer/runtime_credentials_eso.md",
            "scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md",
        ),
    ),
    Step(
        name="module-contract-summaries",
        sync_cmd=(PYTHON, "scripts/lib/docs/sync_module_contract_summaries.py"),
        check_cmd=(PYTHON, "scripts/lib/docs/sync_module_contract_summaries.py", "--check"),
        triggers=(
            "blueprint/modules/",
            "scripts/lib/docs/sync_module_contract_summaries.py",
            "docs/platform/modules/",
            "scripts/templates/blueprint/bootstrap/docs/platform/modules/",
        ),
    ),
)

STEP_BY_NAME = {step.name: step for step in STEPS}


def _run_git(repo_root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _resolve_base_ref(repo_root: Path, explicit_base_ref: str | None) -> str | None:
    candidates: list[str] = []
    if explicit_base_ref:
        candidates.append(explicit_base_ref)

    env_base_ref = os.environ.get("BLUEPRINT_DOCS_CHANGED_BASE_REF", "").strip()
    if env_base_ref:
        candidates.append(env_base_ref)

    github_base_ref = os.environ.get("GITHUB_BASE_REF", "").strip()
    if github_base_ref:
        # Prefer remote-tracking reference when available in CI checkouts.
        candidates.append(f"origin/{github_base_ref}")
        candidates.append(github_base_ref)

    # Deterministic fallback for default branch workflows.
    candidates.append("origin/main")

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if _run_git(repo_root, "rev-parse", "--verify", candidate):
            return candidate
    return None


def _changed_paths(repo_root: Path, *, base_ref: str | None = None) -> list[str]:
    paths: set[str] = set()
    for entry in _run_git(repo_root, "diff", "--name-only", "--relative", "HEAD"):
        paths.add(entry)
    for entry in _run_git(repo_root, "diff", "--name-only", "--relative", "--cached"):
        paths.add(entry)
    for entry in _run_git(repo_root, "ls-files", "--others", "--exclude-standard"):
        paths.add(entry)

    if paths:
        return sorted(paths)

    resolved_base_ref = _resolve_base_ref(repo_root, base_ref)
    if resolved_base_ref:
        for entry in _run_git(repo_root, "diff", "--name-only", "--relative", f"{resolved_base_ref}...HEAD"):
            paths.add(entry)

    return sorted(paths)


def _matches_trigger(path: str, trigger: str) -> bool:
    if trigger.endswith("/"):
        return path.startswith(trigger)
    return path == trigger


def _select_steps(*, step_names: list[str] | None, changed_only: bool, changed_paths: list[str]) -> list[Step]:
    if step_names:
        missing = [name for name in step_names if name not in STEP_BY_NAME]
        if missing:
            raise ValueError(f"unknown docs sync step(s): {', '.join(missing)}")
        selected = [STEP_BY_NAME[name] for name in step_names]
    else:
        selected = list(STEPS)

    if not changed_only:
        return selected

    filtered: list[Step] = []
    for step in selected:
        if any(_matches_trigger(path, trigger) for path in changed_paths for trigger in step.triggers):
            filtered.append(step)
    return filtered


def _run_step(repo_root: Path, step: Step, mode: str) -> int:
    cmd = step.sync_cmd if mode == "sync" else step.check_cmd
    print(f"[docs-orchestrator] step={step.name} mode={mode}")
    result = subprocess.run(list(cmd), cwd=repo_root, check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--mode", choices=("sync", "check"), required=True)
    parser.add_argument(
        "--step",
        action="append",
        dest="steps",
        help="Limit execution to one or more orchestrator step names.",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Run only steps whose configured triggers match changed repository paths.",
    )
    parser.add_argument(
        "--base-ref",
        help=(
            "Optional git base ref used for changed-scope detection in clean worktrees "
            "(for example origin/main or origin/<base-branch>)."
        ),
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    changed_paths = _changed_paths(repo_root, base_ref=args.base_ref) if args.changed_only else []
    steps = _select_steps(step_names=args.steps, changed_only=args.changed_only, changed_paths=changed_paths)

    if args.changed_only and not changed_paths and os.environ.get("CI", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        print("[docs-orchestrator] CI detected with empty changed-path set; falling back to all selected steps")
        steps = _select_steps(step_names=args.steps, changed_only=False, changed_paths=[])

    if args.changed_only:
        if changed_paths:
            print("[docs-orchestrator] changed paths:")
            for path in changed_paths:
                print(f"  - {path}")
        else:
            print("[docs-orchestrator] no changed paths detected")

    if not steps:
        print("[docs-orchestrator] no matching steps selected; nothing to do")
        return 0

    for step in steps:
        exit_code = _run_step(repo_root, step, args.mode)
        if exit_code != 0:
            return exit_code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
