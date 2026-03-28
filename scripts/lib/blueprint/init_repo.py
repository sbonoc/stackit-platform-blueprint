#!/usr/bin/env python3
"""Initialize repository identity after GitHub template instantiation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import (  # noqa: E402
    ChangeSummary,
    render_template,
    resolve_repo_root,
)
from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402


def _replace_scalar_once(content: str, pattern: str, replacement: str, label: str) -> str:
    compiled = re.compile(pattern, flags=re.MULTILINE)
    updated, count = compiled.subn(replacement, content, count=1)
    if count != 1:
        raise ValueError(f"unable to update {label}")
    return updated


def _replace_js_string_key(content: str, key: str, value: str, label: str) -> str:
    pattern = re.compile(rf'^(\s*{re.escape(key)}:\s*")[^"]*(".*)$', flags=re.MULTILINE)

    def repl(match: re.Match[str]) -> str:
        return f'{match.group(1)}{value}{match.group(2)}'

    updated, count = pattern.subn(repl, content, count=1)
    if count != 1:
        raise ValueError(f"unable to update {label}")
    return updated


def _replace_quoted_assignment_once(content: str, key: str, value: str, label: str) -> str:
    pattern = re.compile(rf'^(\s*{re.escape(key)}\s*=\s*")[^"]*(".*)$', flags=re.MULTILINE)

    def repl(match: re.Match[str]) -> str:
        return f'{match.group(1)}{value}{match.group(2)}'

    updated, count = pattern.subn(repl, content, count=1)
    if count != 1:
        raise ValueError(f"unable to update {label}")
    return updated


def _render_contract(
    content: str,
    repo_name: str,
    default_branch: str,
    repo_mode: str,
) -> str:
    content = _replace_scalar_once(
        content,
        r"^(\s*name:\s*).+$",
        rf"\1{repo_name}",
        "blueprint contract metadata.name",
    )
    content = _replace_scalar_once(
        content,
        r"^(\s*default_branch:\s*).+$",
        rf"\1{default_branch}",
        "blueprint contract repository.default_branch",
    )
    content = _replace_scalar_once(
        content,
        r"^(\s*repo_mode:\s*).+$",
        rf"\1{repo_mode}",
        "blueprint contract repository.repo_mode",
    )
    return content


def _render_docusaurus_config(
    content: str,
    docs_title: str,
    docs_tagline: str,
    github_org: str,
    github_repo: str,
    default_branch: str,
) -> str:
    edit_url = f"https://github.com/{github_org}/{github_repo}/edit/{default_branch}/docs/"

    content = _replace_js_string_key(content, "title", docs_title, "docs title")
    content = _replace_js_string_key(content, "tagline", docs_tagline, "docs tagline")
    content = _replace_js_string_key(content, "organizationName", github_org, "docs organizationName")
    content = _replace_js_string_key(content, "projectName", github_repo, "docs projectName")
    content = _replace_js_string_key(content, "editUrl", edit_url, "docs editUrl")
    return content


def _render_argocd_repo_urls(
    content: str,
    github_org: str,
    github_repo: str,
) -> str:
    repo_url = f"https://github.com/{github_org}/{github_repo}.git"

    content = re.sub(
        r"(^\s*repoURL:\s*)https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git(\s*$)",
        rf"\g<1>{repo_url}\g<2>",
        content,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r"(^\s*-\s*)https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git(\s*$)",
        rf"\g<1>{repo_url}\g<2>",
        content,
        flags=re.MULTILINE,
    )
    return content


def _render_stackit_bootstrap_tfvars(
    content: str,
    environment: str,
    stackit_region: str,
    tenant_slug: str,
    platform_slug: str,
    stackit_project_id: str,
    stackit_tfstate_key_prefix: str,
) -> str:
    content = _replace_quoted_assignment_once(
        content,
        "environment",
        environment,
        f"bootstrap tfvars {environment} environment",
    )
    content = _replace_quoted_assignment_once(
        content,
        "stackit_region",
        stackit_region,
        f"bootstrap tfvars {environment} stackit_region",
    )
    content = _replace_quoted_assignment_once(
        content,
        "tenant_slug",
        tenant_slug,
        f"bootstrap tfvars {environment} tenant_slug",
    )
    content = _replace_quoted_assignment_once(
        content,
        "platform_slug",
        platform_slug,
        f"bootstrap tfvars {environment} platform_slug",
    )
    content = _replace_quoted_assignment_once(
        content,
        "stackit_project_id",
        stackit_project_id,
        f"bootstrap tfvars {environment} stackit_project_id",
    )
    content = _replace_quoted_assignment_once(
        content,
        "state_key_prefix",
        stackit_tfstate_key_prefix,
        f"bootstrap tfvars {environment} state_key_prefix",
    )
    return content


def _render_stackit_foundation_tfvars(
    content: str,
    environment: str,
    stackit_region: str,
    tenant_slug: str,
    platform_slug: str,
    stackit_project_id: str,
) -> str:
    content = _replace_quoted_assignment_once(
        content,
        "environment",
        environment,
        f"foundation tfvars {environment} environment",
    )
    content = _replace_quoted_assignment_once(
        content,
        "tenant_slug",
        tenant_slug,
        f"foundation tfvars {environment} tenant_slug",
    )
    content = _replace_quoted_assignment_once(
        content,
        "platform_slug",
        platform_slug,
        f"foundation tfvars {environment} platform_slug",
    )
    content = _replace_quoted_assignment_once(
        content,
        "stackit_project_id",
        stackit_project_id,
        f"foundation tfvars {environment} stackit_project_id",
    )
    content = _replace_quoted_assignment_once(
        content,
        "stackit_region",
        stackit_region,
        f"foundation tfvars {environment} stackit_region",
    )
    return content


def _render_stackit_backend_hcl(
    content: str,
    environment: str,
    layer: str,
    stackit_region: str,
    stackit_tfstate_bucket: str,
    stackit_tfstate_key_prefix: str,
) -> str:
    content = _replace_quoted_assignment_once(
        content,
        "bucket",
        stackit_tfstate_bucket,
        f"{layer} backend {environment} bucket",
    )
    content = _replace_quoted_assignment_once(
        content,
        "key",
        f"{stackit_tfstate_key_prefix}/{environment}/{layer}.tfstate",
        f"{layer} backend {environment} key",
    )
    content = _replace_quoted_assignment_once(
        content,
        "region",
        stackit_region,
        f"{layer} backend {environment} region",
    )
    content = _replace_scalar_once(
        content,
        r'(^\s*s3\s*=\s*")https://object\.storage\.[^"]+(".*$)',
        rf'\1https://object.storage.{stackit_region}.onstackit.cloud\2',
        f"{layer} backend {environment} s3 endpoint",
    )
    return content


def _apply_file_update(
    path: Path,
    original: str | None,
    updated: str,
    dry_run: bool,
    summary: ChangeSummary,
) -> bool:
    original_content = original if original is not None else ""
    changed = original is None or updated != original_content
    if not changed:
        summary.skipped_path(path, "no change required")
        return False

    if dry_run:
        if original is None:
            summary.created_path(path)
        else:
            summary.updated_path(path)
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")
    if original is None:
        summary.created_path(path)
    else:
        summary.updated_path(path)
    return True


def _remove_path(path: Path, dry_run: bool, summary: ChangeSummary) -> bool:
    if not path.exists():
        summary.skipped_path(path, "already absent")
        return False

    if dry_run:
        summary.removed_path(path)
        return True

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    summary.removed_path(path)
    return True


def _normalize_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _expand_optional_module_path(path_value: str) -> list[str]:
    if "${ENV}" not in path_value:
        return [path_value]
    return [path_value.replace("${ENV}", env) for env in ("local", "dev", "stage", "prod")]


def _seed_consumer_owned_files(
    repo_root: Path,
    dry_run: bool,
    summary: ChangeSummary,
    replacements: dict[str, str],
) -> None:
    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    repository = contract.repository
    consumer_init = repository.consumer_init
    if repository.repo_mode != consumer_init.mode_from:
        summary.skipped_path(repo_root / "README.md", f"consumer-owned seed already applied ({repository.repo_mode})")
        return

    template_root = repo_root / consumer_init.template_root
    for relative_path in repository.consumer_seeded_paths:
        target_path = repo_root / relative_path
        template_path = template_root / f"{relative_path}.tmpl"
        original = target_path.read_text(encoding="utf-8") if target_path.is_file() else None
        updated = render_template(template_path.read_text(encoding="utf-8"), replacements)
        _apply_file_update(target_path, original, updated, dry_run, summary)

    for relative_path in repository.source_only_paths:
        _remove_path(repo_root / relative_path, dry_run, summary)

    if not consumer_init.prune_disabled_optional_scaffolding:
        return

    for module in contract.optional_modules.modules.values():
        if module.scaffolding_mode != "conditional":
            continue

        env_value = os.environ.get(module.enable_flag)
        module_enabled = module.enabled_by_default if env_value is None else _normalize_bool(env_value)
        if module_enabled:
            continue

        for path_key in module.paths_required_when_enabled:
            for expanded in _expand_optional_module_path(module.paths[path_key]):
                _remove_path(repo_root / expanded.rstrip("/"), dry_run, summary)


def _target_repo_mode(repo_root: Path) -> str:
    repository = load_blueprint_contract(repo_root / "blueprint/contract.yaml").repository
    if repository.repo_mode == repository.consumer_init.mode_from:
        return repository.consumer_init.mode_to
    return repository.repo_mode


def _consumer_template_replacements(args: argparse.Namespace, repo_root: Path) -> dict[str, str]:
    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    return {
        "REPO_NAME": args.repo_name,
        "DOCS_TITLE": args.docs_title,
        "DOCS_TAGLINE": args.docs_tagline,
        "DEFAULT_BRANCH": args.default_branch,
        "TEMPLATE_VERSION": contract.repository.template_bootstrap.template_version,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Absolute repository root path.")
    parser.add_argument("--repo-name", required=True, help="Repository slug for contract metadata.")
    parser.add_argument("--github-org", required=True, help="GitHub org/user for edit links.")
    parser.add_argument("--github-repo", required=True, help="GitHub repo for edit links.")
    parser.add_argument("--default-branch", required=True, help="Default branch name.")
    parser.add_argument("--docs-title", required=True, help="Docusaurus site title.")
    parser.add_argument("--docs-tagline", required=True, help="Docusaurus site tagline.")
    parser.add_argument("--stackit-region", required=True, help="STACKIT region for tfvars/backend contracts.")
    parser.add_argument("--stackit-tenant-slug", required=True, help="Tenant slug for STACKIT naming contracts.")
    parser.add_argument("--stackit-platform-slug", required=True, help="Platform slug for STACKIT naming contracts.")
    parser.add_argument("--stackit-project-id", required=True, help="STACKIT project identifier for foundation tfvars.")
    parser.add_argument("--stackit-tfstate-bucket", required=True, help="Object Storage bucket for Terraform state.")
    parser.add_argument(
        "--stackit-tfstate-key-prefix",
        required=True,
        help="Terraform state key prefix used by STACKIT backend files and bootstrap tfvars.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview updates without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    contract_path = repo_root / "blueprint/contract.yaml"
    docusaurus_path = repo_root / "docs/docusaurus.config.js"
    summary = ChangeSummary("blueprint-init-repo")
    consumer_replacements = _consumer_template_replacements(args, repo_root)
    argocd_paths = [
        repo_root / "infra/gitops/argocd/root/applicationset-platform-environments.yaml",
        repo_root / "infra/gitops/argocd/environments/dev/platform-application.yaml",
        repo_root / "infra/gitops/argocd/environments/stage/platform-application.yaml",
        repo_root / "infra/gitops/argocd/environments/prod/platform-application.yaml",
        repo_root / "infra/gitops/argocd/overlays/local/appproject.yaml",
        repo_root / "infra/gitops/argocd/overlays/local/application-platform-local.yaml",
        repo_root / "infra/gitops/argocd/overlays/dev/appproject.yaml",
        repo_root / "infra/gitops/argocd/overlays/dev/applicationset-platform-environments.yaml",
        repo_root / "infra/gitops/argocd/overlays/stage/appproject.yaml",
        repo_root / "infra/gitops/argocd/overlays/stage/applicationset-platform-environments.yaml",
        repo_root / "infra/gitops/argocd/overlays/prod/appproject.yaml",
        repo_root / "infra/gitops/argocd/overlays/prod/applicationset-platform-environments.yaml",
    ]
    stackit_bootstrap_tfvars_paths = [
        (repo_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars", "dev"),
        (repo_root / "infra/cloud/stackit/terraform/bootstrap/env/stage.tfvars", "stage"),
        (repo_root / "infra/cloud/stackit/terraform/bootstrap/env/prod.tfvars", "prod"),
    ]
    stackit_foundation_tfvars_paths = [
        (repo_root / "infra/cloud/stackit/terraform/foundation/env/dev.tfvars", "dev"),
        (repo_root / "infra/cloud/stackit/terraform/foundation/env/stage.tfvars", "stage"),
        (repo_root / "infra/cloud/stackit/terraform/foundation/env/prod.tfvars", "prod"),
    ]
    stackit_bootstrap_backend_paths = [
        (repo_root / "infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl", "dev"),
        (repo_root / "infra/cloud/stackit/terraform/bootstrap/state-backend/stage.hcl", "stage"),
        (repo_root / "infra/cloud/stackit/terraform/bootstrap/state-backend/prod.hcl", "prod"),
    ]
    stackit_foundation_backend_paths = [
        (repo_root / "infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl", "dev"),
        (repo_root / "infra/cloud/stackit/terraform/foundation/state-backend/stage.hcl", "stage"),
        (repo_root / "infra/cloud/stackit/terraform/foundation/state-backend/prod.hcl", "prod"),
    ]

    _seed_consumer_owned_files(
        repo_root=repo_root,
        dry_run=args.dry_run,
        summary=summary,
        replacements=consumer_replacements,
    )

    contract_original = contract_path.read_text(encoding="utf-8")
    contract_updated = _render_contract(
        content=contract_original,
        repo_name=args.repo_name,
        default_branch=args.default_branch,
        repo_mode=_target_repo_mode(repo_root),
    )
    docusaurus_original = docusaurus_path.read_text(encoding="utf-8")
    docusaurus_updated = _render_docusaurus_config(
        content=docusaurus_original,
        docs_title=args.docs_title,
        docs_tagline=args.docs_tagline,
        github_org=args.github_org,
        github_repo=args.github_repo,
        default_branch=args.default_branch,
    )
    _apply_file_update(contract_path, contract_original, contract_updated, args.dry_run, summary)
    _apply_file_update(docusaurus_path, docusaurus_original, docusaurus_updated, args.dry_run, summary)
    for argocd_path in argocd_paths:
        if not argocd_path.is_file():
            continue
        argocd_original = argocd_path.read_text(encoding="utf-8")
        argocd_updated = _render_argocd_repo_urls(
            content=argocd_original,
            github_org=args.github_org,
            github_repo=args.github_repo,
        )
        _apply_file_update(argocd_path, argocd_original, argocd_updated, args.dry_run, summary)

    for tfvars_path, environment in stackit_bootstrap_tfvars_paths:
        if not tfvars_path.is_file():
            continue
        tfvars_original = tfvars_path.read_text(encoding="utf-8")
        tfvars_updated = _render_stackit_bootstrap_tfvars(
            content=tfvars_original,
            environment=environment,
            stackit_region=args.stackit_region,
            tenant_slug=args.stackit_tenant_slug,
            platform_slug=args.stackit_platform_slug,
            stackit_project_id=args.stackit_project_id,
            stackit_tfstate_key_prefix=args.stackit_tfstate_key_prefix,
        )
        _apply_file_update(tfvars_path, tfvars_original, tfvars_updated, args.dry_run, summary)

    for tfvars_path, environment in stackit_foundation_tfvars_paths:
        if not tfvars_path.is_file():
            continue
        tfvars_original = tfvars_path.read_text(encoding="utf-8")
        tfvars_updated = _render_stackit_foundation_tfvars(
            content=tfvars_original,
            environment=environment,
            stackit_region=args.stackit_region,
            tenant_slug=args.stackit_tenant_slug,
            platform_slug=args.stackit_platform_slug,
            stackit_project_id=args.stackit_project_id,
        )
        _apply_file_update(tfvars_path, tfvars_original, tfvars_updated, args.dry_run, summary)

    for backend_path, environment in stackit_bootstrap_backend_paths:
        if not backend_path.is_file():
            continue
        backend_original = backend_path.read_text(encoding="utf-8")
        backend_updated = _render_stackit_backend_hcl(
            content=backend_original,
            environment=environment,
            layer="bootstrap",
            stackit_region=args.stackit_region,
            stackit_tfstate_bucket=args.stackit_tfstate_bucket,
            stackit_tfstate_key_prefix=args.stackit_tfstate_key_prefix,
        )
        _apply_file_update(backend_path, backend_original, backend_updated, args.dry_run, summary)

    for backend_path, environment in stackit_foundation_backend_paths:
        if not backend_path.is_file():
            continue
        backend_original = backend_path.read_text(encoding="utf-8")
        backend_updated = _render_stackit_backend_hcl(
            content=backend_original,
            environment=environment,
            layer="foundation",
            stackit_region=args.stackit_region,
            stackit_tfstate_bucket=args.stackit_tfstate_bucket,
            stackit_tfstate_key_prefix=args.stackit_tfstate_key_prefix,
        )
        _apply_file_update(backend_path, backend_original, backend_updated, args.dry_run, summary)

    summary.emit(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
