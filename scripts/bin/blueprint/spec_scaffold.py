#!/usr/bin/env python3
"""Scaffold a Spec-Driven Development work-item directory from canonical templates."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402


def _as_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    raise ValueError(f"{field} must be a mapping")


def _as_optional_mapping(value: Any, *, field: str) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    raise ValueError(f"{field} must be a mapping")


def _as_list_of_str(value: Any, *, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{idx}] must be a non-empty string")
        result.append(item.strip())
    return result


def _sanitize_slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized:
        raise ValueError("slug must contain at least one alphanumeric character")
    return normalized


def _resolve_template_root(artifacts: dict[str, Any], track: str) -> Path:
    if track == "blueprint":
        template_root = str(artifacts.get("blueprint_template_root", "")).strip()
        if not template_root:
            raise ValueError("spec.spec_driven_development_contract.artifacts.blueprint_template_root must be set")
        return Path(template_root)
    if track == "consumer":
        template_root = str(artifacts.get("consumer_template_root", "")).strip()
        if not template_root:
            raise ValueError("spec.spec_driven_development_contract.artifacts.consumer_template_root must be set")
        return Path(template_root)
    raise ValueError(f"unsupported track: {track}")


def _copy_document(source: Path, target: Path) -> None:
    content = source.read_text(encoding="utf-8", errors="surrogateescape")
    target.write_text(content, encoding="utf-8")


def _run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise ValueError(f"git {' '.join(args)} failed: {stderr}")
    return result


def _current_branch(repo_root: Path) -> str:
    result = _run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = result.stdout.strip()
    if not branch or branch == "HEAD":
        raise ValueError(
            "unable to resolve current git branch; create an initial commit or rerun with --no-create-branch"
        )
    return branch


def _branch_exists(repo_root: Path, branch: str) -> bool:
    result = _run_git(
        repo_root,
        "show-ref",
        "--verify",
        "--quiet",
        f"refs/heads/{branch}",
        check=False,
    )
    return result.returncode == 0


def _resolve_branch_prefix(*, allowed_prefixes: list[str], preferred_prefix: str) -> str:
    if preferred_prefix and preferred_prefix in allowed_prefixes:
        return preferred_prefix
    if "codex/" in allowed_prefixes:
        return "codex/"
    if allowed_prefixes:
        return allowed_prefixes[0]
    raise ValueError("repository.branch_naming.purpose_prefixes must define at least one prefix")


def _ensure_unique_branch(repo_root: Path, desired: str) -> str:
    if not _branch_exists(repo_root, desired):
        return desired
    index = 2
    while True:
        candidate = f"{desired}-{index}"
        if not _branch_exists(repo_root, candidate):
            return candidate
        index += 1


def _matches_allowed_prefix(*, branch_name: str, allowed_prefixes: list[str]) -> bool:
    return any(branch_name.startswith(prefix) for prefix in allowed_prefixes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--slug", required=True, help="Work-item slug, e.g. runtime-identity-doctor")
    parser.add_argument("--track", choices=("blueprint", "consumer"), default="blueprint")
    parser.add_argument("--date", dest="work_date", default=date.today().isoformat())
    parser.add_argument("--force", action="store_true", help="Overwrite an existing scaffold directory")
    parser.add_argument(
        "--branch",
        help="Explicit branch name to create/check out for this work item (must match allowed branch prefixes)",
    )
    parser.add_argument(
        "--no-create-branch",
        action="store_true",
        help="Explicit opt-out: scaffold the work item without creating a dedicated branch",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, __file__)
    slug = _sanitize_slug(args.slug)

    try:
        work_date = date.fromisoformat(args.work_date)
    except ValueError as exc:
        raise ValueError("--date must be in YYYY-MM-DD format") from exc

    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    contract_raw = contract.raw
    spec_raw = _as_mapping(contract_raw.get("spec"), field="spec")
    repository_raw = _as_mapping(spec_raw.get("repository"), field="spec.repository")
    branch_naming = _as_mapping(repository_raw.get("branch_naming"), field="spec.repository.branch_naming")
    allowed_prefixes = _as_list_of_str(
        branch_naming.get("purpose_prefixes", []),
        field="spec.repository.branch_naming.purpose_prefixes",
    )
    default_branch = str(repository_raw.get("default_branch", "")).strip()
    sdd_raw = _as_mapping(
        spec_raw.get("spec_driven_development_contract"),
        field="spec.spec_driven_development_contract",
    )
    branch_contract = _as_optional_mapping(
        sdd_raw.get("branch_contract"),
        field="spec.spec_driven_development_contract.branch_contract",
    )
    artifacts = _as_mapping(
        sdd_raw.get("artifacts"),
        field="spec.spec_driven_development_contract.artifacts",
    )
    dedicated_branch_required = bool(branch_contract.get("dedicated_branch_required_by_default", True))
    enforce_non_default_branch = bool(branch_contract.get("enforce_non_default_branch", True))
    default_prefix = str(branch_contract.get("default_prefix", "")).strip()
    required_documents = _as_list_of_str(
        artifacts.get("required_work_item_documents", []),
        field="spec.spec_driven_development_contract.artifacts.required_work_item_documents",
    )
    if not required_documents:
        raise ValueError(
            "spec.spec_driven_development_contract.artifacts.required_work_item_documents must not be empty"
        )

    template_root = repo_root / _resolve_template_root(artifacts, args.track)

    active_branch = _current_branch(repo_root)
    if dedicated_branch_required and not args.no_create_branch:
        requested_branch = str(args.branch or "").strip()
        auto_generated_branch = not requested_branch
        if auto_generated_branch:
            branch_prefix = _resolve_branch_prefix(allowed_prefixes=allowed_prefixes, preferred_prefix=default_prefix)
            requested_branch = f"{branch_prefix}{work_date.isoformat()}-{slug}"

        if not _matches_allowed_prefix(branch_name=requested_branch, allowed_prefixes=allowed_prefixes):
            raise ValueError(
                "branch name must start with one of repository.branch_naming.purpose_prefixes: "
                + ", ".join(allowed_prefixes)
            )
        if enforce_non_default_branch and default_branch and requested_branch == default_branch:
            raise ValueError(f"branch name must not equal default branch: {default_branch}")

        target_branch = requested_branch
        if auto_generated_branch:
            target_branch = _ensure_unique_branch(repo_root, requested_branch)
        elif active_branch != requested_branch and _branch_exists(repo_root, requested_branch):
            raise ValueError(
                f"requested branch already exists and is not current: {requested_branch} "
                "(pass a unique --branch name)"
            )

        if active_branch != target_branch:
            _run_git(repo_root, "checkout", "-b", target_branch)
            active_branch = target_branch

    destination = repo_root / "specs" / f"{work_date.isoformat()}-{slug}"
    if destination.exists() and not args.force:
        raise ValueError(f"destination already exists: {destination.relative_to(repo_root)} (use --force to overwrite)")

    destination.mkdir(parents=True, exist_ok=True)
    for document in required_documents:
        source_path = template_root / document
        if not source_path.is_file():
            raise ValueError(f"missing template document: {source_path.relative_to(repo_root)}")
        _copy_document(source_path, destination / document)

    print(f"scaffolded SDD work item: {destination.relative_to(repo_root)}")
    for document in required_documents:
        print(f"  - {document}")
    if dedicated_branch_required and not args.no_create_branch:
        print(f"active SDD branch: {active_branch}")
    elif args.no_create_branch:
        print(f"branch auto-creation skipped (--no-create-branch); current branch: {active_branch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
