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
