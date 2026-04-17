from __future__ import annotations

import re
from pathlib import Path

from scripts.lib.blueprint.contract_schema import BlueprintContract
from scripts.lib.blueprint.contract_validators.shared import ContractValidationHelpers


def _extract_area_tokens(area_cell: str) -> set[str]:
    tokens = {match.strip() for match in re.findall(r"`([^`]+)`", area_cell) if match.strip()}
    if tokens:
        return tokens
    return {token.strip() for token in area_cell.split(",") if token.strip()}


def validate_source_artifact_prune_globs_documented(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    prune_globs = contract.repository.consumer_init.source_artifact_prune_globs_on_init
    if not prune_globs:
        return errors

    blueprint_docs_root = contract.docs_contract.blueprint_docs.root
    ownership_matrix_relative = f"{blueprint_docs_root}/governance/ownership_matrix.md"
    ownership_matrix_path = repo_root / ownership_matrix_relative
    if not ownership_matrix_path.is_file():
        return [f"missing ownership matrix file: {ownership_matrix_relative}"]

    source_only_area_tokens: set[str] = set()
    for line in ownership_matrix_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue

        area_cell, ownership_cell = cells[0], cells[1]
        if "source only" not in ownership_cell.lower():
            continue
        source_only_area_tokens.update(_extract_area_tokens(area_cell))

    if not source_only_area_tokens:
        errors.append(
            "ownership matrix must include at least one 'source only' row for prune-glob documentation checks"
        )
        return errors

    for pattern in prune_globs:
        if pattern in source_only_area_tokens:
            continue
        errors.append(
            "repository.consumer_init.source_artifact_prune_globs_on_init pattern must be documented "
            f"in ownership matrix source-only rows ({ownership_matrix_relative}): {pattern}"
        )

    return errors


def validate_docs_edit_link(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    if not contract.docs_contract.edit_link_enabled:
        return errors

    docusaurus_config = repo_root / "docs/docusaurus.config.js"
    if not docusaurus_config.is_file():
        return ["missing docs config file: docs/docusaurus.config.js"]

    content = docusaurus_config.read_text(encoding="utf-8")
    if "editUrl" not in content:
        errors.append("docs edit_link_enabled=true requires editUrl in docs/docusaurus.config.js")
    return errors


def validate_platform_docs_seed_contract(
    repo_root: Path,
    contract: BlueprintContract,
    helpers: ContractValidationHelpers,
) -> list[str]:
    errors: list[str] = []
    platform_docs = contract.docs_contract.platform_docs

    platform_root = platform_docs.root
    if not platform_root:
        errors.append("docs_contract.platform_docs.root is required")
    elif not (repo_root / platform_root).is_dir():
        errors.append(f"missing docs_contract.platform_docs.root directory: {platform_root}")

    if platform_docs.seed_mode != "create_if_missing":
        errors.append("docs_contract.platform_docs.seed_mode must be create_if_missing")

    if platform_docs.bootstrap_command != "make blueprint-bootstrap":
        errors.append("docs_contract.platform_docs.bootstrap_command must be make blueprint-bootstrap")
    elif "blueprint-bootstrap" not in helpers.make_targets(repo_root):
        errors.append("docs_contract.platform_docs.bootstrap_command references missing make target: blueprint-bootstrap")

    template_root = platform_docs.template_root
    if not template_root:
        errors.append("docs_contract.platform_docs.template_root is required")
    elif not (repo_root / template_root).is_dir():
        errors.append(f"missing docs_contract.platform_docs.template_root directory: {template_root}")

    required_seed_files = platform_docs.required_seed_files
    if not required_seed_files:
        errors.append("docs_contract.platform_docs.required_seed_files must define at least one file")
        return errors

    for relative_path in required_seed_files:
        target_path = repo_root / relative_path
        if not target_path.is_file():
            errors.append(f"missing platform docs seed file: {relative_path}")
            continue
        if not target_path.read_text(encoding="utf-8").strip():
            errors.append(f"platform docs seed file is empty: {relative_path}")

        if platform_root and not relative_path.startswith(f"{platform_root}/"):
            errors.append("platform docs seed file must be under configured root " f"{platform_root}: {relative_path}")
            continue

        if not template_root or not platform_root:
            continue
        suffix = relative_path.removeprefix(f"{platform_root}/")
        template_path = repo_root / template_root / suffix
        if not template_path.is_file():
            errors.append(
                "missing platform docs seed template file for "
                f"{relative_path}: {(Path(template_root) / suffix).as_posix()}"
            )
            continue
        template_lines = template_path.read_text(encoding="utf-8").splitlines()
        first_nonempty = next((line.strip() for line in template_lines if line.strip()), "")
        if not first_nonempty.startswith("# "):
            errors.append(
                "platform docs seed template must start with a markdown heading: "
                f"{(Path(template_root) / suffix).as_posix()}"
            )

    return errors


def validate_bootstrap_template_sync(repo_root: Path, contract: BlueprintContract) -> list[str]:
    errors: list[str] = []
    repository = contract.repository
    consumer_owned_seed_paths = set(repository.consumer_seeded_paths)
    init_managed_paths = set(repository.init_managed_paths)

    template_sync_contract = (
        (
            repo_root / "scripts/templates/blueprint/bootstrap",
            (
                "Makefile",
                ".editorconfig",
                ".gitignore",
                ".dockerignore",
                ".pre-commit-config.yaml",
                "blueprint/contract.yaml",
                "blueprint/repo.init.env",
                "blueprint/repo.init.secrets.example.env",
                "docs/docusaurus.config.js",
                "docs/README.md",
                "docs/blueprint/README.md",
                "docs/blueprint/architecture/system_overview.md",
                "docs/blueprint/architecture/execution_model.md",
                "docs/blueprint/governance/ownership_matrix.md",
            ),
        ),
        (
            repo_root / "scripts/templates/infra/bootstrap",
            (
                "tests/infra/modules/observability/README.md",
                "infra/local/crossplane/kustomization.yaml",
                "infra/local/crossplane/namespace.yaml",
                "infra/local/helm/core/argocd.values.yaml",
                "infra/local/helm/core/external-secrets.values.yaml",
                "infra/local/helm/core/cert-manager.values.yaml",
                "infra/local/helm/core/crossplane.values.yaml",
                "infra/local/helm/observability/grafana.values.yaml",
                "infra/local/helm/observability/otel-collector.values.yaml",
                "infra/gitops/argocd/base/kustomization.yaml",
                "infra/gitops/argocd/base/namespace.yaml",
                "infra/gitops/argocd/environments/dev/kustomization.yaml",
                "infra/gitops/argocd/environments/dev/platform-config.yaml",
                "infra/gitops/argocd/overlays/local/kustomization.yaml",
                "infra/gitops/argocd/overlays/local/keycloak.yaml",
                "infra/gitops/platform/base/kustomization.yaml",
                "infra/gitops/platform/base/namespaces.yaml",
                "infra/gitops/platform/base/security/kustomization.yaml",
                "infra/gitops/platform/base/security/runtime-source-store.yaml",
                "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
                "infra/gitops/platform/environments/local/kustomization.yaml",
                "infra/gitops/platform/environments/local/runtime-contract-configmap.yaml",
                "infra/gitops/platform/environments/dev/kustomization.yaml",
                "infra/gitops/platform/environments/dev/runtime-contract-configmap.yaml",
            ),
        ),
    )

    for template_root, synced_files in template_sync_contract:
        for rel_path in synced_files:
            if repository.repo_mode == repository.consumer_init.mode_to and (
                rel_path in consumer_owned_seed_paths or rel_path in init_managed_paths
            ):
                continue
            target_path = repo_root / rel_path
            template_path = template_root / rel_path
            template_rel = template_path.relative_to(repo_root).as_posix()
            if not target_path.is_file():
                errors.append(f"missing bootstrap target file for template sync: {rel_path}")
                continue
            if not template_path.is_file():
                errors.append(f"missing bootstrap template file: {template_rel}")
                continue
            if target_path.read_text(encoding="utf-8") != template_path.read_text(encoding="utf-8"):
                errors.append("bootstrap template drift detected for " f"{rel_path}; sync with {template_rel}")
    return errors
