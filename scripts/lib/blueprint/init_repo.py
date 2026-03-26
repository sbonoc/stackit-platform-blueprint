#!/usr/bin/env python3
"""Initialize repository identity after GitHub template instantiation."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


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


def _apply_file_update(path: Path, original: str, updated: str, dry_run: bool) -> bool:
    changed = updated != original
    if not changed:
        print(f"no change required: {path}")
        return False

    if dry_run:
        print(f"[dry-run] would update: {path}")
        return True

    path.write_text(updated, encoding="utf-8")
    print(f"updated: {path}")
    return True


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
    repo_root = Path(args.repo_root).resolve()
    contract_path = repo_root / "blueprint/contract.yaml"
    docusaurus_path = repo_root / "docs/docusaurus.config.js"
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

    contract_original = contract_path.read_text(encoding="utf-8")
    contract_updated = _render_contract(
        content=contract_original,
        repo_name=args.repo_name,
        default_branch=args.default_branch,
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
    changed_count = 0
    changed_count += int(
        _apply_file_update(contract_path, contract_original, contract_updated, args.dry_run)
    )
    changed_count += int(
        _apply_file_update(docusaurus_path, docusaurus_original, docusaurus_updated, args.dry_run)
    )
    for argocd_path in argocd_paths:
        if not argocd_path.is_file():
            continue
        argocd_original = argocd_path.read_text(encoding="utf-8")
        argocd_updated = _render_argocd_repo_urls(
            content=argocd_original,
            github_org=args.github_org,
            github_repo=args.github_repo,
        )
        changed_count += int(_apply_file_update(argocd_path, argocd_original, argocd_updated, args.dry_run))

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
        changed_count += int(_apply_file_update(tfvars_path, tfvars_original, tfvars_updated, args.dry_run))

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
        changed_count += int(_apply_file_update(tfvars_path, tfvars_original, tfvars_updated, args.dry_run))

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
        changed_count += int(_apply_file_update(backend_path, backend_original, backend_updated, args.dry_run))

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
        changed_count += int(_apply_file_update(backend_path, backend_original, backend_updated, args.dry_run))

    if args.dry_run:
        print(f"[dry-run] summary: {changed_count} file(s) would be updated")
    else:
        print(f"summary: updated {changed_count} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
