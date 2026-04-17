"""Contract-aware helpers for blueprint init-repo."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from scripts.lib.blueprint.cli_support import ChangeSummary, render_template
from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from scripts.lib.blueprint.init_repo_io import apply_file_update, remove_path

BLUEPRINT_TEMPLATE_ROOT = Path("scripts/templates/blueprint/bootstrap")
INFRA_TEMPLATE_ROOT = Path("scripts/templates/infra/bootstrap")


def load_blueprint_contract_for_init(repo_root: Path):
    contract_path = repo_root / "blueprint/contract.yaml"
    if contract_path.is_file():
        return load_blueprint_contract(contract_path)
    return load_blueprint_contract(repo_root / BLUEPRINT_TEMPLATE_ROOT / "blueprint/contract.yaml")


def normalize_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def expand_optional_module_path(path_value: str) -> list[str]:
    if "${ENV}" not in path_value:
        return [path_value]
    return [path_value.replace("${ENV}", env) for env in ("local", "dev", "stage", "prod")]


def resolve_optional_module_enablement(repo_root: Path) -> dict[str, bool]:
    contract = load_blueprint_contract_for_init(repo_root)
    module_enablement: dict[str, bool] = {}
    for module in contract.optional_modules.modules.values():
        env_value = os.environ.get(module.enable_flag)
        module_enablement[module.module_id] = (
            module.enabled_by_default if env_value is None else normalize_bool(env_value)
        )
    return module_enablement


def resolve_app_catalog_scaffold_contract(repo_root: Path) -> tuple[bool, list[str]]:
    contract = load_blueprint_contract_for_init(repo_root)
    spec_raw = contract.raw.get("spec")
    if not isinstance(spec_raw, dict):
        return True, []

    scaffold_raw = spec_raw.get("app_catalog_scaffold_contract")
    if not isinstance(scaffold_raw, dict):
        return True, []

    enabled_by_default_raw = scaffold_raw.get("enabled_by_default")
    enabled_by_default = enabled_by_default_raw if isinstance(enabled_by_default_raw, bool) else False
    enable_flag_raw = scaffold_raw.get("enable_flag")
    enable_flag = enable_flag_raw if isinstance(enable_flag_raw, str) else ""
    env_value = os.environ.get(enable_flag) if enable_flag else None
    enabled = enabled_by_default if env_value is None else normalize_bool(env_value)

    required_paths_raw = scaffold_raw.get("required_paths_when_enabled")
    required_paths: list[str] = []
    if isinstance(required_paths_raw, list):
        for raw_path in required_paths_raw:
            if not isinstance(raw_path, str):
                continue
            stripped = raw_path.strip().rstrip("/")
            if stripped:
                required_paths.append(stripped)

    return enabled, required_paths


def _is_safe_relative_glob_pattern(pattern: str) -> bool:
    candidate = pattern.strip()
    if not candidate:
        return False

    parsed = Path(candidate)
    if parsed.is_absolute():
        return False

    if any(part == ".." for part in parsed.parts):
        return False

    if any(part == ".." for part in candidate.replace("\\", "/").split("/")):
        return False

    return True


def _is_within_repo_root(path: Path, repo_root: Path) -> bool:
    try:
        path.relative_to(repo_root)
        return True
    except ValueError:
        return False


def prune_source_artifacts_on_initial_init(
    repo_root: Path,
    summary: ChangeSummary,
    *,
    dry_run: bool,
    repo_mode: str,
    mode_from: str,
    prune_globs: list[str],
) -> None:
    if repo_mode != mode_from:
        return

    repo_root_resolved = repo_root.resolve()
    for raw_pattern in prune_globs:
        pattern = raw_pattern.strip()
        if not pattern:
            continue

        if not _is_safe_relative_glob_pattern(pattern):
            summary.skipped_path(repo_root / pattern, "unsafe prune glob ignored")
            continue

        for matched_path in sorted(repo_root.glob(pattern)):
            resolved_path = matched_path.resolve(strict=False)
            if not _is_within_repo_root(resolved_path, repo_root_resolved):
                summary.skipped_path(matched_path, "prune candidate resolves outside repository root")
                continue
            remove_path(matched_path, dry_run, summary)


def seed_consumer_owned_files(
    repo_root: Path,
    dry_run: bool,
    force: bool,
    summary: ChangeSummary,
    replacements: dict[str, str],
    module_enablement: dict[str, bool],
) -> None:
    contract = load_blueprint_contract_for_init(repo_root)
    repository = contract.repository
    consumer_init = repository.consumer_init
    allow_reseed = repository.repo_mode == consumer_init.mode_from or force or dry_run
    if not allow_reseed:
        summary.skipped_path(repo_root / "README.md", f"consumer-owned seed already applied ({repository.repo_mode})")
        return

    template_root = repo_root / consumer_init.template_root
    for relative_path in repository.consumer_seeded_paths:
        target_path = repo_root / relative_path
        template_path = template_root / f"{relative_path}.tmpl"
        original = target_path.read_text(encoding="utf-8") if target_path.is_file() else None
        updated = render_template(template_path.read_text(encoding="utf-8"), replacements)
        apply_file_update(target_path, original, updated, dry_run, summary)

    for relative_path in repository.source_only_paths:
        remove_path(repo_root / relative_path, dry_run, summary)

    prune_source_artifacts_on_initial_init(
        repo_root=repo_root,
        summary=summary,
        dry_run=dry_run,
        repo_mode=repository.repo_mode,
        mode_from=consumer_init.mode_from,
        prune_globs=consumer_init.source_artifact_prune_globs_on_init,
    )

    if not consumer_init.prune_disabled_optional_scaffolding:
        return

    for module in contract.optional_modules.modules.values():
        if module.scaffolding_mode != "conditional":
            continue
        if module_enablement[module.module_id]:
            continue
        for path_key in module.paths_required_when_enabled:
            for expanded in expand_optional_module_path(module.paths[path_key]):
                remove_path(repo_root / expanded.rstrip("/"), dry_run, summary)

    app_catalog_enabled, app_catalog_required_paths = resolve_app_catalog_scaffold_contract(repo_root)
    if not app_catalog_enabled:
        for relative_path in app_catalog_required_paths:
            remove_path(repo_root / relative_path, dry_run, summary)


def target_repo_mode(repo_root: Path) -> str:
    repository = load_blueprint_contract_for_init(repo_root).repository
    if repository.repo_mode == repository.consumer_init.mode_from:
        return repository.consumer_init.mode_to
    return repository.repo_mode


def consumer_template_replacements(args: argparse.Namespace, repo_root: Path) -> dict[str, str]:
    contract = load_blueprint_contract_for_init(repo_root)
    return {
        "REPO_NAME": args.repo_name,
        "DOCS_TITLE": args.docs_title,
        "DOCS_TAGLINE": args.docs_tagline,
        "DEFAULT_BRANCH": args.default_branch,
        "TEMPLATE_VERSION": contract.repository.template_bootstrap.template_version,
    }
