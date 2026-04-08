from __future__ import annotations

from pathlib import Path

from scripts.lib.blueprint.contract_validators.shared import ContractValidationHelpers


def validate_runtime_credentials_contract(repo_root: Path, helpers: ContractValidationHelpers) -> list[str]:
    errors: list[str] = []

    required_security_files = (
        "blueprint/runtime_identity_contract.yaml",
        "docs/platform/consumer/runtime_credentials_eso.md",
        "infra/gitops/platform/base/extensions/kustomization.yaml",
        "infra/gitops/platform/base/security/kustomization.yaml",
        "infra/gitops/platform/base/security/runtime-source-store.yaml",
        "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
        "infra/gitops/argocd/core/local/keycloak.yaml",
        "infra/gitops/argocd/core/dev/keycloak.yaml",
        "infra/gitops/argocd/core/stage/keycloak.yaml",
        "infra/gitops/argocd/core/prod/keycloak.yaml",
        "infra/gitops/argocd/overlays/local/keycloak.yaml",
        "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
        "scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh",
        "scripts/bin/platform/auth/reconcile_runtime_identity.sh",
        "scripts/lib/infra/state_artifact_contract.py",
        "scripts/lib/infra/schemas/state_artifact.schema.json",
        "scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md",
        "scripts/templates/infra/bootstrap/infra/gitops/argocd/core/keycloak.application.yaml.tmpl",
        "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/keycloak.yaml",
        "scripts/templates/blueprint/bootstrap/blueprint/runtime_identity_contract.yaml",
        "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
    )
    errors.extend(helpers.validate_required_files(repo_root, list(required_security_files)))

    runtime_identity_contract_path = repo_root / "blueprint/runtime_identity_contract.yaml"
    if runtime_identity_contract_path.is_file():
        try:
            runtime_identity_contract = helpers.load_runtime_identity_contract(runtime_identity_contract_path)
            rendered_eso_manifest = helpers.render_eso_external_secrets_manifest(runtime_identity_contract)
        except Exception as exc:  # pragma: no cover - defensive guard for contract parsing
            errors.append(f"invalid runtime identity contract: {exc}")
            rendered_eso_manifest = ""
            runtime_identity_contract = None

        if rendered_eso_manifest and runtime_identity_contract is not None:
            runtime_default_names = {item.name for item in runtime_identity_contract.runtime_env_defaults}
            for required_default in ("ARGOCD_REPO_USERNAME", "ARGOCD_REPO_CREDENTIALS_REQUIRED"):
                if required_default not in runtime_default_names:
                    errors.append(
                        "blueprint/runtime_identity_contract.yaml missing required runtime env default: "
                        f"{required_default}"
                    )

            argocd_repo_contract = next(
                (item for item in runtime_identity_contract.eso_contracts if item.contract_id == "argocd-gitops-repo"),
                None,
            )
            if argocd_repo_contract is None:
                errors.append("blueprint/runtime_identity_contract.yaml missing ESO contract id=argocd-gitops-repo")
            else:
                if argocd_repo_contract.namespace != "argocd":
                    errors.append("argocd-gitops-repo ESO contract must target namespace=argocd")
                if argocd_repo_contract.external_secret_name != "argocd-gitops-repo":
                    errors.append(
                        "argocd-gitops-repo ESO contract must use external_secret_name=argocd-gitops-repo"
                    )
                if argocd_repo_contract.target_secret_name != "argocd-gitops-repo":
                    errors.append("argocd-gitops-repo ESO contract must use target_secret_name=argocd-gitops-repo")
                expected_repo_keys = {"type", "url", "username", "password"}
                actual_repo_keys = {item.secret_key for item in argocd_repo_contract.data_mappings}
                missing_repo_keys = sorted(expected_repo_keys - actual_repo_keys)
                if missing_repo_keys:
                    errors.append(
                        "argocd-gitops-repo ESO contract missing required target secret keys: "
                        + ", ".join(missing_repo_keys)
                    )
                secret_type_label = argocd_repo_contract.target_template_labels.get(
                    "argocd.argoproj.io/secret-type",
                    "",
                )
                if secret_type_label != "repository":
                    errors.append(
                        "argocd-gitops-repo ESO contract must set target_template_labels."
                        "argocd.argoproj.io/secret-type=repository"
                    )

            errors.extend(helpers.validate_argocd_https_repo_url_contract(repo_root))

            for relative_path in (
                "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
                "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
            ):
                manifest_path = repo_root / relative_path
                if not manifest_path.is_file():
                    continue
                if manifest_path.read_text(encoding="utf-8") != rendered_eso_manifest:
                    errors.append(
                        f"{relative_path} is out of sync with blueprint/runtime_identity_contract.yaml; "
                        "run runtime_identity_contract.py render-eso-manifest"
                    )

    base_kustomization = repo_root / "infra/gitops/platform/base/kustomization.yaml"
    base_resources = helpers.kustomization_resources(base_kustomization)
    required_base_resources = {"security", "extensions"}
    missing_base_resources = sorted(required_base_resources - base_resources)
    if missing_base_resources:
        errors.append(
            "infra/gitops/platform/base/kustomization.yaml missing required runtime credentials resources: "
            + ", ".join(missing_base_resources)
        )

    security_kustomization = repo_root / "infra/gitops/platform/base/security/kustomization.yaml"
    security_resources = helpers.kustomization_resources(security_kustomization)
    required_security_resources = {"runtime-source-store.yaml", "runtime-external-secrets-core.yaml"}
    missing_security_resources = sorted(required_security_resources - security_resources)
    if missing_security_resources:
        errors.append(
            "infra/gitops/platform/base/security/kustomization.yaml missing required resources: "
            + ", ".join(missing_security_resources)
        )

    extensions_kustomization = repo_root / "infra/gitops/platform/base/extensions/kustomization.yaml"
    if extensions_kustomization.is_file():
        extensions_content = extensions_kustomization.read_text(encoding="utf-8")
        if "resources:" not in extensions_content:
            errors.append(
                "infra/gitops/platform/base/extensions/kustomization.yaml must define resources for drift-safe extensions"
            )

    required_keycloak_resources = {
        "local": "keycloak.yaml",
        "dev": "../../core/dev/keycloak.yaml",
        "stage": "../../core/stage/keycloak.yaml",
        "prod": "../../core/prod/keycloak.yaml",
    }
    for env_name, resource_path in required_keycloak_resources.items():
        overlay_path = repo_root / f"infra/gitops/argocd/overlays/{env_name}/kustomization.yaml"
        overlay_resources = helpers.kustomization_resources(overlay_path)
        if resource_path not in overlay_resources:
            errors.append(
                f"infra/gitops/argocd/overlays/{env_name}/kustomization.yaml missing mandatory keycloak resource: "
                f"{resource_path}"
            )

    keycloak_sync_policy_contract = {
        "infra/gitops/argocd/core/local/keycloak.yaml": False,
        "infra/gitops/argocd/overlays/local/keycloak.yaml": False,
        "infra/gitops/argocd/core/dev/keycloak.yaml": True,
        "infra/gitops/argocd/core/stage/keycloak.yaml": True,
        "infra/gitops/argocd/core/prod/keycloak.yaml": True,
    }
    for relative_path, expected_automated in keycloak_sync_policy_contract.items():
        manifest_path = repo_root / relative_path
        if not manifest_path.is_file():
            continue
        has_automated = helpers.manifest_sync_policy_has_automated(manifest_path.read_text(encoding="utf-8"))
        if has_automated == expected_automated:
            continue
        if expected_automated:
            errors.append(
                f"{relative_path} must keep syncPolicy.automated enabled for managed profile convergence"
            )
        else:
            errors.append(
                f"{relative_path} must keep syncPolicy manual (syncPolicy.automated absent) "
                "until runtime credentials are reconciled"
            )

    external_secrets_api_contract_paths = (
        "infra/gitops/platform/base/security/runtime-source-store.yaml",
        "infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
        "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-source-store.yaml",
        "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml",
    )
    for relative_path in external_secrets_api_contract_paths:
        manifest_path = repo_root / relative_path
        if not manifest_path.is_file():
            continue
        content = manifest_path.read_text(encoding="utf-8")
        if "external-secrets.io/v1beta1" in content:
            errors.append(f"{relative_path} uses deprecated External Secrets apiVersion external-secrets.io/v1beta1")
        if "external-secrets.io/v1" not in content:
            errors.append(f"{relative_path} must target External Secrets apiVersion external-secrets.io/v1")

    runtime_identity_renderer = repo_root / "scripts/lib/infra/runtime_identity_contract.py"
    if runtime_identity_renderer.is_file():
        renderer_content = runtime_identity_renderer.read_text(encoding="utf-8")
        if 'EXTERNAL_SECRETS_API_VERSION = "external-secrets.io/v1"' not in renderer_content:
            errors.append(
                "scripts/lib/infra/runtime_identity_contract.py must define EXTERNAL_SECRETS_API_VERSION="
                '"external-secrets.io/v1"'
            )
        if "external-secrets.io/v1beta1" in renderer_content:
            errors.append(
                "scripts/lib/infra/runtime_identity_contract.py must not render deprecated "
                "External Secrets apiVersion external-secrets.io/v1beta1"
            )

    for consumer_path, dependency_path in helpers.runtime_dependency_edges:
        consumer_file = repo_root / consumer_path
        if not consumer_file.is_file():
            continue
        consumer_content = consumer_file.read_text(encoding="utf-8", errors="surrogateescape")
        if dependency_path not in consumer_content:
            continue
        if not (repo_root / dependency_path).is_file():
            errors.append(
                f"{consumer_path} references {dependency_path} but dependency file is missing; "
                "reconcile runtime identity artifacts before infra-smoke/upgrade validation"
            )

    return errors
