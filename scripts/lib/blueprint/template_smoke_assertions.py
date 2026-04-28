#!/usr/bin/env python3
"""Generated-repository conformance assertions for blueprint template smoke."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.blueprint.contract_schema import load_blueprint_contract  # noqa: E402


def _extract_kustomization_resources(text: str) -> list[str]:
    """Extract resource filenames from a kustomization.yaml resources section."""
    data = yaml.safe_load(text) or {}
    return [str(r) for r in data.get("resources", [])]


def _assert_descriptor_kustomization_agreement(
    app_manifest_names: list[str],
    descriptor: dict,
    descriptor_path: Path,
    kustomization_path: Path,
) -> None:
    """Assert every manifest filename declared in the descriptor is listed in kustomization.

    Handles convention-default paths for components without an explicit manifests: block.
    Convention default (matching _resolve_manifest_path in app_descriptor.py):
      deployment -> {component_id}-deployment.yaml
      service    -> {component_id}-service.yaml

    Raises AssertionError per missing filename with a message naming the filename and both
    file paths (FR-001, NFR-OBS-001).
    """
    names_set = set(app_manifest_names)
    for app in (descriptor.get("apps") or []):
        for component in (app.get("components") or []):
            component_id = component.get("id", "")
            manifests = component.get("manifests") or {}

            # Resolve deployment filename
            dep_val = manifests.get("deployment")
            if dep_val:
                deployment_filename = Path(dep_val).name
            else:
                deployment_filename = f"{component_id}-deployment.yaml"

            # Resolve service filename
            svc_val = manifests.get("service")
            if svc_val:
                service_filename = Path(svc_val).name
            else:
                service_filename = f"{component_id}-service.yaml"

            for filename in (deployment_filename, service_filename):
                if filename not in names_set:
                    raise AssertionError(
                        f"apps/descriptor.yaml: component '{component_id}' manifest '{filename}' "
                        f"is not listed in kustomization.yaml. "
                        f"Descriptor: {descriptor_path}. Kustomization: {kustomization_path}."
                    )


def normalize_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def profile_environment(profile: str) -> tuple[str, str]:
    if profile.startswith("local-"):
        return "local", "local"
    if profile.startswith("stackit-"):
        return "stackit", profile.split("-", 1)[1]
    raise AssertionError(f"unsupported BLUEPRINT_PROFILE={profile}")


def assert_path_exists(repo_root: Path, relative_path: str, scenario: str) -> None:
    path = repo_root / relative_path
    if not path.exists():
        raise AssertionError(f"{scenario}: expected path to exist: {relative_path}")


def assert_make_target_presence(makefile_text: str, target: str, expected: bool, scenario: str) -> None:
    pattern = re.compile(rf"^{re.escape(target)}:", re.MULTILINE)
    present = bool(pattern.search(makefile_text))
    if present != expected:
        state = "present" if expected else "absent"
        raise AssertionError(f"{scenario}: expected target to be {state}: {target}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: template_smoke_assertions.py <repo_root>", file=sys.stderr)
        return 2

    repo_root = Path(sys.argv[1]).resolve()
    scenario = os.environ.get("BLUEPRINT_TEMPLATE_SMOKE_SCENARIO", "default")
    profile = os.environ["BLUEPRINT_PROFILE"]
    expected_stack, expected_environment = profile_environment(profile)
    observability_enabled = normalize_bool(os.environ.get("OBSERVABILITY_ENABLED", "false"))
    app_catalog_scaffold_enabled = normalize_bool(os.environ.get("APP_CATALOG_SCAFFOLD_ENABLED", "false"))
    app_runtime_gitops_enabled = normalize_bool(os.environ.get("APP_RUNTIME_GITOPS_ENABLED", "true"))
    app_runtime_min_workloads_raw = os.environ.get("APP_RUNTIME_MIN_WORKLOADS", "1")
    if not app_runtime_min_workloads_raw.isdigit():
        raise AssertionError(
            f"{scenario}: APP_RUNTIME_MIN_WORKLOADS must be a non-negative integer, got {app_runtime_min_workloads_raw!r}"
        )
    app_runtime_min_workloads = int(app_runtime_min_workloads_raw)

    contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
    if contract.repository.repo_mode != "generated-consumer":
        raise AssertionError(
            f"{scenario}: expected repo_mode=generated-consumer after blueprint-init-repo, "
            f"got {contract.repository.repo_mode}"
        )

    makefile_path = repo_root / contract.make_contract.ownership.blueprint_generated_file
    makefile_text = makefile_path.read_text(encoding="utf-8")

    expected_modules: list[str] = []
    for module_name, module in sorted(contract.optional_modules.modules.items()):
        enabled = normalize_bool(os.environ.get(module.enable_flag, "false"))
        if enabled:
            expected_modules.append(module_name)

        for target in module.make_targets:
            assert_make_target_presence(makefile_text, target, enabled, scenario)

        for path_key in module.paths_required_when_enabled:
            raw_path = module.paths[path_key].replace("${ENV}", expected_environment)
            relative_path = raw_path.rstrip("/")
            path = repo_root / relative_path
            if enabled:
                assert_path_exists(repo_root, relative_path, scenario)
            elif path.exists():
                raise AssertionError(
                    f"{scenario}: expected disabled conditional scaffold to stay pruned in generated repo: {relative_path}"
                )

    required_artifacts = [
        "artifacts/infra/provision.env",
        "artifacts/infra/deploy.env",
        "artifacts/infra/smoke.env",
        "artifacts/infra/smoke_result.json",
        "artifacts/infra/smoke_diagnostics.json",
        "artifacts/infra/infra_status_snapshot.json",
        "artifacts/apps/apps_bootstrap.env",
        "artifacts/apps/apps_smoke.env",
    ]
    for artifact in required_artifacts:
        assert_path_exists(repo_root, artifact, scenario)

    if expected_stack == "local":
        assert_path_exists(repo_root, "artifacts/infra/local_crossplane_bootstrap.env", scenario)
    else:
        for artifact in (
            "artifacts/infra/stackit_bootstrap_apply.env",
            "artifacts/infra/stackit_foundation_apply.env",
            "artifacts/infra/stackit_foundation_kubeconfig.env",
            "artifacts/infra/stackit_runtime_prerequisites.env",
            "artifacts/infra/stackit_foundation_runtime_secret.env",
        ):
            assert_path_exists(repo_root, artifact, scenario)

    manifest_path = repo_root / "apps/catalog/manifest.yaml"
    versions_lock_path = repo_root / "apps/catalog/versions.lock"
    if app_catalog_scaffold_enabled:
        assert_path_exists(repo_root, "apps/catalog/manifest.yaml", scenario)
        assert_path_exists(repo_root, "apps/catalog/versions.lock", scenario)
        manifest_text = manifest_path.read_text(encoding="utf-8")
        expected_manifest_line = "enabled: true" if observability_enabled else "enabled: false"
        if expected_manifest_line not in manifest_text:
            raise AssertionError(
                f"{scenario}: apps/catalog/manifest.yaml drifted from OBSERVABILITY_ENABLED={observability_enabled}"
            )
        if observability_enabled and "endpoint: http" not in manifest_text:
            raise AssertionError(f"{scenario}: observability-enabled app manifest is missing OTEL endpoint wiring")
    else:
        if manifest_path.exists() or versions_lock_path.exists():
            raise AssertionError(
                f"{scenario}: app catalog scaffold disabled but apps/catalog manifest/lock still exist"
            )

    platform_base_kustomization = (repo_root / "infra/gitops/platform/base/kustomization.yaml").read_text(encoding="utf-8")
    apps_resource_present = "\n  - apps\n" in f"\n{platform_base_kustomization}\n"
    if app_runtime_gitops_enabled:
        if not apps_resource_present:
            raise AssertionError(
                f"{scenario}: APP_RUNTIME_GITOPS_ENABLED=true but infra/gitops/platform/base/kustomization.yaml does not include apps resource"
            )

        apps_kust_rel = "infra/gitops/platform/base/apps/kustomization.yaml"
        apps_kustomization = repo_root / apps_kust_rel
        if not apps_kustomization.is_file():
            raise AssertionError(f"{scenario}: missing app runtime kustomization scaffold")

        kust_text = apps_kustomization.read_text(encoding="utf-8")
        app_manifest_names = _extract_kustomization_resources(kust_text)
        if not app_manifest_names:
            raise AssertionError(
                f"{scenario}: {apps_kust_rel} declares no resources; "
                "add at least one Deployment and one Service manifest"
            )

        # Issue #217: cross-check descriptor manifest filenames against kustomization resources
        descriptor_path = repo_root / "apps" / "descriptor.yaml"
        if descriptor_path.is_file():
            descriptor = yaml.safe_load(descriptor_path.read_text(encoding="utf-8")) or {}
            _assert_descriptor_kustomization_agreement(
                app_manifest_names=app_manifest_names,
                descriptor=descriptor,
                descriptor_path=descriptor_path,
                kustomization_path=apps_kustomization,
            )

        app_manifest_paths = [f"infra/gitops/platform/base/apps/{name}" for name in app_manifest_names]

        for relative_path in app_manifest_paths:
            assert_path_exists(repo_root, relative_path, scenario)

        kinds: list[str] = []
        for relative_path in app_manifest_paths:
            content = (repo_root / relative_path).read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("kind:"):
                    kinds.append(line.split(":", 1)[1].strip())
        if "Deployment" not in kinds or "Service" not in kinds:
            raise AssertionError(
                f"{scenario}: app runtime scaffold missing expected workload kinds Deployment/Service"
            )

    smoke_result = json.loads((repo_root / "artifacts/infra/smoke_result.json").read_text(encoding="utf-8"))
    if smoke_result.get("status") != "success":
        raise AssertionError(f"{scenario}: smoke result status is not success")
    if smoke_result.get("profile") != profile:
        raise AssertionError(f"{scenario}: smoke result profile drifted from BLUEPRINT_PROFILE")
    if smoke_result.get("stack") != expected_stack:
        raise AssertionError(f"{scenario}: smoke result stack drifted from BLUEPRINT_PROFILE")
    if smoke_result.get("environment") != expected_environment:
        raise AssertionError(f"{scenario}: smoke result environment drifted from BLUEPRINT_PROFILE")
    if bool(smoke_result.get("observabilityEnabled")) != observability_enabled:
        raise AssertionError(f"{scenario}: smoke result observability flag drifted from input")
    if sorted(smoke_result.get("enabledModules", [])) != expected_modules:
        raise AssertionError(f"{scenario}: smoke result enabledModules drifted from input flags")

    smoke_diagnostics = json.loads((repo_root / "artifacts/infra/smoke_diagnostics.json").read_text(encoding="utf-8"))
    for artifact_name in ("provision", "deploy", "coreRuntimeSmoke", "appsSmoke"):
        if not smoke_diagnostics.get("artifacts", {}).get(artifact_name):
            raise AssertionError(f"{scenario}: smoke diagnostics missing artifact flag {artifact_name}=true")
    app_runtime_diagnostics = smoke_diagnostics.get("appRuntime", {})
    if bool(app_runtime_diagnostics.get("gitopsEnabled")) != app_runtime_gitops_enabled:
        raise AssertionError(f"{scenario}: smoke diagnostics appRuntime.gitopsEnabled drifted from input")
    expected_minimum_runtime_workloads = app_runtime_min_workloads if app_runtime_gitops_enabled else 0
    if int(app_runtime_diagnostics.get("minimumExpectedWorkloads", -1)) != expected_minimum_runtime_workloads:
        raise AssertionError(
            f"{scenario}: smoke diagnostics appRuntime.minimumExpectedWorkloads drifted from contract default"
        )
    workload_health = smoke_diagnostics.get("workloadHealth", {})
    for field_name in ("requiredNamespaceMinimumPods", "emptyRuntimeNamespaceCount", "emptyRuntimeNamespaces"):
        if field_name not in workload_health:
            raise AssertionError(f"{scenario}: smoke diagnostics workloadHealth missing field {field_name}")

    status_snapshot = json.loads((repo_root / "artifacts/infra/infra_status_snapshot.json").read_text(encoding="utf-8"))
    if status_snapshot.get("profile") != profile:
        raise AssertionError(f"{scenario}: infra status snapshot profile drifted from BLUEPRINT_PROFILE")
    if status_snapshot.get("environment") != expected_environment:
        raise AssertionError(f"{scenario}: infra status snapshot environment drifted from BLUEPRINT_PROFILE")
    if bool(status_snapshot.get("observabilityEnabled")) != observability_enabled:
        raise AssertionError(f"{scenario}: infra status snapshot observability flag drifted from input")
    if sorted(status_snapshot.get("enabledModules", [])) != expected_modules:
        raise AssertionError(f"{scenario}: infra status snapshot enabledModules drifted from input flags")
    if status_snapshot.get("latestSmoke", {}).get("status") != "success":
        raise AssertionError(f"{scenario}: infra status snapshot latestSmoke.status is not success")

    status_artifacts = status_snapshot.get("artifacts", {})
    for artifact_name in ("provision", "deploy", "smoke"):
        if not status_artifacts.get(artifact_name):
            raise AssertionError(f"{scenario}: infra status snapshot missing artifact flag {artifact_name}=true")
    if expected_stack == "stackit":
        for artifact_name in ("stackitBootstrapApply", "stackitFoundationApply"):
            if not status_artifacts.get(artifact_name):
                raise AssertionError(f"{scenario}: expected STACKIT artifact flag {artifact_name}=true")
    else:
        for artifact_name in ("stackitBootstrapApply", "stackitFoundationApply"):
            if status_artifacts.get(artifact_name):
                raise AssertionError(f"{scenario}: local profile should not report {artifact_name}=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
