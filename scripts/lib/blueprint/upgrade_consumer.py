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
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import display_repo_path, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import BlueprintContract, load_blueprint_contract  # noqa: E402
from scripts.lib.blueprint.init_repo_contract import expand_optional_module_path  # noqa: E402
from scripts.lib.blueprint.merge_markers import find_merge_markers  # noqa: E402
from scripts.lib.blueprint.runtime_dependency_edges import RUNTIME_DEPENDENCY_EDGES  # noqa: E402
from scripts.lib.blueprint.upgrade_reconcile_report import (  # noqa: E402
    RECONCILE_REPORT_DEFAULT_PATH,
    build_upgrade_reconcile_report,
)
from scripts.lib.blueprint.upgrade_semantic_annotator import (  # noqa: E402
    KIND_STRUCTURAL_CHANGE,
    SemanticAnnotation,
    annotate as _annotate,
)


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
LOCAL_POST_DEPLOY_HOOK_ENABLE_FLAG = "LOCAL_POST_DEPLOY_HOOK_ENABLED"
LOCAL_POST_DEPLOY_HOOK_COMMAND_ENV = "LOCAL_POST_DEPLOY_HOOK_CMD"
LOCAL_POST_DEPLOY_HOOK_CONSUMER_TARGET = "infra-post-deploy-consumer"
LOCAL_POST_DEPLOY_HOOK_CONSUMER_PLACEHOLDER_TOKEN = "infra-post-deploy-consumer placeholder active"
LOCAL_POST_DEPLOY_HOOK_REFERENCE_PATH = "scripts/bin/infra/provision_deploy.sh"


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
    semantic: SemanticAnnotation | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
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
        if self.semantic is not None:
            payload["semantic"] = self.semantic.as_dict()
        return payload


@dataclass(frozen=True)
class ApplyResult:
    path: str
    planned_action: str
    planned_operation: str
    result: str
    reason: str
    conflict_artifact: str | None = None
    semantic: SemanticAnnotation | None = None

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
        if self.semantic is not None:
            payload["semantic"] = self.semantic.as_dict()
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
    parser.add_argument(
        "--reconcile-report-path",
        default=RECONCILE_REPORT_DEFAULT_PATH,
        help="Ownership-aware reconcile report path (absolute or repo-relative).",
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


_CONSUMER_WORKLOAD_APPS_PREFIX = "infra/gitops/platform/base/apps/"


def _is_consumer_owned_workload(relative_path: str) -> bool:
    """Return True for non-kustomization YAML files under infra/gitops/platform/base/apps/.

    These files are consumer-defined workload manifests. Blueprint manages the directory
    structure and kustomization.yaml but does not own individual manifests.
    Bridge guard until issue #206 delivers a general contract schema mechanism.
    """
    if not relative_path.startswith(_CONSUMER_WORKLOAD_APPS_PREFIX):
        return False
    filename = relative_path[len(_CONSUMER_WORKLOAD_APPS_PREFIX):]
    return filename != "kustomization.yaml" and filename.endswith(".yaml") and "/" not in filename


def _is_kustomization_referenced(repo_root: Path, relative_path: str) -> bool:
    """Return True if any kustomization.yaml in the same directory references relative_path's basename.

    Checks resources: (direct strings) and patches: (strings or {path: …} dicts).
    Uses yaml.safe_load only (NFR-SEC-001). On parse failure, logs a warning to stderr
    and returns False without raising (NFR-REL-001).
    """
    candidate_dir = (repo_root / relative_path).parent
    basename = Path(relative_path).name
    kust_file = candidate_dir / "kustomization.yaml"
    if not kust_file.is_file():
        return False
    try:
        data = yaml.safe_load(kust_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(
            f"warning: _is_kustomization_referenced: failed to parse {kust_file}: {exc}",
            file=sys.stderr,
        )
        return False
    if not isinstance(data, dict):
        return False
    for item in data.get("resources", []) or []:
        if isinstance(item, str) and item == basename:
            return True
    for item in data.get("patches", []) or []:
        if isinstance(item, str) and item == basename:
            return True
        if isinstance(item, dict):
            patch_path = item.get("path", "")
            if isinstance(patch_path, str) and patch_path == basename:
                return True
    return False


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


# ---------------------------------------------------------------------------
# Source tree completeness audit (FR-009 / FR-010 / FR-011 — Issue #185)
# ---------------------------------------------------------------------------

_AUDIT_SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", "__pycache__", ".venv",
})


