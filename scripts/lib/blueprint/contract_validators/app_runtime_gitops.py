from __future__ import annotations

from pathlib import Path

from scripts.lib.blueprint.contract_schema import BlueprintContract
from scripts.lib.blueprint.contract_validators.shared import ContractValidationHelpers


def validate_app_runtime_gitops_contract(
    repo_root: Path,
    contract: BlueprintContract,
    helpers: ContractValidationHelpers,
) -> list[str]:
    errors: list[str] = []
    spec_raw = helpers.mapping_or_error(contract.raw.get("spec"), "spec", errors)
    raw_contract_section = spec_raw.get("app_runtime_gitops_contract")
    if raw_contract_section is None:
        errors.append("spec.app_runtime_gitops_contract is required")
        return errors
    contract_section = helpers.mapping_or_error(
        raw_contract_section,
        "spec.app_runtime_gitops_contract",
        errors,
    )

    enabled_by_default = helpers.bool_or_error(
        contract_section.get("enabled_by_default"),
        "spec.app_runtime_gitops_contract.enabled_by_default",
        errors,
    )
    if enabled_by_default is not True:
        errors.append("spec.app_runtime_gitops_contract.enabled_by_default must be true")

    enable_flag = helpers.string_or_error(
        contract_section.get("enable_flag"),
        "spec.app_runtime_gitops_contract.enable_flag",
        errors,
    )
    toggles_raw = spec_raw.get("toggles")
    if isinstance(toggles_raw, dict) and enable_flag and enable_flag not in toggles_raw:
        errors.append(
            "spec.app_runtime_gitops_contract.enable_flag must reference an existing toggle: "
            f"{enable_flag}"
        )

    required_paths = helpers.list_of_str_or_error(
        contract_section.get("required_paths_when_enabled"),
        "spec.app_runtime_gitops_contract.required_paths_when_enabled",
        errors,
    )
    if not required_paths:
        errors.append("spec.app_runtime_gitops_contract.required_paths_when_enabled must not be empty")

    workload_kinds = helpers.list_of_str_or_error(
        contract_section.get("workload_kinds_required_when_enabled"),
        "spec.app_runtime_gitops_contract.workload_kinds_required_when_enabled",
        errors,
    )
    if not workload_kinds:
        errors.append("spec.app_runtime_gitops_contract.workload_kinds_required_when_enabled must not be empty")

    docs_paths = helpers.list_of_str_or_error(
        contract_section.get("docs_paths"),
        "spec.app_runtime_gitops_contract.docs_paths",
        errors,
    )
    for docs_path in docs_paths:
        if not (repo_root / docs_path).is_file():
            errors.append(f"missing app runtime GitOps docs path: {docs_path}")

    app_catalog_manifest_path = helpers.string_or_error(
        contract_section.get("app_catalog_manifest_path"),
        "spec.app_runtime_gitops_contract.app_catalog_manifest_path",
        errors,
    )
    smoke_guardrails = helpers.mapping_or_error(
        contract_section.get("smoke_guardrails"),
        "spec.app_runtime_gitops_contract.smoke_guardrails",
        errors,
    )
    app_namespace = helpers.string_or_error(
        smoke_guardrails.get("app_namespace"),
        "spec.app_runtime_gitops_contract.smoke_guardrails.app_namespace",
        errors,
    )
    live_workload_kinds = helpers.list_of_str_or_error(
        smoke_guardrails.get("workload_kinds"),
        "spec.app_runtime_gitops_contract.smoke_guardrails.workload_kinds",
        errors,
    )
    if not live_workload_kinds:
        errors.append("spec.app_runtime_gitops_contract.smoke_guardrails.workload_kinds must not be empty")
    minimum_workloads_env = helpers.string_or_error(
        smoke_guardrails.get("minimum_workloads_env"),
        "spec.app_runtime_gitops_contract.smoke_guardrails.minimum_workloads_env",
        errors,
    )
    minimum_workloads_default = helpers.int_or_error(
        smoke_guardrails.get("minimum_workloads_default"),
        "spec.app_runtime_gitops_contract.smoke_guardrails.minimum_workloads_default",
        errors,
    )
    if minimum_workloads_default is not None and minimum_workloads_default < 1:
        errors.append(
            "spec.app_runtime_gitops_contract.smoke_guardrails.minimum_workloads_default must be >= 1"
        )
    diagnostics_reason = helpers.string_or_error(
        smoke_guardrails.get("diagnostics_reason"),
        "spec.app_runtime_gitops_contract.smoke_guardrails.diagnostics_reason",
        errors,
    )
    if diagnostics_reason != "empty-runtime-workloads":
        errors.append(
            "spec.app_runtime_gitops_contract.smoke_guardrails.diagnostics_reason must be empty-runtime-workloads"
        )
    if isinstance(toggles_raw, dict) and minimum_workloads_env and minimum_workloads_env not in toggles_raw:
        errors.append(
            "spec.app_runtime_gitops_contract.smoke_guardrails.minimum_workloads_env must reference an existing "
            f"toggle: {minimum_workloads_env}"
        )
    if (
        isinstance(toggles_raw, dict)
        and minimum_workloads_env
        and minimum_workloads_default is not None
        and isinstance(toggles_raw.get(minimum_workloads_env), dict)
    ):
        toggle_default = toggles_raw.get(minimum_workloads_env, {}).get("default")
        if toggle_default != minimum_workloads_default:
            errors.append(
                "spec.app_runtime_gitops_contract.smoke_guardrails.minimum_workloads_default must match "
                f"spec.toggles.{minimum_workloads_env}.default"
            )

    if not helpers.is_optional_contract_enabled(spec_raw, contract_section):
        return errors

    errors.extend(helpers.validate_required_paths(repo_root, required_paths))

    base_kustomization_path = repo_root / "infra/gitops/platform/base/kustomization.yaml"
    base_resources = helpers.kustomization_resources(base_kustomization_path)
    if "apps" not in base_resources:
        errors.append(
            "infra/gitops/platform/base/kustomization.yaml missing required app runtime resource: apps "
            "(set APP_RUNTIME_GITOPS_ENABLED=true and reconcile scaffold)"
        )

    app_runtime_manifest_root = repo_root / "infra/gitops/platform/base/apps"
    manifest_kinds = helpers.manifest_kinds_under_path(app_runtime_manifest_root)
    if not manifest_kinds:
        errors.append(
            "app runtime GitOps scaffold enabled but no Kubernetes manifests were detected under "
            "infra/gitops/platform/base/apps"
        )
    else:
        for required_kind in workload_kinds:
            if required_kind not in manifest_kinds:
                errors.append(
                    "app runtime GitOps scaffold enabled but required workload kind is missing under "
                    f"infra/gitops/platform/base/apps: {required_kind}"
                )

    app_catalog_section_raw = spec_raw.get("app_catalog_scaffold_contract")
    app_catalog_enabled = False
    if isinstance(app_catalog_section_raw, dict):
        app_catalog_enabled = helpers.is_optional_contract_enabled(spec_raw, app_catalog_section_raw)
    if app_catalog_enabled:
        manifest_path = repo_root / app_catalog_manifest_path
        if not manifest_path.is_file():
            errors.append(f"missing app runtime GitOps manifest contract path: {app_catalog_manifest_path}")
        else:
            manifest_content = manifest_path.read_text(encoding="utf-8")
            for marker in (
                "deliveryTopology:",
                "runtimeDeliveryContract:",
                "gitopsWorkloads:",
                "manifestsRoot: infra/gitops/platform/base/apps",
                "gitopsEnabled: true",
            ):
                if marker not in manifest_content:
                    errors.append(
                        "apps/catalog/manifest.yaml missing runtime delivery contract marker while "
                        "APP_RUNTIME_GITOPS_ENABLED=true and APP_CATALOG_SCAFFOLD_ENABLED=true: "
                        f"{marker}"
                    )

    apps_smoke_script = repo_root / "scripts/bin/platform/apps/smoke.sh"
    if apps_smoke_script.is_file():
        apps_smoke_content = apps_smoke_script.read_text(encoding="utf-8")
        for marker in ("APP_RUNTIME_MIN_WORKLOADS", "run_runtime_workload_presence_check"):
            if marker not in apps_smoke_content:
                errors.append(
                    "scripts/bin/platform/apps/smoke.sh must enforce app runtime live workload presence guardrails: "
                    f"missing marker {marker}"
                )

    infra_smoke_script = repo_root / "scripts/bin/infra/smoke.sh"
    if infra_smoke_script.is_file():
        infra_smoke_content = infra_smoke_script.read_text(encoding="utf-8")
        for marker in ("APP_RUNTIME_MIN_WORKLOADS", "--required-namespace-min-pods"):
            if marker not in infra_smoke_content:
                errors.append(
                    "scripts/bin/infra/smoke.sh must propagate runtime empty-workload diagnostics and guardrails: "
                    f"missing marker {marker}"
                )
        diagnostics_helper_path = repo_root / "scripts/lib/infra/smoke_artifacts.py"
        diagnostics_helper_content = (
            diagnostics_helper_path.read_text(encoding="utf-8")
            if diagnostics_helper_path.is_file()
            else ""
        )
        for marker in ("emptyRuntimeNamespaceCount", "emptyRuntimeNamespaces"):
            marker_in_scripts = marker in infra_smoke_content or marker in diagnostics_helper_content
            if marker_in_scripts:
                continue
            errors.append(
                "runtime smoke diagnostics contract missing marker "
                f"{marker} across scripts/bin/infra/smoke.sh and scripts/lib/infra/smoke_artifacts.py"
            )
        if app_namespace and app_namespace not in infra_smoke_content:
            errors.append(
                "scripts/bin/infra/smoke.sh must include app runtime smoke namespace from contract "
                f"spec.app_runtime_gitops_contract.smoke_guardrails.app_namespace={app_namespace}"
            )

    return errors
