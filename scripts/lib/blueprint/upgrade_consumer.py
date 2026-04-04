#!/usr/bin/env python3
"""Plan/apply non-destructive upgrades for generated-consumer repositories."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import BlueprintContract, load_blueprint_contract  # noqa: E402
from scripts.lib.blueprint.init_repo_contract import expand_optional_module_path  # noqa: E402
from scripts.lib.blueprint.merge_markers import find_merge_markers  # noqa: E402
from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES  # noqa: E402


ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_MERGE_REQUIRED = "merge-required"
ACTION_SKIP = "skip"
ACTION_CONFLICT = "conflict"

OPERATION_CREATE = "create"
OPERATION_UPDATE = "update"
OPERATION_DELETE = "delete"
OPERATION_MERGE = "merge"
OPERATION_NONE = "none"

REASON_PLATFORM_PROTECTED_SKIP = "path is platform-owned and protected from blueprint-managed overwrite"
MAKE_TARGET_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+):")
BLUEPRINT_MAKE_TARGET_REFERENCE_PATHS = (
    ".github/actions/prepare-blueprint-ci/action.yml",
    ".github/workflows/ci.yml",
    "make/blueprint.generated.mk",
    "scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl",
    "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl",
)
APPS_CI_BOOTSTRAP_TARGET = "apps-ci-bootstrap"
APPS_CI_BOOTSTRAP_CONSUMER_TARGET = "apps-ci-bootstrap-consumer"
APPS_CI_BOOTSTRAP_CONSUMER_PLACEHOLDER_TOKEN = "apps-ci-bootstrap-consumer placeholder active"


@dataclass(frozen=True)
class UpgradeEntry:
    path: str
    ownership: str
    action: str
    operation: str
    reason: str
    source_exists: bool
    target_exists: bool
    baseline_ref: str | None
    baseline_content_available: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "ownership": self.ownership,
            "action": self.action,
            "operation": self.operation,
            "reason": self.reason,
            "source_exists": self.source_exists,
            "target_exists": self.target_exists,
            "baseline_ref": self.baseline_ref,
            "baseline_content_available": self.baseline_content_available,
        }


@dataclass(frozen=True)
class ApplyResult:
    path: str
    planned_action: str
    planned_operation: str
    result: str
    reason: str
    conflict_artifact: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "path": self.path,
            "planned_action": self.planned_action,
            "planned_operation": self.planned_operation,
            "result": self.result,
            "reason": self.reason,
        }
        if self.conflict_artifact:
            payload["conflict_artifact"] = self.conflict_artifact
        return payload


@dataclass(frozen=True)
class RequiredManualAction:
    dependency_path: str
    dependency_of: str
    reason: str
    required_follow_up_commands: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "dependency_path": self.dependency_path,
            "dependency_of": self.dependency_of,
            "reason": self.reason,
            "required_follow_up_commands": list(self.required_follow_up_commands),
        }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None, help="Repository root path.")
    parser.add_argument("--source", required=True, help="Blueprint source repository URL/path.")
    parser.add_argument("--ref", required=True, help="Upgrade source ref (tag/branch/commit).")
    parser.add_argument("--apply", action="store_true", help="Apply plan actions.")
    parser.add_argument("--allow-dirty", action="store_true", help="Allow running with dirty worktree.")
    parser.add_argument("--allow-delete", action="store_true", help="Allow delete operations.")
    parser.add_argument(
        "--plan-path",
        default="artifacts/blueprint/upgrade_plan.json",
        help="Upgrade plan report path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--apply-path",
        default="artifacts/blueprint/upgrade_apply.json",
        help="Upgrade apply report path (absolute or repo-relative).",
    )
    parser.add_argument(
        "--summary-path",
        default="artifacts/blueprint/upgrade_summary.md",
        help="Upgrade human summary path (absolute or repo-relative).",
    )
    return parser.parse_args()


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", *args], cwd=repo_root)


def _ensure_git_repo(repo_root: Path) -> None:
    result = _run_git(repo_root, "rev-parse", "--is-inside-work-tree")
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise RuntimeError(f"repository is not a git worktree: {repo_root}")


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


def _path_is_within(path: str, root: str) -> bool:
    normalized_path = path.strip("/")
    normalized_root = root.strip("/")
    if not normalized_root:
        return False
    return normalized_path == normalized_root or normalized_path.startswith(f"{normalized_root}/")


def _entry_looks_like_dir(path_value: str) -> bool:
    normalized = path_value.rstrip("/")
    if path_value.endswith("/"):
        return True
    return Path(normalized).suffix == ""


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="surrogateescape")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _copy_permissions(from_path: Path, to_path: Path) -> None:
    source_mode = from_path.stat().st_mode
    # Preserve rwx permission bits so new scripts keep executable mode.
    os.chmod(to_path, source_mode & 0o777)


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8", "surrogateescape")).hexdigest()


def _repo_is_dirty(repo_root: Path) -> bool:
    result = _run_git(repo_root, "status", "--porcelain")
    return result.returncode == 0 and bool(result.stdout.strip())


def _expand_contract_paths(values: list[str]) -> list[str]:
    expanded: list[str] = []
    for value in values:
        expanded.extend(expand_optional_module_path(value))
    return expanded


def _collect_files_under(root: Path, rel_root: str) -> set[str]:
    absolute_root = root / rel_root.strip("/")
    if absolute_root.is_file():
        return {rel_root.strip("/")}
    if not absolute_root.is_dir():
        return set()
    return {
        path.relative_to(root).as_posix()
        for path in absolute_root.rglob("*")
        if path.is_file()
    }


def _resolve_baseline_ref(source_repo: Path, template_version: str) -> str | None:
    candidates = [f"v{template_version}", template_version]
    for candidate in candidates:
        result = _run_git(source_repo, "rev-parse", "-q", "--verify", f"{candidate}^{{commit}}")
        if result.returncode == 0:
            return candidate
    return None


def _resolve_commit(source_repo: Path, ref: str) -> str | None:
    result = _run_git(source_repo, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}")
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _clone_source_repository(source: str, ref: str) -> tuple[Path, Path, str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="blueprint-upgrade-source-"))
    source_repo = temp_dir / "source"

    clone = _run(["git", "clone", "--quiet", source, str(source_repo)])
    if clone.returncode != 0:
        raise RuntimeError(f"failed cloning source repository {source}: {clone.stderr.strip()}")

    checkout = _run_git(source_repo, "checkout", "--detach", ref)
    if checkout.returncode != 0:
        raise RuntimeError(f"failed checking out ref {ref}: {checkout.stderr.strip()}")

    resolved = _run_git(source_repo, "rev-parse", "HEAD")
    if resolved.returncode != 0:
        raise RuntimeError(f"failed resolving source HEAD for ref {ref}: {resolved.stderr.strip()}")
    return temp_dir, source_repo, resolved.stdout.strip()


def _contract_paths(contract: BlueprintContract) -> tuple[set[str], set[str], set[str], set[str], set[str]]:
    required_files = set(contract.repository.required_files)
    source_only = set(contract.repository.source_only_paths)
    consumer_seeded = set(contract.repository.consumer_seeded_paths)
    init_managed = set(_expand_contract_paths(contract.repository.init_managed_paths))
    conditional = set(_expand_contract_paths(contract.repository.conditional_scaffold_paths))
    return required_files, source_only, consumer_seeded, init_managed, conditional


def _managed_roots(contract: BlueprintContract) -> set[str]:
    return {root.rstrip("/") for root in contract.script_contract.blueprint_managed_roots}


def _merge_path_sets(*path_sets: set[str]) -> set[str]:
    merged: set[str] = set()
    for path_set in path_sets:
        merged.update(path_set)
    return merged


def _protected_roots(contract: BlueprintContract, source_contract: BlueprintContract | None = None) -> set[str]:
    def roots_for(value: BlueprintContract) -> set[str]:
        ownership = value.make_contract.ownership
        roots = set(value.script_contract.platform_editable_roots)
        roots.add(ownership.platform_editable_file)
        roots.add(ownership.platform_editable_include_dir)
        roots.add(value.docs_contract.platform_docs.root)
        return {root.rstrip("/") for root in roots}

    roots = roots_for(contract)
    if source_contract is not None:
        roots.update(roots_for(source_contract))
    return roots


def _collect_candidate_paths(
    repo_root: Path,
    source_repo: Path,
    managed_dir_roots: set[str],
    required_files: set[str],
    init_managed: set[str],
    conditional_entries: set[str],
) -> tuple[set[str], set[str], set[str]]:
    explicit_file_paths: set[str] = set(required_files | init_managed)
    managed_roots = set(managed_dir_roots)

    for entry in conditional_entries:
        normalized = entry.rstrip("/")
        source_candidate = source_repo / normalized
        target_candidate = repo_root / normalized
        if source_candidate.is_dir() or target_candidate.is_dir() or _entry_looks_like_dir(entry):
            managed_roots.add(normalized)
        else:
            explicit_file_paths.add(normalized)

    source_files: set[str] = set()
    target_files: set[str] = set()
    for root in sorted(managed_roots):
        source_files.update(_collect_files_under(source_repo, root))
        target_files.update(_collect_files_under(repo_root, root))

    for relative in explicit_file_paths:
        source_path = source_repo / relative
        if source_path.is_file():
            source_files.add(relative)
        target_path = repo_root / relative
        if target_path.is_file():
            target_files.add(relative)

    return source_files, target_files, managed_roots


def _ownership_class(
    relative_path: str,
    required_files: set[str],
    init_managed: set[str],
    conditional_entries: set[str],
    managed_dir_roots: set[str],
) -> str:
    if relative_path in init_managed:
        return "init-managed"
    if relative_path in conditional_entries:
        return "conditional-scaffold"
    if any(_path_is_within(relative_path, entry) for entry in conditional_entries if _entry_looks_like_dir(entry)):
        return "conditional-scaffold"
    if relative_path in required_files:
        return "required-file"
    if any(_path_is_within(relative_path, root) for root in managed_dir_roots):
        return "blueprint-managed-root"
    return "blueprint-managed"


def _classify_entries(
    *,
    repo_root: Path,
    source_repo: Path,
    all_paths: list[str],
    required_files: set[str],
    source_only: set[str],
    consumer_seeded: set[str],
    init_managed: set[str],
    conditional_entries: set[str],
    managed_dir_roots: set[str],
    protected_roots: set[str],
    baseline_ref: str | None,
    baseline_cache: dict[str, str | None],
    allow_delete: bool,
) -> list[UpgradeEntry]:
    entries: list[UpgradeEntry] = []

    def resolve_baseline_content(path: str) -> str | None:
        if baseline_ref is None:
            return None
        if path not in baseline_cache:
            show = _run_git(source_repo, "show", f"{baseline_ref}:{path}")
            baseline_cache[path] = show.stdout if show.returncode == 0 else None
        return baseline_cache[path]

    for relative_path in all_paths:
        ownership = _ownership_class(relative_path, required_files, init_managed, conditional_entries, managed_dir_roots)
        source_path = source_repo / relative_path
        target_path = repo_root / relative_path
        source_exists = source_path.is_file()
        target_exists = target_path.is_file()

        if any(_path_is_within(relative_path, root) for root in source_only):
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership="source-only",
                    action=ACTION_SKIP,
                    operation=OPERATION_NONE,
                    reason="path is source-only in repository ownership contract",
                    source_exists=source_exists,
                    target_exists=target_exists,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        if relative_path in consumer_seeded:
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership="consumer-seeded",
                    action=ACTION_SKIP,
                    operation=OPERATION_NONE,
                    reason="path is consumer-owned and excluded from blueprint upgrade apply",
                    source_exists=source_exists,
                    target_exists=target_exists,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        if any(_path_is_within(relative_path, root) for root in protected_roots):
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership=ownership,
                    action=ACTION_SKIP,
                    operation=OPERATION_NONE,
                    reason=REASON_PLATFORM_PROTECTED_SKIP,
                    source_exists=source_exists,
                    target_exists=target_exists,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        if not source_exists and target_exists:
            if allow_delete:
                entries.append(
                    UpgradeEntry(
                        path=relative_path,
                        ownership=ownership,
                        action=ACTION_UPDATE,
                        operation=OPERATION_DELETE,
                        reason="path absent in upgrade source; delete enabled by explicit opt-in",
                        source_exists=False,
                        target_exists=True,
                        baseline_ref=baseline_ref,
                        baseline_content_available=False,
                    )
                )
            else:
                entries.append(
                    UpgradeEntry(
                        path=relative_path,
                        ownership=ownership,
                        action=ACTION_SKIP,
                        operation=OPERATION_DELETE,
                        reason="path absent in upgrade source; deletion skipped (set BLUEPRINT_UPGRADE_ALLOW_DELETE=true)",
                        source_exists=False,
                        target_exists=True,
                        baseline_ref=baseline_ref,
                        baseline_content_available=False,
                    )
                )
            continue

        if source_exists and not target_exists:
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership=ownership,
                    action=ACTION_CREATE,
                    operation=OPERATION_CREATE,
                    reason="path exists in upgrade source and is missing locally",
                    source_exists=True,
                    target_exists=False,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        if not source_exists and not target_exists:
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership=ownership,
                    action=ACTION_SKIP,
                    operation=OPERATION_NONE,
                    reason="path absent in both source and target repositories",
                    source_exists=False,
                    target_exists=False,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        source_content = _read_text(source_path)
        target_content = _read_text(target_path)
        if source_content == target_content:
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership=ownership,
                    action=ACTION_SKIP,
                    operation=OPERATION_NONE,
                    reason="path already matches upgrade source content",
                    source_exists=True,
                    target_exists=True,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        if baseline_ref is None:
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership=ownership,
                    action=ACTION_CONFLICT,
                    operation=OPERATION_MERGE,
                    reason=(
                        "unable to resolve baseline ref from template version; "
                        "cannot perform required 3-way merge safely"
                    ),
                    source_exists=True,
                    target_exists=True,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        baseline_content = resolve_baseline_content(relative_path)
        if baseline_content is None:
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership=ownership,
                    action=ACTION_CONFLICT,
                    operation=OPERATION_MERGE,
                    reason=(
                        f"path not present at baseline ref {baseline_ref}; "
                        "manual conflict resolution required"
                    ),
                    source_exists=True,
                    target_exists=True,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        if target_content == baseline_content:
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership=ownership,
                    action=ACTION_UPDATE,
                    operation=OPERATION_UPDATE,
                    reason=f"path matches baseline ref {baseline_ref}; safe update",
                    source_exists=True,
                    target_exists=True,
                    baseline_ref=baseline_ref,
                    baseline_content_available=True,
                )
            )
            continue

        entries.append(
            UpgradeEntry(
                path=relative_path,
                ownership=ownership,
                action=ACTION_MERGE_REQUIRED,
                operation=OPERATION_MERGE,
                reason=f"path diverged from baseline ref {baseline_ref}; 3-way merge required",
                source_exists=True,
                target_exists=True,
                baseline_ref=baseline_ref,
                baseline_content_available=True,
            )
        )

    return entries


def _required_manual_follow_up_commands(path: str) -> tuple[str, ...]:
    commands: list[str] = []
    if path.startswith("docs/platform/"):
        commands.append("make blueprint-bootstrap")
    commands.append("make blueprint-upgrade-consumer-validate")
    return tuple(commands)


def _source_file_references_dependency(source_repo: Path, depender_path: str, dependency_path: str) -> bool:
    depender_file = source_repo / depender_path
    if not depender_file.is_file():
        return False
    return dependency_path in _read_text(depender_file)


def _annotate_protected_dependency_gaps(
    entries: list[UpgradeEntry],
    source_repo: Path,
    protected_roots: set[str],
) -> tuple[list[UpgradeEntry], list[RequiredManualAction]]:
    entries_by_path = {entry.path: entry for entry in entries}
    annotated: list[UpgradeEntry] = []
    required_manual_actions: list[RequiredManualAction] = []
    seen_manual_actions: set[tuple[str, str]] = set()

    for entry in entries:
        reason = entry.reason
        for depender_path, dependency_path in RUNTIME_DEPENDENCY_EDGES:
            if entry.path != dependency_path:
                continue
            if entry.action != ACTION_SKIP:
                continue
            if entry.target_exists or not entry.source_exists:
                continue
            if not any(_path_is_within(entry.path, root) for root in protected_roots):
                continue
            if entry.reason != REASON_PLATFORM_PROTECTED_SKIP:
                continue
            depender_entry = entries_by_path.get(depender_path)
            if depender_entry is None or not depender_entry.source_exists:
                continue
            if not _source_file_references_dependency(source_repo, depender_path, dependency_path):
                continue
            manual_action_key = (depender_path, dependency_path)
            if manual_action_key not in seen_manual_actions:
                seen_manual_actions.add(manual_action_key)
                required_manual_actions.append(
                    RequiredManualAction(
                        dependency_path=dependency_path,
                        dependency_of=depender_path,
                        reason=(
                            f"{depender_path} references {dependency_path} and upgrade validation "
                            "will fail until the dependency file exists"
                        ),
                        required_follow_up_commands=_required_manual_follow_up_commands(dependency_path),
                    )
                )
            reason = (
                f"{entry.reason}; required-manual-action: {depender_path} references {dependency_path} "
                "and upgrade validation will fail until the dependency file exists"
            )
            break

        if reason == entry.reason:
            annotated.append(entry)
            continue

        annotated.append(
            UpgradeEntry(
                path=entry.path,
                ownership=entry.ownership,
                action=entry.action,
                operation=entry.operation,
                reason=reason,
                source_exists=entry.source_exists,
                target_exists=entry.target_exists,
                baseline_ref=entry.baseline_ref,
                baseline_content_available=entry.baseline_content_available,
            )
        )

    return annotated, required_manual_actions


def _collect_platform_make_paths(root: Path, contract: BlueprintContract) -> list[tuple[str, Path]]:
    ownership = contract.make_contract.ownership
    paths: list[tuple[str, Path]] = []

    editable_file = ownership.platform_editable_file.strip()
    if editable_file:
        editable_path = root / editable_file
        if editable_path.is_file():
            paths.append((editable_file, editable_path))

    editable_include_dir = ownership.platform_editable_include_dir.strip()
    if editable_include_dir:
        include_root = root / editable_include_dir
        if include_root.is_dir():
            for include_file in sorted(include_root.rglob("*.mk")):
                if not include_file.is_file():
                    continue
                rel_path = include_file.relative_to(root).as_posix()
                paths.append((rel_path, include_file))

    deduped: list[tuple[str, Path]] = []
    seen_rel_paths: set[str] = set()
    for rel_path, abs_path in paths:
        if rel_path in seen_rel_paths:
            continue
        seen_rel_paths.add(rel_path)
        deduped.append((rel_path, abs_path))
    return deduped


def _make_target_definitions(paths: list[tuple[str, Path]]) -> dict[str, str]:
    definitions: dict[str, str] = {}
    for rel_path, abs_path in paths:
        for line in _read_text(abs_path).splitlines():
            match = MAKE_TARGET_PATTERN.match(line)
            if not match:
                continue
            target_name = match.group(1)
            if target_name == ".PHONY":
                continue
            definitions.setdefault(target_name, rel_path)
    return definitions


def _file_contains_literal(path: Path, token: str) -> bool:
    if not path.is_file():
        return False
    return token in _read_text(path)


def _source_make_target_reference(source_repo: Path, target_name: str) -> str | None:
    needles = (f"make {target_name}", f"$(MAKE) {target_name}")
    for rel_path in BLUEPRINT_MAKE_TARGET_REFERENCE_PATHS:
        abs_path = source_repo / rel_path
        if not abs_path.is_file():
            continue
        content = _read_text(abs_path)
        if any(needle in content for needle in needles):
            return rel_path
    return None


def _collect_missing_platform_make_target_actions(
    repo_root: Path,
    source_repo: Path,
    contract: BlueprintContract,
    source_contract: BlueprintContract | None,
) -> list[RequiredManualAction]:
    source_scope_contract = source_contract or contract
    source_target_definitions = _make_target_definitions(_collect_platform_make_paths(source_repo, source_scope_contract))
    if not source_target_definitions:
        return []

    target_target_definitions = _make_target_definitions(_collect_platform_make_paths(repo_root, contract))
    target_targets = set(target_target_definitions.keys())
    required_targets = set(source_scope_contract.make_contract.required_targets)
    platform_makefile = contract.make_contract.ownership.platform_editable_file

    actions: list[RequiredManualAction] = []
    for target_name in sorted(source_target_definitions.keys()):
        if target_name not in required_targets:
            continue
        if target_name in target_targets:
            continue
        reference_path = _source_make_target_reference(source_repo, target_name)
        if reference_path is None:
            continue
        actions.append(
            RequiredManualAction(
                dependency_path=platform_makefile,
                dependency_of=f"{reference_path}: make {target_name}",
                reason=(
                    f"required make target `{target_name}` is missing from platform-owned make surfaces; "
                    f"{reference_path} invokes it and validation will fail until the target is added"
                ),
                required_follow_up_commands=("make blueprint-upgrade-consumer-validate",),
            )
        )

    if APPS_CI_BOOTSTRAP_TARGET in target_targets and APPS_CI_BOOTSTRAP_CONSUMER_TARGET in required_targets:
        bootstrap_reference_path = _source_make_target_reference(source_repo, APPS_CI_BOOTSTRAP_TARGET) or platform_makefile
        bootstrap_dependency_of = f"{bootstrap_reference_path}: make {APPS_CI_BOOTSTRAP_TARGET}"
        consumer_target_path = target_target_definitions.get(APPS_CI_BOOTSTRAP_CONSUMER_TARGET)
        if consumer_target_path is None:
            actions.append(
                RequiredManualAction(
                    dependency_path=platform_makefile,
                    dependency_of=bootstrap_dependency_of,
                    reason=(
                        f"required consumer-owned make target `{APPS_CI_BOOTSTRAP_CONSUMER_TARGET}` is missing; "
                        f"`{APPS_CI_BOOTSTRAP_TARGET}` invokes it and CI dependency bootstrap cannot be completed "
                        "until the target is implemented"
                    ),
                    required_follow_up_commands=("make blueprint-upgrade-consumer-validate",),
                )
            )
        elif _file_contains_literal(
            repo_root / consumer_target_path,
            APPS_CI_BOOTSTRAP_CONSUMER_PLACEHOLDER_TOKEN,
        ):
            actions.append(
                RequiredManualAction(
                    dependency_path=consumer_target_path,
                    dependency_of=bootstrap_dependency_of,
                    reason=(
                        f"required consumer-owned make target `{APPS_CI_BOOTSTRAP_CONSUMER_TARGET}` is still "
                        "placeholder; replace it with deterministic repository-specific dependency bootstrap commands"
                    ),
                    required_follow_up_commands=("make blueprint-upgrade-consumer-validate",),
                )
            )
    return actions


def _merge_required_manual_actions(*groups: list[RequiredManualAction]) -> list[RequiredManualAction]:
    merged: list[RequiredManualAction] = []
    seen: set[tuple[str, str, str, tuple[str, ...]]] = set()
    for actions in groups:
        for action in actions:
            key = (
                action.dependency_path,
                action.dependency_of,
                action.reason,
                action.required_follow_up_commands,
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(action)
    return merged


def _three_way_merge(base: str, ours: str, theirs: str) -> tuple[str, bool]:
    with tempfile.TemporaryDirectory(prefix="blueprint-upgrade-merge-") as tmpdir:
        tmp_root = Path(tmpdir)
        ours_path = tmp_root / "ours"
        base_path = tmp_root / "base"
        theirs_path = tmp_root / "theirs"
        _write_text(ours_path, ours)
        _write_text(base_path, base)
        _write_text(theirs_path, theirs)

        merge = _run(["git", "merge-file", "-p", str(ours_path), str(base_path), str(theirs_path)])
        if merge.returncode < 0:
            raise RuntimeError(f"git merge-file failed: {merge.stderr.strip()}")
        # `git merge-file` may return conflict counts greater than 1 when multiple
        # conflict hunks are present. Any positive code means conflicts were detected.
        return merge.stdout, merge.returncode > 0


def _write_conflict_artifact(
    repo_root: Path,
    relative_path: str,
    reason: str,
    source_content: str,
    target_content: str,
    baseline_content: str | None = None,
    merged_content: str | None = None,
) -> str:
    artifact_root = repo_root / "artifacts/blueprint/conflicts"
    artifact_path = artifact_root / f"{relative_path}.conflict.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "path": relative_path,
        "reason": reason,
        "source_sha256": _content_hash(source_content),
        "target_sha256": _content_hash(target_content),
        "baseline_sha256": _content_hash(baseline_content) if baseline_content is not None else None,
        "merged_sha256": _content_hash(merged_content) if merged_content is not None else None,
        "source_content": source_content,
        "target_content": target_content,
        "baseline_content": baseline_content,
        "merged_content": merged_content,
    }
    artifact_path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")
    return display_repo_path(repo_root, artifact_path)


def _apply_entries(
    repo_root: Path,
    source_repo: Path,
    entries: list[UpgradeEntry],
    baseline_cache: dict[str, str | None],
    apply_enabled: bool,
) -> tuple[list[ApplyResult], int]:
    results: list[ApplyResult] = []
    applied_count = 0

    for entry in entries:
        source_path = source_repo / entry.path
        target_path = repo_root / entry.path

        if not apply_enabled:
            results.append(
                ApplyResult(
                    path=entry.path,
                    planned_action=entry.action,
                    planned_operation=entry.operation,
                    result="planned-only",
                    reason="apply mode disabled",
                )
            )
            continue

        if entry.action == ACTION_SKIP:
            results.append(
                ApplyResult(
                    path=entry.path,
                    planned_action=entry.action,
                    planned_operation=entry.operation,
                    result="skipped",
                    reason=entry.reason,
                )
            )
            continue

        if entry.action == ACTION_CONFLICT:
            source_content = _read_text(source_path) if source_path.is_file() else ""
            target_content = _read_text(target_path) if target_path.is_file() else ""
            conflict_artifact = _write_conflict_artifact(
                repo_root,
                entry.path,
                entry.reason,
                source_content,
                target_content,
                baseline_content=baseline_cache.get(entry.path),
            )
            results.append(
                ApplyResult(
                    path=entry.path,
                    planned_action=entry.action,
                    planned_operation=entry.operation,
                    result="conflict",
                    reason=entry.reason,
                    conflict_artifact=conflict_artifact,
                )
            )
            continue

        if entry.action == ACTION_CREATE or (entry.action == ACTION_UPDATE and entry.operation == OPERATION_UPDATE):
            if not source_path.is_file():
                results.append(
                    ApplyResult(
                        path=entry.path,
                        planned_action=entry.action,
                        planned_operation=entry.operation,
                        result="skipped",
                        reason="source file missing at apply-time",
                    )
                )
                continue
            _write_text(target_path, _read_text(source_path))
            _copy_permissions(source_path, target_path)
            applied_count += 1
            results.append(
                ApplyResult(
                    path=entry.path,
                    planned_action=entry.action,
                    planned_operation=entry.operation,
                    result="applied",
                    reason="source content applied",
                )
            )
            continue

        if entry.action == ACTION_UPDATE and entry.operation == OPERATION_DELETE:
            if target_path.exists():
                target_path.unlink()
                applied_count += 1
                results.append(
                    ApplyResult(
                        path=entry.path,
                        planned_action=entry.action,
                        planned_operation=entry.operation,
                        result="deleted",
                        reason="path removed because deletion was explicitly enabled",
                    )
                )
            else:
                results.append(
                    ApplyResult(
                        path=entry.path,
                        planned_action=entry.action,
                        planned_operation=entry.operation,
                        result="skipped",
                        reason="target path already absent",
                    )
                )
            continue

        if entry.action == ACTION_MERGE_REQUIRED:
            source_content = _read_text(source_path)
            target_content = _read_text(target_path)
            baseline_content = baseline_cache.get(entry.path)
            if baseline_content is None:
                conflict_artifact = _write_conflict_artifact(
                    repo_root,
                    entry.path,
                    "baseline content unavailable during apply; cannot 3-way merge",
                    source_content,
                    target_content,
                )
                results.append(
                    ApplyResult(
                        path=entry.path,
                        planned_action=entry.action,
                        planned_operation=entry.operation,
                        result="conflict",
                        reason="baseline content unavailable",
                        conflict_artifact=conflict_artifact,
                    )
                )
                continue

            merged_content, has_conflicts = _three_way_merge(baseline_content, target_content, source_content)
            if has_conflicts:
                conflict_artifact = _write_conflict_artifact(
                    repo_root,
                    entry.path,
                    "3-way merge produced conflicts",
                    source_content,
                    target_content,
                    baseline_content=baseline_content,
                    merged_content=merged_content,
                )
                results.append(
                    ApplyResult(
                        path=entry.path,
                        planned_action=entry.action,
                        planned_operation=entry.operation,
                        result="conflict",
                        reason="3-way merge conflict",
                        conflict_artifact=conflict_artifact,
                    )
                )
                continue

            _write_text(target_path, merged_content)
            applied_count += 1
            results.append(
                ApplyResult(
                    path=entry.path,
                    planned_action=entry.action,
                    planned_operation=entry.operation,
                    result="merged",
                    reason="3-way merge applied cleanly",
                )
            )
            continue

        results.append(
            ApplyResult(
                path=entry.path,
                planned_action=entry.action,
                planned_operation=entry.operation,
                result="skipped",
                reason=f"unsupported action {entry.action}",
            )
        )

    return results, applied_count


def _summarize_plan(
    entries: list[UpgradeEntry],
    required_manual_actions: list[RequiredManualAction],
) -> dict[str, int]:
    counts = {
        ACTION_CREATE: 0,
        ACTION_UPDATE: 0,
        ACTION_MERGE_REQUIRED: 0,
        ACTION_SKIP: 0,
        ACTION_CONFLICT: 0,
    }
    for entry in entries:
        counts[entry.action] = counts.get(entry.action, 0) + 1
    counts["total"] = len(entries)
    counts["required_manual_action_count"] = len(required_manual_actions)
    return counts


def _summarize_apply(
    results: list[ApplyResult],
    applied_count: int,
    required_manual_actions: list[RequiredManualAction],
) -> dict[str, int]:
    counts: dict[str, int] = {"total": len(results), "applied_count": applied_count}
    for result in results:
        counts[result.result] = counts.get(result.result, 0) + 1
    counts["required_manual_action_count"] = len(required_manual_actions)
    return counts


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")


def _write_summary(
    *,
    summary_path: Path,
    repo_root: Path,
    source: str,
    ref: str,
    resolved_commit: str,
    baseline_ref: str | None,
    plan_summary: dict[str, int],
    apply_summary: dict[str, int],
    apply_enabled: bool,
    results: list[ApplyResult],
    required_manual_actions: list[RequiredManualAction],
) -> None:
    conflict_results = [result for result in results if result.result == "conflict"]
    lines = [
        "# Blueprint Consumer Upgrade Summary",
        "",
        f"- Source: `{source}`",
        f"- Upgrade Ref: `{ref}`",
        f"- Resolved Commit: `{resolved_commit}`",
        f"- Baseline Ref: `{baseline_ref or 'unresolved'}`",
        f"- Apply Enabled: `{str(apply_enabled).lower()}`",
        "",
        "## Plan Summary",
        "",
        "| Action | Count |",
        "| --- | ---: |",
        f"| {ACTION_CREATE} | {plan_summary.get(ACTION_CREATE, 0)} |",
        f"| {ACTION_UPDATE} | {plan_summary.get(ACTION_UPDATE, 0)} |",
        f"| {ACTION_MERGE_REQUIRED} | {plan_summary.get(ACTION_MERGE_REQUIRED, 0)} |",
        f"| {ACTION_SKIP} | {plan_summary.get(ACTION_SKIP, 0)} |",
        f"| {ACTION_CONFLICT} | {plan_summary.get(ACTION_CONFLICT, 0)} |",
        f"| total | {plan_summary.get('total', 0)} |",
        "",
        f"- Required manual actions: `{plan_summary.get('required_manual_action_count', 0)}`",
        "",
        "## Apply Summary",
        "",
        "| Result | Count |",
        "| --- | ---: |",
    ]

    result_keys = sorted(
        key for key in apply_summary if key not in ("total", "applied_count", "required_manual_action_count")
    )
    for key in result_keys:
        lines.append(f"| {key} | {apply_summary[key]} |")
    lines.append(f"| total | {apply_summary.get('total', 0)} |")
    lines.append("")
    lines.append(f"- Applied paths: `{apply_summary.get('applied_count', 0)}`")
    lines.append(f"- Required manual actions: `{apply_summary.get('required_manual_action_count', 0)}`")

    if required_manual_actions:
        lines.extend(["", "## Required Manual Actions", ""])
        for action in required_manual_actions:
            follow_up_commands = ", ".join(f"`{command}`" for command in action.required_follow_up_commands)
            lines.append(
                f"- `{action.dependency_path}` required by `{action.dependency_of}`: {action.reason}. "
                f"Follow-up: {follow_up_commands}"
            )

    if conflict_results:
        lines.extend(
            [
                "",
                "## Conflicts",
                "",
            ]
        )
        for result in conflict_results:
            artifact = result.conflict_artifact or "n/a"
            lines.append(f"- `{result.path}`: {result.reason} (artifact: `{artifact}`)")

    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "- Run `make blueprint-upgrade-consumer-validate` before committing upgrade results.",
            f"- Summary generated at `{display_repo_path(repo_root, summary_path)}`.",
        ]
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    try:
        plan_path = _resolve_repo_scoped_path(repo_root, args.plan_path, "--plan-path")
        apply_path = _resolve_repo_scoped_path(repo_root, args.apply_path, "--apply-path")
        summary_path = _resolve_repo_scoped_path(repo_root, args.summary_path, "--summary-path")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _ensure_git_repo(repo_root)

    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    if contract.repository.repo_mode != contract.repository.consumer_init.mode_to:
        print(
            "blueprint-upgrade-consumer is only supported for generated-consumer repositories "
            f"(repo_mode={contract.repository.repo_mode})",
            file=sys.stderr,
        )
        return 1

    if _repo_is_dirty(repo_root) and not args.allow_dirty:
        print(
            "refusing upgrade on dirty worktree; commit/stash changes or set BLUEPRINT_UPGRADE_ALLOW_DIRTY=true",
            file=sys.stderr,
        )
        return 1

    temp_dir: Path | None = None
    try:
        temp_dir, source_repo, resolved_commit = _clone_source_repository(args.source, args.ref)
        baseline_ref = _resolve_baseline_ref(source_repo, contract.repository.template_bootstrap.template_version)
        baseline_commit = _resolve_commit(source_repo, baseline_ref) if baseline_ref else None
        if baseline_ref is not None and baseline_commit == resolved_commit:
            print(
                "upgrade baseline collision: "
                f"baseline ref {baseline_ref} and upgrade ref {args.ref} both resolve to target commit {resolved_commit}. "
                "Pick an upgrade ref newer than the baseline tag or bump template_bootstrap.template_version first.",
                file=sys.stderr,
            )
            return 1

        source_contract: BlueprintContract | None = None
        source_contract_path = source_repo / "blueprint/contract.yaml"
        if source_contract_path.is_file():
            try:
                source_contract = load_blueprint_contract(source_contract_path)
            except Exception as exc:  # pragma: no cover - defensive fallback for malformed source snapshots
                print(
                    f"warning: unable to load source contract at {source_contract_path}: {exc}; "
                    "falling back to target repository contract scope",
                    file=sys.stderr,
                )

        required_files, source_only, consumer_seeded, init_managed, conditional = _contract_paths(contract)
        managed_dir_roots = _managed_roots(contract)
        if source_contract is not None:
            (
                source_required_files,
                source_source_only,
                source_consumer_seeded,
                source_init_managed,
                source_conditional,
            ) = _contract_paths(source_contract)
            required_files = _merge_path_sets(required_files, source_required_files)
            source_only = _merge_path_sets(source_only, source_source_only)
            consumer_seeded = _merge_path_sets(consumer_seeded, source_consumer_seeded)
            init_managed = _merge_path_sets(init_managed, source_init_managed)
            conditional = _merge_path_sets(conditional, source_conditional)
            managed_dir_roots = _merge_path_sets(managed_dir_roots, _managed_roots(source_contract))

        source_files, target_files, managed_dir_roots = _collect_candidate_paths(
            repo_root,
            source_repo,
            managed_dir_roots,
            required_files,
            init_managed,
            conditional,
        )
        all_paths = sorted(source_files | target_files)
        protected_roots = _protected_roots(contract, source_contract)

        baseline_cache: dict[str, str | None] = {}
        entries = _classify_entries(
            repo_root=repo_root,
            source_repo=source_repo,
            all_paths=all_paths,
            required_files=required_files,
            source_only=source_only,
            consumer_seeded=consumer_seeded,
            init_managed=init_managed,
            conditional_entries=conditional,
            managed_dir_roots=managed_dir_roots,
            protected_roots=protected_roots,
            baseline_ref=baseline_ref,
            baseline_cache=baseline_cache,
            allow_delete=args.allow_delete,
        )
        entries, runtime_dependency_manual_actions = _annotate_protected_dependency_gaps(
            entries,
            source_repo,
            protected_roots,
        )
        platform_make_target_manual_actions = _collect_missing_platform_make_target_actions(
            repo_root,
            source_repo,
            contract,
            source_contract,
        )
        required_manual_actions = _merge_required_manual_actions(
            runtime_dependency_manual_actions,
            platform_make_target_manual_actions,
        )

        plan_summary = _summarize_plan(entries, required_manual_actions)
        plan_payload = {
            "repo_root": str(repo_root),
            "source": args.source,
            "upgrade_ref": args.ref,
            "resolved_upgrade_commit": resolved_commit,
            "template_version": contract.repository.template_bootstrap.template_version,
            "baseline_ref": baseline_ref,
            "apply_requested": args.apply,
            "allow_dirty": args.allow_dirty,
            "allow_delete": args.allow_delete,
            "entries": [entry.as_dict() for entry in entries],
            "required_manual_actions": [action.as_dict() for action in required_manual_actions],
            "summary": plan_summary,
        }
        _write_json(plan_path, plan_payload)
        print(f"upgrade-plan: {display_repo_path(repo_root, plan_path)}")

        results, applied_count = _apply_entries(
            repo_root=repo_root,
            source_repo=source_repo,
            entries=entries,
            baseline_cache=baseline_cache,
            apply_enabled=args.apply,
        )
        apply_summary = _summarize_apply(results, applied_count, required_manual_actions)
        apply_payload = {
            "repo_root": str(repo_root),
            "source": args.source,
            "upgrade_ref": args.ref,
            "resolved_upgrade_commit": resolved_commit,
            "baseline_ref": baseline_ref,
            "apply_enabled": args.apply,
            "allow_delete": args.allow_delete,
            "results": [result.as_dict() for result in results],
            "required_manual_actions": [action.as_dict() for action in required_manual_actions],
            "summary": apply_summary,
        }

        markers = find_merge_markers(repo_root) if args.apply else []
        if args.apply and markers:
            apply_payload["merge_markers"] = markers
            apply_payload["status"] = "failure"
            _write_json(apply_path, apply_payload)
            _write_summary(
                summary_path=summary_path,
                repo_root=repo_root,
                source=args.source,
                ref=args.ref,
                resolved_commit=resolved_commit,
                baseline_ref=baseline_ref,
                plan_summary=plan_summary,
                apply_summary=apply_summary,
                apply_enabled=args.apply,
                results=results,
                required_manual_actions=required_manual_actions,
            )
            print(
                "merge conflict markers detected after apply; resolve markers before validation",
                file=sys.stderr,
            )
            return 1

        conflict_count = sum(1 for result in results if result.result == "conflict")
        apply_payload["status"] = "failure" if (args.apply and conflict_count > 0) else "success"
        _write_json(apply_path, apply_payload)
        _write_summary(
            summary_path=summary_path,
            repo_root=repo_root,
            source=args.source,
            ref=args.ref,
            resolved_commit=resolved_commit,
            baseline_ref=baseline_ref,
            plan_summary=plan_summary,
            apply_summary=apply_summary,
            apply_enabled=args.apply,
            results=results,
            required_manual_actions=required_manual_actions,
        )
        print(f"upgrade-apply: {display_repo_path(repo_root, apply_path)}")
        print(f"upgrade-summary: {display_repo_path(repo_root, summary_path)}")
        if required_manual_actions:
            manual_actions_summary = ", ".join(
                f"{action.dependency_of} -> {action.dependency_path}" for action in required_manual_actions
            )
            print(
                "upgrade requires manual actions for protected/consumer-owned dependency gaps: "
                + manual_actions_summary,
                file=sys.stderr,
            )

        if args.apply and conflict_count > 0:
            print(
                f"upgrade apply produced {conflict_count} conflict(s); inspect artifacts/blueprint/conflicts",
                file=sys.stderr,
            )
            return 1
        return 0
    finally:
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
