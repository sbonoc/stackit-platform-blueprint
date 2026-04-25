#!/usr/bin/env python3
"""Initialize repository identity after GitHub template instantiation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.cli_support import ChangeSummary, resolve_repo_root  # noqa: E402
from scripts.lib.blueprint.init_repo_contract import (  # noqa: E402
    BLUEPRINT_TEMPLATE_ROOT,
    INFRA_TEMPLATE_ROOT,
    consumer_template_replacements as _consumer_template_replacements,
    load_blueprint_contract_for_init as _load_blueprint_contract_for_init,
    resolve_optional_module_enablement as _resolve_optional_module_enablement,
    seed_consumer_owned_files as _seed_consumer_owned_files,
    target_repo_mode as _target_repo_mode,
)
from scripts.lib.blueprint.init_repo_env import (  # noqa: E402
    ensure_defaults_env_file as _ensure_defaults_env_file,
    ensure_local_secrets_env_file as _ensure_local_secrets_env_file,
    ensure_secrets_example_env_file as _ensure_secrets_example_env_file,
)
from scripts.lib.blueprint.init_repo_io import (  # noqa: E402
    apply_file_update as _apply_file_update,
    read_existing_or_template as _read_existing_or_template,
)
from scripts.lib.blueprint.init_repo_renderers import (  # noqa: E402
    render_argocd_repo_urls as _render_argocd_repo_urls,
    render_contract as _render_contract,
    render_docusaurus_config as _render_docusaurus_config,
    render_stackit_backend_hcl as _render_stackit_backend_hcl,
    render_stackit_bootstrap_tfvars as _render_stackit_bootstrap_tfvars,
    render_stackit_foundation_tfvars as _render_stackit_foundation_tfvars,
)


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
    parser.add_argument("--force", action="store_true", help="Allow re-applying init in generated-consumer repos.")
    parser.add_argument("--dry-run", action="store_true", help="Preview updates without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root, __file__)
    repository = _load_blueprint_contract_for_init(repo_root).repository
    if (
        repository.repo_mode == repository.consumer_init.mode_to
        and not args.force
        and not args.dry_run
    ):
        print(
            "blueprint-init-repo already completed for this generated repository; "
            f"rerun only with {repository.template_bootstrap.force_env_var}=true",
            file=sys.stderr,
        )
        return 1

    contract_path = repo_root / "blueprint/contract.yaml"
    docusaurus_path = repo_root / "docs/docusaurus.config.js"
    summary = ChangeSummary("blueprint-init-repo")
    consumer_replacements = _consumer_template_replacements(args, repo_root)
    module_enablement = _resolve_optional_module_enablement(repo_root)

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

    # Generate env files BEFORE seeding consumer-owned files.  seed_consumer_owned_files
    # removes source_only paths (including blueprint/modules/) which contain the per-module
    # contract YAML that ensure_defaults_env_file needs to resolve module-specific env specs.
    # The env files themselves are not source_only, so generating them first is safe.
    _ensure_defaults_env_file(
        repo_root=repo_root,
        args=args,
        dry_run=args.dry_run,
        summary=summary,
        module_enablement=module_enablement,
    )
    _ensure_secrets_example_env_file(
        repo_root=repo_root,
        dry_run=args.dry_run,
        summary=summary,
        module_enablement=module_enablement,
    )
    _ensure_local_secrets_env_file(
        repo_root=repo_root,
        dry_run=args.dry_run,
        summary=summary,
        module_enablement=module_enablement,
    )

    _seed_consumer_owned_files(
        repo_root=repo_root,
        dry_run=args.dry_run,
        force=args.force,
        summary=summary,
        replacements=consumer_replacements,
        module_enablement=module_enablement,
    )

    contract_original, contract_base = _read_existing_or_template(
        repo_root,
        contract_path,
        BLUEPRINT_TEMPLATE_ROOT,
        "blueprint/contract.yaml",
    )
    contract_updated = _render_contract(
        content=contract_base,
        repo_name=args.repo_name,
        default_branch=args.default_branch,
        repo_mode=_target_repo_mode(repo_root),
        module_enablement=module_enablement,
    )
    docusaurus_original, docusaurus_base = _read_existing_or_template(
        repo_root,
        docusaurus_path,
        BLUEPRINT_TEMPLATE_ROOT,
        "docs/docusaurus.config.js",
    )
    docusaurus_updated = _render_docusaurus_config(
        content=docusaurus_base,
        docs_title=args.docs_title,
        docs_tagline=args.docs_tagline,
        github_org=args.github_org,
        github_repo=args.github_repo,
        default_branch=args.default_branch,
    )
    _apply_file_update(contract_path, contract_original, contract_updated, args.dry_run, summary)
    _apply_file_update(docusaurus_path, docusaurus_original, docusaurus_updated, args.dry_run, summary)

    for argocd_path in argocd_paths:
        argocd_original, argocd_base = _read_existing_or_template(
            repo_root,
            argocd_path,
            INFRA_TEMPLATE_ROOT,
            argocd_path.relative_to(repo_root).as_posix(),
        )
        argocd_updated = _render_argocd_repo_urls(
            content=argocd_base,
            github_org=args.github_org,
            github_repo=args.github_repo,
        )
        _apply_file_update(argocd_path, argocd_original, argocd_updated, args.dry_run, summary)

    for tfvars_path, environment in stackit_bootstrap_tfvars_paths:
        tfvars_original, tfvars_base = _read_existing_or_template(
            repo_root,
            tfvars_path,
            INFRA_TEMPLATE_ROOT,
            tfvars_path.relative_to(repo_root).as_posix(),
        )
        tfvars_updated = _render_stackit_bootstrap_tfvars(
            content=tfvars_base,
            environment=environment,
            stackit_region=args.stackit_region,
            tenant_slug=args.stackit_tenant_slug,
            platform_slug=args.stackit_platform_slug,
            stackit_project_id=args.stackit_project_id,
            stackit_tfstate_key_prefix=args.stackit_tfstate_key_prefix,
        )
        _apply_file_update(tfvars_path, tfvars_original, tfvars_updated, args.dry_run, summary)

    for tfvars_path, environment in stackit_foundation_tfvars_paths:
        tfvars_original, tfvars_base = _read_existing_or_template(
            repo_root,
            tfvars_path,
            INFRA_TEMPLATE_ROOT,
            tfvars_path.relative_to(repo_root).as_posix(),
        )
        tfvars_updated = _render_stackit_foundation_tfvars(
            content=tfvars_base,
            environment=environment,
            stackit_region=args.stackit_region,
            tenant_slug=args.stackit_tenant_slug,
            platform_slug=args.stackit_platform_slug,
            stackit_project_id=args.stackit_project_id,
        )
        _apply_file_update(tfvars_path, tfvars_original, tfvars_updated, args.dry_run, summary)

    for backend_path, environment in stackit_bootstrap_backend_paths:
        backend_original, backend_base = _read_existing_or_template(
            repo_root,
            backend_path,
            INFRA_TEMPLATE_ROOT,
            backend_path.relative_to(repo_root).as_posix(),
        )
        backend_updated = _render_stackit_backend_hcl(
            content=backend_base,
            environment=environment,
            layer="bootstrap",
            stackit_region=args.stackit_region,
            stackit_tfstate_bucket=args.stackit_tfstate_bucket,
            stackit_tfstate_key_prefix=args.stackit_tfstate_key_prefix,
        )
        _apply_file_update(backend_path, backend_original, backend_updated, args.dry_run, summary)

    for backend_path, environment in stackit_foundation_backend_paths:
        backend_original, backend_base = _read_existing_or_template(
            repo_root,
            backend_path,
            INFRA_TEMPLATE_ROOT,
            backend_path.relative_to(repo_root).as_posix(),
        )
        backend_updated = _render_stackit_backend_hcl(
            content=backend_base,
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