def _source_repo_tracked_files(source_repo: Path) -> list[str] | None:
    """Return git-tracked file paths relative to source_repo, or None if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(source_repo),
            capture_output=True,
            text=True,
            check=True,
        )
        return [line for line in result.stdout.splitlines() if line]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def audit_source_tree_coverage(
    source_repo: Path,
    required_files: set[str],
    source_only: set[str],
    init_managed: set[str],
    conditional: set[str],
    managed_roots: set[str],
    feature_gated: frozenset[str] = frozenset(),
) -> list[str]:
    """Return sorted list of source files not covered by any contract category.

    Emits a WARNING to stderr for each uncovered path.  (FR-009 / FR-010)

    All coverage categories support both exact-file and directory-prefix matching
    so that directory-scoped entries (e.g. ``infra/cloud/stackit/terraform/modules/dns``)
    cover all files nested under them.

    When source_repo is a git repository, only git-tracked files are audited
    (untracked build artifacts and local state are excluded automatically).
    Falls back to filesystem rglob when source_repo is not a git repo (e.g. in tests).
    """
    all_coverage_roots = (
        required_files
        | source_only
        | init_managed
        | conditional
        | managed_roots
        | feature_gated
    )

    # Prefer git-tracked files to exclude untracked/generated artifacts.
    tracked = _source_repo_tracked_files(source_repo)
    if tracked is not None:
        candidate_rels: list[str] = sorted(tracked)
    else:
        # Non-git source repo (e.g. tempdir in tests) — rglob fallback.
        candidate_rels = []
        for path in sorted(source_repo.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(source_repo).as_posix()
            if any(part in _AUDIT_SKIP_DIRS for part in path.relative_to(source_repo).parts):
                continue
            candidate_rels.append(rel)

    uncovered: list[str] = []
    for rel in candidate_rels:
        # A file is covered when any contract entry equals or is a path-prefix of rel.
        if any(rel == entry or _path_is_within(rel, entry) for entry in all_coverage_roots):
            continue
        print(f"WARNING: uncovered blueprint source file not in contract: {rel}", file=sys.stderr)
        uncovered.append(rel)
    return uncovered


def validate_plan_uncovered_source_files(plan_payload: dict[str, Any]) -> list[str]:
    """Belt-and-suspenders: return error strings when uncovered_source_files_count > 0.

    Called by the plan step before writing the plan artifact to enforce FR-011.
    """
    raw = plan_payload.get("uncovered_source_files_count", 0)
    count = raw if isinstance(raw, int) else 0
    if count > 0:
        return [
            f"uncovered_source_files_count={count}: {count} blueprint source file(s) "
            "are not reachable via required_files, init_managed, conditional_scaffold_paths, "
            "feature_gated, blueprint_managed_roots, or source_only; add them to blueprint/contract.yaml"
        ]
    return []


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


def _try_annotate(baseline_content: str, source_content: str, path: str) -> SemanticAnnotation:
    """Call the semantic annotator with a per-entry try/except fallback.

    On any exception, returns a structural-change annotation and logs a warning
    so plan generation always completes regardless of annotator errors.
    """
    try:
        return _annotate(baseline_content, source_content)
    except Exception as exc:  # noqa: BLE001
        print(
            f"semantic annotator: exception for {path!r}; structural-change fallback: {exc}",
            file=sys.stderr,
        )
        return SemanticAnnotation(
            kind=KIND_STRUCTURAL_CHANGE,
            description="Annotation generation failed; structural-change fallback applied.",
            verification_hints=(
                "Manually review the diff between the baseline ref and the upgrade source.",
            ),
        )


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

    def resolve_baseline_exists(path: str) -> bool:
        """Cheap existence check at baseline ref without fetching file content.

        Uses git cat-file -e (no content transfer) for paths not already cached.
        Re-uses cached content result when resolve_baseline_content was called first.
        """
        if baseline_ref is None:
            return False
        if path in baseline_cache:
            return baseline_cache[path] is not None
        result = _run_git(source_repo, "cat-file", "-e", f"{baseline_ref}:{path}")
        return result.returncode == 0

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

        if not source_exists and _is_consumer_owned_workload(relative_path):
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership="consumer-owned-workload",
                    action=ACTION_SKIP,
                    operation=OPERATION_NONE,
                    reason="path is a consumer workload manifest in base/apps/; excluded from blueprint prune",
                    source_exists=source_exists,
                    target_exists=target_exists,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                )
            )
            continue

        if not source_exists and target_exists and _is_kustomization_referenced(repo_root, relative_path):
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership="consumer-kustomization-ref",
                    action=ACTION_SKIP,
                    operation=OPERATION_NONE,
                    reason="path is referenced in a consumer kustomization.yaml; excluded from blueprint prune",
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

        if baseline_ref is None:
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
            else:
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

        if source_content == target_content:
            # Fast path: content already matches. Use cheap existence check (git cat-file -e,
            # no content transfer) to distinguish additive vs non-additive for accurate
            # reason/baseline_content_available fields without fetching full baseline content.
            baseline_exists = resolve_baseline_exists(relative_path)
            if not baseline_exists:
                entries.append(
                    UpgradeEntry(
                        path=relative_path,
                        ownership=ownership,
                        action=ACTION_SKIP,
                        operation=OPERATION_NONE,
                        reason="additive file already at source version; safe to take",
                        source_exists=True,
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
                        operation=OPERATION_NONE,
                        reason="path already matches upgrade source content",
                        source_exists=True,
                        target_exists=True,
                        baseline_ref=baseline_ref,
                        baseline_content_available=True,
                    )
                )
            continue

        baseline_content = resolve_baseline_content(relative_path)

        if baseline_content is None:
            # Additive file: absent at the baseline ref, so no 3-way merge ancestor exists.
            # Source and target content differ (same-content case handled above).
            entries.append(
                UpgradeEntry(
                    path=relative_path,
                    ownership=ownership,
                    action=ACTION_MERGE_REQUIRED,
                    operation=OPERATION_MERGE,
                    reason=(
                        f"additive file: not present at baseline ref {baseline_ref}; "
                        "target diverges from source; manual merge advisory"
                    ),
                    source_exists=True,
                    target_exists=True,
                    baseline_ref=baseline_ref,
                    baseline_content_available=False,
                    semantic=_try_annotate("", source_content, relative_path),
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
                semantic=_try_annotate(baseline_content, source_content, relative_path),
            )
        )

    _mr = [e for e in entries if e.action == ACTION_MERGE_REQUIRED]
    _auto = sum(1 for e in _mr if e.semantic and e.semantic.kind != KIND_STRUCTURAL_CHANGE)
    print(f"semantic annotator: merge-required={len(_mr)} auto={_auto} fallback={len(_mr) - _auto}")
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
            # Keep discovery aligned with root Makefile include contract:
            # -include $(wildcard $(PLATFORM_MAKEFILES_DIR)/*.mk)
            for include_file in sorted(include_root.glob("*.mk")):
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


def _strip_wrapping_quotes(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1]
    return stripped


def _read_repo_init_defaults(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    defaults: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="surrogateescape").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        defaults[key] = _strip_wrapping_quotes(value)
    return defaults


def _value_is_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _local_post_deploy_consumer_target_required(repo_root: Path) -> bool:
    defaults = _read_repo_init_defaults(repo_root / "blueprint/repo.init.env")
    if not _value_is_true(defaults.get(LOCAL_POST_DEPLOY_HOOK_ENABLE_FLAG, "false")):
        return False
    hook_cmd = defaults.get(LOCAL_POST_DEPLOY_HOOK_COMMAND_ENV, "")
    if not hook_cmd:
        return False
    return LOCAL_POST_DEPLOY_HOOK_CONSUMER_TARGET in hook_cmd


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


def _platform_make_location_hint(contract: BlueprintContract) -> str:
    ownership = contract.make_contract.ownership
    platform_makefile = ownership.platform_editable_file.strip()
    include_dir = ownership.platform_editable_include_dir.strip()
    if platform_makefile and include_dir:
        return f"`{platform_makefile}` or linked includes under `{include_dir}/*.mk`"
    if platform_makefile:
        return f"`{platform_makefile}`"
    if include_dir:
        return f"linked includes under `{include_dir}/*.mk`"
    return "platform-owned make surfaces"


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
    location_hint = _platform_make_location_hint(contract)

    actions: list[RequiredManualAction] = []
    for target_name in sorted(source_target_definitions.keys()):
        if target_name not in required_targets:
            continue
        if target_name in target_targets:
            continue
        reference_path = _source_make_target_reference(source_repo, target_name)
        dependency_of = (
            f"{reference_path}: make {target_name}"
            if reference_path is not None
            else f"blueprint/contract.yaml: spec.make_contract.required_targets -> {target_name}"
        )
        reference_reason = (
            f"; `{reference_path}` invokes it and validation will fail until the target is added"
            if reference_path is not None
            else "; contract validation enforces this target for generated-consumer repositories"
        )
        actions.append(
            RequiredManualAction(
                dependency_path=platform_makefile,
                dependency_of=dependency_of,
                reason=(
                    f"required make target `{target_name}` is missing from consumer-owned platform make surfaces; "
                    f"define `{target_name}` in {location_hint} before running upgrade validation"
                    f"{reference_reason}"
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
                        f"until the target is implemented; define it in {location_hint}"
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
                        "placeholder; replace it with deterministic repository-specific dependency bootstrap commands "
                        f"in {location_hint}"
                    ),
                    required_follow_up_commands=("make blueprint-upgrade-consumer-validate",),
                )
            )

    if (
        _local_post_deploy_consumer_target_required(repo_root)
        and LOCAL_POST_DEPLOY_HOOK_CONSUMER_TARGET in required_targets
    ):
        hook_dependency_of = (
            f"{LOCAL_POST_DEPLOY_HOOK_REFERENCE_PATH}: "
            f"{LOCAL_POST_DEPLOY_HOOK_COMMAND_ENV} -> make {LOCAL_POST_DEPLOY_HOOK_CONSUMER_TARGET}"
        )
        post_deploy_target_path = target_target_definitions.get(LOCAL_POST_DEPLOY_HOOK_CONSUMER_TARGET)
        if post_deploy_target_path is None:
            actions.append(
                RequiredManualAction(
                    dependency_path=platform_makefile,
                    dependency_of=hook_dependency_of,
                    reason=(
                        f"required consumer-owned make target `{LOCAL_POST_DEPLOY_HOOK_CONSUMER_TARGET}` is missing "
                        f"while {LOCAL_POST_DEPLOY_HOOK_ENABLE_FLAG}=true; "
                        f"{LOCAL_POST_DEPLOY_HOOK_COMMAND_ENV} invokes it by default; define it in {location_hint}"
                    ),
                    required_follow_up_commands=("make blueprint-upgrade-consumer-validate",),
                )
            )
        elif _file_contains_literal(
            repo_root / post_deploy_target_path,
            LOCAL_POST_DEPLOY_HOOK_CONSUMER_PLACEHOLDER_TOKEN,
        ):
            actions.append(
                RequiredManualAction(
                    dependency_path=post_deploy_target_path,
                    dependency_of=hook_dependency_of,
                    reason=(
                        f"required consumer-owned make target `{LOCAL_POST_DEPLOY_HOOK_CONSUMER_TARGET}` is still "
                        f"placeholder while {LOCAL_POST_DEPLOY_HOOK_ENABLE_FLAG}=true; replace it with deterministic "
                        f"repository-specific post-deploy reconciliation commands in {location_hint}"
                    ),
                    required_follow_up_commands=("make blueprint-upgrade-consumer-validate",),
                )
            )
    return actions


# Static mapping of optional module id → make targets rendered by render_makefile.sh when the module is enabled.
# Keep in sync with scripts/bin/blueprint/render_makefile.sh:makefile_module_phony_suffix.
_MODULE_MAKE_TARGETS: dict[str, frozenset[str]] = {
    "observability": frozenset({
        "infra-observability-plan",
        "infra-observability-apply",
        "infra-observability-deploy",
        "infra-observability-smoke",
        "infra-observability-destroy",
    }),
    "workflows": frozenset({
        "infra-stackit-workflows-plan",
        "infra-stackit-workflows-apply",
        "infra-stackit-workflows-reconcile",
        "infra-stackit-workflows-dag-deploy",
        "infra-stackit-workflows-dag-parse-smoke",
        "infra-stackit-workflows-smoke",
        "infra-stackit-workflows-destroy",
    }),
    "langfuse": frozenset({
        "infra-langfuse-plan",
        "infra-langfuse-apply",
        "infra-langfuse-deploy",
        "infra-langfuse-smoke",
        "infra-langfuse-destroy",
    }),
    "postgres": frozenset({
        "infra-postgres-plan",
        "infra-postgres-apply",
        "infra-postgres-smoke",
        "infra-postgres-destroy",
    }),
    "neo4j": frozenset({
        "infra-neo4j-plan",
        "infra-neo4j-apply",
        "infra-neo4j-deploy",
        "infra-neo4j-smoke",
        "infra-neo4j-destroy",
    }),
    "object-storage": frozenset({
        "infra-object-storage-plan",
        "infra-object-storage-apply",
        "infra-object-storage-smoke",
        "infra-object-storage-destroy",
    }),
    "rabbitmq": frozenset({
        "infra-rabbitmq-plan",
        "infra-rabbitmq-apply",
        "infra-rabbitmq-smoke",
        "infra-rabbitmq-destroy",
    }),
    "opensearch": frozenset({
        "infra-opensearch-plan",
        "infra-opensearch-apply",
        "infra-opensearch-smoke",
        "infra-opensearch-destroy",
    }),
    "dns": frozenset({
        "infra-dns-plan",
        "infra-dns-apply",
        "infra-dns-smoke",
        "infra-dns-destroy",
    }),
    "public-endpoints": frozenset({
        "infra-public-endpoints-plan",
        "infra-public-endpoints-apply",
        "infra-public-endpoints-deploy",
        "infra-public-endpoints-smoke",
        "infra-public-endpoints-destroy",
    }),
    "secrets-manager": frozenset({
        "infra-secrets-manager-plan",
        "infra-secrets-manager-apply",
        "infra-secrets-manager-smoke",
        "infra-secrets-manager-destroy",
    }),
    "kms": frozenset({
        "infra-kms-plan",
        "infra-kms-apply",
        "infra-kms-smoke",
        "infra-kms-destroy",
    }),
    "identity-aware-proxy": frozenset({
        "infra-identity-aware-proxy-plan",
        "infra-identity-aware-proxy-apply",
        "infra-identity-aware-proxy-deploy",
        "infra-identity-aware-proxy-smoke",
        "infra-identity-aware-proxy-destroy",
    }),
}


def _collect_stale_module_target_actions(
    repo_root: Path,
    contract: BlueprintContract,
) -> list[RequiredManualAction]:
    """Detect stale references to infra-<module>-* targets absent from make/blueprint.generated.mk.

    When an optional module is disabled, render_makefile.sh omits its targets from the generated
    makefile. Consumer CI workflows or make files that still invoke those targets will fail silently.
    This helper surfaces each stale reference as a RequiredManualAction in the upgrade plan.
    """
    generated_mk_path = repo_root / "make/blueprint.generated.mk"
    if not generated_mk_path.is_file():
        return []

    # Collect all target names present in the generated makefile.
    active_targets = set(_make_target_definitions([("make/blueprint.generated.mk", generated_mk_path)]).keys())

    # Find all module targets that are absent (module disabled).
    absent_targets: set[str] = set()
    for targets in _MODULE_MAKE_TARGETS.values():
        for target in targets:
            if target not in active_targets:
                absent_targets.add(target)

    if not absent_targets:
        return []

    # Build the set of consumer-owned files to scan for stale references.
    scan_paths: list[tuple[str, Path]] = []
    for rel_path in BLUEPRINT_MAKE_TARGET_REFERENCE_PATHS:
        abs_path = repo_root / rel_path
        if abs_path.is_file():
            scan_paths.append((rel_path, abs_path))
    for rel_path, abs_path in _collect_platform_make_paths(repo_root, contract):
        scan_paths.append((rel_path, abs_path))

    # Deduplicate scan paths (a file can appear in both lists).
    seen_scan: set[str] = set()
    deduped_scan: list[tuple[str, Path]] = []
    for rel_path, abs_path in scan_paths:
        key = abs_path.as_posix()
        if key in seen_scan:
            continue
        seen_scan.add(key)
        deduped_scan.append((rel_path, abs_path))

    actions: list[RequiredManualAction] = []
    for rel_path, abs_path in sorted(deduped_scan, key=lambda t: t[0]):
        try:
            content = _read_text(abs_path)
        except (OSError, UnicodeDecodeError) as exc:
            actions.append(
                RequiredManualAction(
                    dependency_path=rel_path,
                    dependency_of=f"{rel_path}: scan for stale disabled-module make target references",
                    reason=(
                        f"could not scan `{rel_path}` for stale disabled-module make target references: {exc}; "
                        "review file readability and rerun upgrade validation because stale references may still exist"
                    ),
                    required_follow_up_commands=("make blueprint-upgrade-consumer-validate",),
                )
            )
            continue
        for target in sorted(absent_targets):
            if not _file_content_references_make_target(content, target):
                continue
            actions.append(
                RequiredManualAction(
                    dependency_path=rel_path,
                    dependency_of=f"{rel_path}: make {target}",
                    reason=(
                        f"stale reference to `{target}` in `{rel_path}`; "
                        "this target is absent from make/blueprint.generated.mk because the module is disabled; "
                        "remove or guard the reference while the module is disabled (or before running validation/CI)"
                    ),
                    required_follow_up_commands=("make blueprint-render-makefile", "make blueprint-upgrade-consumer-validate"),
                )
            )
    return actions


def _file_content_references_make_target(content: str, target: str) -> bool:
    """Return True if content contains a make invocation of target as a standalone command.

    Uses a negative lookbehind for word characters to avoid matching substrings
    (e.g. ``cmake <target>``). Scans line-by-line and skips comment-only lines.
    """
    import re as _re
    # Negative lookbehind ensures `make` is not preceded by a word character (e.g. avoids `cmake`).
    pattern = _re.compile(
        r"(?<!\w)(?:make|\$\(MAKE\))\s+" + _re.escape(target) + r"(?=\s|$|[^\w-])",
    )
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if pattern.search(line):
            return True
    return False


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


_TF_BLOCK_RE = re.compile(r'^(\w+)\s+"([^"]+)"(?:\s+"([^"]+)")?\s*\{', re.MULTILINE)


def _tf_find_block_end(content: str, open_pos: int) -> int:
    """Return the index after the closing } matching the { at open_pos."""
    depth = 0
    i = open_pos
    while i < len(content):
        c = content[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(content)


def _tf_deduplicate_blocks(content: str) -> tuple[str | None, list[str], list[str]]:
    """Scan merged Terraform content for duplicate top-level named block declarations.

    Returns (processed_content, dedup_log, conflict_keys):
    - processed_content: deduplicated content (None when non-identical conflicts exist)
    - dedup_log: block keys removed as byte-identical duplicates (e.g. "variable.opensearch_enabled")
    - conflict_keys: block keys with non-identical duplicate declarations

    The common path (no duplicates) returns content unchanged with empty lists (REQ-004).
    """
    # Collect all occurrences of each named block: key → list of (start, end) spans
    occurrences: dict[str, list[tuple[int, int]]] = {}
    for match in _TF_BLOCK_RE.finditer(content):
        block_type = match.group(1)
        label1 = match.group(2)
        label2 = match.group(3)
        key = f"{block_type}.{label1}.{label2}" if label2 else f"{block_type}.{label1}"
        brace_pos = content.index("{", match.start())
        block_end = _tf_find_block_end(content, brace_pos)
        occurrences.setdefault(key, []).append((match.start(), block_end))

    dedup_log: list[str] = []
    conflict_keys: list[str] = []
    for key, spans in occurrences.items():
        if len(spans) <= 1:
            continue
        texts = [content[s:e] for s, e in spans]
        if all(t == texts[0] for t in texts):
            dedup_log.append(key)
        else:
            conflict_keys.append(key)

    if conflict_keys:
        return None, [], conflict_keys

    if not dedup_log:
        return content, [], []

    # Remove all but the first occurrence of each duplicated key, back-to-front
    spans_to_remove: list[tuple[int, int]] = []
    for key in dedup_log:
        for start, end in occurrences[key][1:]:
            # Consume any preceding blank line so we don't leave stray whitespace
            while start > 0 and content[start - 1] == "\n":
                start -= 1
            spans_to_remove.append((start, end))
    spans_to_remove.sort(key=lambda x: x[0], reverse=True)

    result = content
    for start, end in spans_to_remove:
        result = result[:start] + result[end:]

    return result, dedup_log, []


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
        # `git merge-file` returns:
        # - 0 for a clean merge
        # - positive values when conflicts exist (often conflict count)
        # - negative values only when process execution itself failed
        if merge.returncode < 0:
            raise RuntimeError(f"git merge-file failed: {merge.stderr.strip()}")
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
) -> tuple[list[ApplyResult], int, list[dict[str, str]]]:
    results: list[ApplyResult] = []
    applied_count = 0
    deduplication_log: list[dict[str, str]] = []

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
                        semantic=entry.semantic,
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
                        semantic=entry.semantic,
                    )
                )
                continue

            if entry.path.endswith(".tf"):
                tf_content, dedup_log, conflict_keys = _tf_deduplicate_blocks(merged_content)
                if conflict_keys:
                    conflict_artifact = _write_conflict_artifact(
                        repo_root,
                        entry.path,
                        f"duplicate non-identical Terraform blocks after merge: {', '.join(conflict_keys)}",
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
                            reason=f"non-identical duplicate Terraform blocks: {', '.join(conflict_keys)}",
                            conflict_artifact=conflict_artifact,
                            semantic=entry.semantic,
                        )
                    )
                    continue
                if dedup_log:
                    _write_text(target_path, tf_content)
                    applied_count += 1
                    for block_key in dedup_log:
                        deduplication_log.append({"path": entry.path, "block": block_key})
                    results.append(
                        ApplyResult(
                            path=entry.path,
                            planned_action=entry.action,
                            planned_operation=entry.operation,
                            result="merged-deduped",
                            reason=f"3-way merge applied; removed byte-identical duplicate blocks: {', '.join(dedup_log)}",
                            semantic=entry.semantic,
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
                    semantic=entry.semantic,
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

    return results, applied_count, deduplication_log


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
    entries: list[UpgradeEntry] | None = None,
) -> dict[str, int]:
    counts: dict[str, int] = {"total": len(results), "applied_count": applied_count}
    for result in results:
        counts[result.result] = counts.get(result.result, 0) + 1
    counts["required_manual_action_count"] = len(required_manual_actions)
    counts["tf_dedup_count"] = counts.get("merged-deduped", 0)
    counts["consumer_kustomization_ref_count"] = (
        sum(1 for e in entries if e.ownership == "consumer-kustomization-ref") if entries else 0
    )
    return counts


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")


def _command_plan(*, source: str, ref: str) -> dict[str, str]:
    return {
        "preflight": f"BLUEPRINT_UPGRADE_SOURCE={source} BLUEPRINT_UPGRADE_REF={ref} make blueprint-upgrade-consumer-preflight",
        "plan": f"BLUEPRINT_UPGRADE_SOURCE={source} BLUEPRINT_UPGRADE_REF={ref} make blueprint-upgrade-consumer",
        "apply": (
            f"BLUEPRINT_UPGRADE_SOURCE={source} BLUEPRINT_UPGRADE_REF={ref} "
            "BLUEPRINT_UPGRADE_APPLY=true make blueprint-upgrade-consumer"
        ),
        "validate": "make blueprint-upgrade-consumer-validate",
        "postcheck": "make blueprint-upgrade-consumer-postcheck",
    }


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
    entries: list[UpgradeEntry] | None = None,
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
    ]

    merge_required_entries = [e for e in (entries or []) if e.action == ACTION_MERGE_REQUIRED and e.semantic]
    if merge_required_entries:
        lines.extend(["", "## Merge-Required Annotations", ""])
        for entry in merge_required_entries:
            ann = entry.semantic
            assert ann is not None
            lines.append(f"**`{entry.path}`** — kind: `{ann.kind}`")
            lines.append(f"> {ann.description}")
            for hint in ann.verification_hints:
                lines.append(f"- {hint}")
            lines.append("")

    lines.extend([
        "",
        "## Apply Summary",
        "",
        "| Result | Count |",
        "| --- | ---: |",
    ])

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
        reconcile_report_path = _resolve_repo_scoped_path(
            repo_root,
            args.reconcile_report_path,
            "--reconcile-report-path",
        )
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
        feature_gated = frozenset(contract.repository.feature_gated_paths)
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
            feature_gated = feature_gated | frozenset(source_contract.repository.feature_gated_paths)

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
        stale_module_target_actions = _collect_stale_module_target_actions(
            repo_root,
            contract,
        )
        required_manual_actions = _merge_required_manual_actions(
            runtime_dependency_manual_actions,
            platform_make_target_manual_actions,
            stale_module_target_actions,
        )

        # Source tree completeness audit — must run before plan is written (FR-011 Option A)
        # Include consumer_seeded files and all platform-owned roots in the coverage check.
        # Platform-editable roots (scripts/bin/platform/, scripts/lib/platform/, make/platform/,
        # docs/platform/) exist in the source repo but are not in blueprint_managed_roots.
        def _platform_owned_roots(c: BlueprintContract) -> set[str]:
            ownership = c.make_contract.ownership
            roots: set[str] = set(c.script_contract.platform_editable_roots)
            roots.add(ownership.platform_editable_file)
            roots.add(ownership.platform_editable_include_dir)
            roots.add(c.docs_contract.platform_docs.root)
            return {r.rstrip("/") for r in roots}

        _plat_owned: set[str] = _platform_owned_roots(contract)
        if source_contract is not None:
            _plat_owned |= _platform_owned_roots(source_contract)
        uncovered_source_files = audit_source_tree_coverage(
            source_repo,
            required_files | consumer_seeded,
            source_only,
            init_managed,
            conditional,
            managed_dir_roots | _plat_owned,
            feature_gated=feature_gated,
        )
        uncovered_source_files_count = len(uncovered_source_files)

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
            "uncovered_source_files_count": uncovered_source_files_count,
        }

        plan_errors = validate_plan_uncovered_source_files(plan_payload)
        if plan_errors:
            for err in plan_errors:
                print(f"upgrade-plan: ERROR: {err}", file=sys.stderr)
            print(
                f"upgrade-plan: BLOCKED — resolve {uncovered_source_files_count} uncovered "
                "source file(s) before producing a plan",
                file=sys.stderr,
            )
            return 1

        _write_json(plan_path, plan_payload)
        print(f"upgrade-plan: {display_repo_path(repo_root, plan_path)}")

        results, applied_count, deduplication_log = _apply_entries(
            repo_root=repo_root,
            source_repo=source_repo,
            entries=entries,
            baseline_cache=baseline_cache,
            apply_enabled=args.apply,
        )
        apply_summary = _summarize_apply(results, applied_count, required_manual_actions, entries=entries)
        apply_payload: dict[str, Any] = {
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
        if deduplication_log:
            apply_payload["deduplication_log"] = deduplication_log

        markers = find_merge_markers(repo_root) if args.apply else []
        if args.apply and markers:
            apply_payload["merge_markers"] = markers
            apply_payload["status"] = "failure"
            _write_json(apply_path, apply_payload)
            reconcile_payload = build_upgrade_reconcile_report(
                repo_root=repo_root,
                plan_payload=plan_payload,
                apply_payload=apply_payload,
                repo_mode=contract.repository.repo_mode,
                source=args.source,
                upgrade_ref=args.ref,
                resolved_upgrade_commit=resolved_commit,
                baseline_ref=baseline_ref,
                command_plan=_command_plan(source=args.source, ref=args.ref),
            )
            _write_json(reconcile_report_path, reconcile_payload)
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
                entries=entries,
            )
            print(f"upgrade-reconcile-report: {display_repo_path(repo_root, reconcile_report_path)}")
            print(
                "merge conflict markers detected after apply; resolve markers before validation",
                file=sys.stderr,
            )
            return 1

        conflict_count = sum(1 for result in results if result.result == "conflict")
        apply_payload["status"] = "failure" if (args.apply and conflict_count > 0) else "success"
        _write_json(apply_path, apply_payload)
        reconcile_payload = build_upgrade_reconcile_report(
            repo_root=repo_root,
            plan_payload=plan_payload,
            apply_payload=apply_payload,
            repo_mode=contract.repository.repo_mode,
            source=args.source,
            upgrade_ref=args.ref,
            resolved_upgrade_commit=resolved_commit,
            baseline_ref=baseline_ref,
            command_plan=_command_plan(source=args.source, ref=args.ref),
        )
        _write_json(reconcile_report_path, reconcile_payload)
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
            entries=entries,
        )
        print(f"upgrade-apply: {display_repo_path(repo_root, apply_path)}")
        print(f"upgrade-summary: {display_repo_path(repo_root, summary_path)}")
        print(f"upgrade-reconcile-report: {display_repo_path(repo_root, reconcile_report_path)}")
        if required_manual_actions:
            manual_actions_summary = ", ".join(
                f"{action.dependency_of} -> {action.dependency_path}" for action in required_manual_actions
            )
            print(
                "upgrade requires manual actions for protected/consumer-owned dependency gaps: "
                + manual_actions_summary,
                file=sys.stderr,
            )
        if reconcile_payload.get("summary", {}).get("blocked", False):
            blocking_buckets = [
                bucket
                for bucket, policy in reconcile_payload.get("bucket_policy", {}).items()
                if isinstance(policy, dict)
                and bool(policy.get("blocking"))
                and len(reconcile_payload.get("buckets", {}).get(bucket, [])) > 0
            ]
            print(
                "upgrade reconcile report indicates blocking buckets: " + ", ".join(sorted(blocking_buckets)),
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
