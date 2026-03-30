from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from scripts.lib.blueprint.contract_schema import load_module_contract


REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_MANAGED_RESTORE_TEMPLATE_PATHS = (
    "scripts/templates/blueprint/bootstrap/blueprint/contract.yaml",
    "scripts/templates/blueprint/bootstrap/docs/docusaurus.config.js",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/root/applicationset-platform-environments.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/environments/dev/platform-application.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/environments/stage/platform-application.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/environments/prod/platform-application.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/appproject.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/application-platform-local.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/dev/appproject.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/dev/applicationset-platform-environments.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/stage/appproject.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/stage/applicationset-platform-environments.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/prod/appproject.yaml",
    "scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/prod/applicationset-platform-environments.yaml",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/env/stage.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/env/prod.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/env/dev.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/env/stage.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/env/prod.tfvars",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/state-backend/stage.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/bootstrap/state-backend/prod.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/state-backend/stage.hcl",
    "scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/state-backend/prod.hcl",
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _copy_repo_text_path(tmp_root: Path, rel_path: str) -> None:
    target_path = tmp_root / rel_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(_read(rel_path), encoding="utf-8")


def _line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_yaml_scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _extract_yaml_section(lines: list[str], marker: str) -> list[str]:
    marker_index = -1
    marker_indent = -1
    for idx, line in enumerate(lines):
        if line.strip() == f"{marker}:":
            marker_index = idx
            marker_indent = _line_indent(line)
            break

    if marker_index == -1:
        return []

    section: list[str] = []
    for line in lines[marker_index + 1 :]:
        if not line.strip():
            continue
        if _line_indent(line) <= marker_indent:
            break
        section.append(line)
    return section


def _extract_yaml_scalar(lines: list[str], key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$")
    for line in lines:
        match = pattern.match(line)
        if match:
            return _strip_yaml_scalar(match.group(1))
    return ""


def _extract_yaml_list(lines: list[str], marker: str) -> list[str]:
    section = _extract_yaml_section(lines, marker)
    values: list[str] = []
    for line in section:
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(_strip_yaml_scalar(stripped[2:]))
    return values


def _make_targets() -> set[str]:
    targets: set[str] = set()
    pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
    makefiles = [REPO_ROOT / "Makefile"]
    make_root = REPO_ROOT / "make"
    if make_root.is_dir():
        makefiles.extend(sorted(path for path in make_root.rglob("*.mk") if path.is_file()))
    for makefile in makefiles:
        for line in makefile.read_text(encoding="utf-8").splitlines():
            match = pattern.match(line)
            if not match:
                continue
            target = match.group(1)
            if target == ".PHONY":
                continue
            targets.add(target)
    return targets


class RefactorContractsTests(unittest.TestCase):
    def _contract_lines(self) -> list[str]:
        return _read("blueprint/contract.yaml").splitlines()

    def test_quality_hooks_require_shellcheck(self) -> None:
        hooks = _read("scripts/bin/quality/hooks_fast.sh")
        self.assertIn("require_command shellcheck", hooks)
        self.assertIn("--severity=error", hooks)
        self.assertNotIn("shellcheck not installed; skipping", hooks)

    def test_stackit_foundation_contract_tracks_rabbitmq_and_kms_provider_coverage(self) -> None:
        providers = _read("infra/cloud/stackit/terraform/foundation/providers.tf")
        foundation_main = _read("infra/cloud/stackit/terraform/foundation/main.tf")
        foundation_outputs = _read("infra/cloud/stackit/terraform/foundation/outputs.tf")
        foundation_locals = _read("infra/cloud/stackit/terraform/foundation/locals.tf")
        foundation_vars = _read("infra/cloud/stackit/terraform/foundation/variables.tf")
        stackit_layers = _read("scripts/lib/infra/stackit_layers.sh")

        self.assertIn("default_region = var.stackit_region", providers)
        self.assertIn('stackit_provider_supported = true', foundation_locals)
        self.assertIn('stackit_rabbitmq_instance', foundation_main)
        self.assertIn('stackit_rabbitmq_credential', foundation_main)
        self.assertIn('stackit_kms_keyring', foundation_main)
        self.assertIn('stackit_kms_key', foundation_main)
        self.assertIn('output "rabbitmq_uri"', foundation_outputs)
        self.assertIn('output "kms_key_ring_id"', foundation_outputs)
        self.assertIn('variable "postgres_instance_name"', foundation_vars)
        self.assertIn('variable "object_storage_bucket_name"', foundation_vars)
        self.assertIn('variable "secrets_manager_instance_name"', foundation_vars)
        self.assertIn('variable "postgres_version"', foundation_vars)
        self.assertIn('default     = "16"', foundation_vars)
        self.assertIn('postgres_instance_name', foundation_locals)
        self.assertIn('postgres_instance_name_override = try(trimspace(var.postgres_instance_name), "")', foundation_locals)
        self.assertIn('postgres_acl_effective', foundation_locals)
        self.assertIn('distinct(concat(', foundation_locals)
        self.assertIn('stackit_ske_cluster.foundation[0].egress_address_ranges', foundation_locals)
        self.assertIn('dns_zone_dns_names', foundation_locals)
        self.assertIn('trimsuffix(zone, ".")', foundation_locals)
        self.assertIn('object_storage_bucket_name', foundation_locals)
        self.assertIn('object_storage_bucket_name_override = try(trimspace(var.object_storage_bucket_name), "")', foundation_locals)
        self.assertIn('object_storage_credentials_group_name', foundation_locals)
        self.assertIn('secrets_manager_instance_name', foundation_locals)
        self.assertIn('secrets_manager_instance_name_override = try(trimspace(var.secrets_manager_instance_name), "")', foundation_locals)
        self.assertNotIn('coalesce(var.postgres_instance_name, "")', foundation_locals)
        self.assertNotIn('coalesce(var.object_storage_bucket_name, "")', foundation_locals)
        self.assertNotIn('coalesce(var.secrets_manager_instance_name, "")', foundation_locals)
        self.assertIn('name            = local.postgres_instance_name', foundation_main)
        self.assertIn('acl             = local.postgres_acl_effective', foundation_main)
        self.assertIn('enabled = var.dns_enabled && length(local.dns_zone_dns_names) > 0', foundation_main)
        self.assertIn('for_each = var.dns_enabled ? local.dns_zone_dns_names : {}', foundation_main)
        self.assertIn('name       = local.object_storage_bucket_name', foundation_main)
        self.assertIn('name       = local.object_storage_credentials_group_name', foundation_main)
        self.assertIn('name       = local.secrets_manager_instance_name', foundation_main)
        self.assertIn('source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"', stackit_layers)
        self.assertIn('"-var=postgres_instance_name=$POSTGRES_INSTANCE_NAME"', stackit_layers)
        self.assertIn('"-var=postgres_version=$POSTGRES_VERSION"', stackit_layers)
        self.assertIn('"-var=object_storage_bucket_name=$OBJECT_STORAGE_BUCKET_NAME"', stackit_layers)
        self.assertIn('stackit_emit_tf_string_list_arg_from_csv "dns_zone_fqdns" "$DNS_ZONE_FQDN"', stackit_layers)
        self.assertIn('"-var=secrets_manager_instance_name=$SECRETS_MANAGER_INSTANCE_NAME"', stackit_layers)

    def test_stackit_observability_defaults_omit_unsupported_medium_plan_retentions(self) -> None:
        foundation_vars = _read("infra/cloud/stackit/terraform/foundation/variables.tf")
        template_vars = _read("scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/variables.tf")

        self.assertIn('variable "observability_logs_retention_days"', foundation_vars)
        self.assertIn('default     = null', foundation_vars)
        self.assertIn('variable "observability_traces_retention_days"', foundation_vars)
        self.assertIn('default     = null', template_vars)

    def test_stackit_foundation_apply_retries_known_postgres_provider_race(self) -> None:
        foundation_apply = _read("scripts/bin/infra/stackit_foundation_apply.sh")

        self.assertIn('STACKIT_FOUNDATION_APPLY_MAX_ATTEMPTS', foundation_apply)
        self.assertIn('STACKIT_FOUNDATION_APPLY_RETRY_DELAY_SECONDS', foundation_apply)
        self.assertIn('stackit_foundation_apply_is_transient_postgres_notfound()', foundation_apply)
        self.assertIn('stackit_foundation_apply_attempt_total', foundation_apply)
        self.assertIn('stackit_foundation_apply_clear_transient_postgres_taint()', foundation_apply)
        self.assertIn('stackit_foundation_apply_untaint_total', foundation_apply)
        self.assertIn('transient STACKIT PostgresFlex create/read race detected', foundation_apply)

    def test_stackit_foundation_destroy_cleans_namespaces_before_cluster_destroy(self) -> None:
        foundation_destroy = _read("scripts/bin/infra/stackit_foundation_destroy.sh")
        tooling = _read("scripts/lib/infra/tooling.sh")

        self.assertIn('STACKIT_FOUNDATION_NAMESPACE_DELETE_TIMEOUT_SECONDS', foundation_destroy)
        self.assertIn('stackit_foundation_cleanup_namespaces_before_destroy', foundation_destroy)
        self.assertIn('stackit_foundation_prepare_namespace_cleanup_access', foundation_destroy)
        self.assertIn('delete_blueprint_managed_namespaces', foundation_destroy)
        self.assertIn('stackit_foundation_namespace_cleanup_total', foundation_destroy)
        self.assertIn('namespace_cleanup_status=$STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS', foundation_destroy)
        self.assertIn('blueprint_managed_namespaces()', tooling)
        self.assertIn('delete_blueprint_managed_namespaces()', tooling)
        self.assertIn('PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE "envoy-gateway-system"', tooling)

    def test_rabbitmq_smoke_accepts_managed_tls_uris(self) -> None:
        rabbitmq_smoke = _read("scripts/bin/infra/rabbitmq_smoke.sh")
        rabbitmq_lib = _read("scripts/lib/infra/rabbitmq.sh")

        self.assertIn("^uri=amqps?://", rabbitmq_smoke)
        self.assertIn('amqps://provider-generated:provider-generated@', rabbitmq_lib)

    def test_local_crossplane_bootstrap_waits_for_chart_deployment_names(self) -> None:
        bootstrap = _read("scripts/bin/infra/local_crossplane_bootstrap.sh")
        self.assertIn("deployment/crossplane", bootstrap)
        self.assertIn("deployment/crossplane-rbac-manager", bootstrap)
        self.assertNotIn('deployment/"$CROSSPLANE_HELM_RELEASE"', bootstrap)

    def test_optional_module_chart_pins_use_canonical_versions_source(self) -> None:
        versions = _read("scripts/lib/infra/versions.sh")
        self.assertIn('POSTGRES_HELM_CHART_VERSION_PIN="15.5.38"', versions)
        self.assertIn('OBJECT_STORAGE_HELM_CHART_VERSION_PIN="17.0.21"', versions)
        self.assertIn('RABBITMQ_HELM_CHART_VERSION_PIN="14.7.0"', versions)
        self.assertIn('NEO4J_HELM_CHART_VERSION_PIN="2026.1.4"', versions)
        self.assertIn('PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN="1.7.1"', versions)
        self.assertIn('IAP_HELM_CHART_VERSION_PIN="10.4.0"', versions)
        self.assertIn('POSTGRES_LOCAL_IMAGE_REGISTRY="docker.io"', versions)
        self.assertIn('POSTGRES_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/postgresql"', versions)
        self.assertIn('OBJECT_STORAGE_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/minio"', versions)
        self.assertIn('RABBITMQ_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/rabbitmq"', versions)
        self.assertIn('RABBITMQ_LOCAL_IMAGE_TAG="3.13.7-debian-12-r2"', versions)
        self.assertIn('IAP_LOCAL_IMAGE_REGISTRY="quay.io"', versions)

        self.assertIn(
            'set_default_env POSTGRES_HELM_CHART_VERSION "$POSTGRES_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/postgres.sh"),
        )
        self.assertIn('set_default_env POSTGRES_IMAGE_REGISTRY "$POSTGRES_LOCAL_IMAGE_REGISTRY"', _read("scripts/lib/infra/postgres.sh"))
        self.assertIn("postgres_render_values_file()", _read("scripts/lib/infra/postgres.sh"))
        self.assertIn(
            'set_default_env OBJECT_STORAGE_HELM_CHART_VERSION "$OBJECT_STORAGE_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/object_storage.sh"),
        )
        self.assertIn(
            'set_default_env OBJECT_STORAGE_IMAGE_REGISTRY "$OBJECT_STORAGE_LOCAL_IMAGE_REGISTRY"',
            _read("scripts/lib/infra/object_storage.sh"),
        )
        self.assertIn("object_storage_render_values_file()", _read("scripts/lib/infra/object_storage.sh"))
        self.assertIn(
            'set_default_env RABBITMQ_HELM_CHART_VERSION "$RABBITMQ_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/rabbitmq.sh"),
        )
        self.assertIn('set_default_env RABBITMQ_IMAGE_REGISTRY "$RABBITMQ_LOCAL_IMAGE_REGISTRY"', _read("scripts/lib/infra/rabbitmq.sh"))
        self.assertIn(
            'set_default_env NEO4J_HELM_CHART_VERSION "$NEO4J_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/neo4j.sh"),
        )
        self.assertIn(
            'set_default_env PUBLIC_ENDPOINTS_HELM_CHART_VERSION "$PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/public_endpoints.sh"),
        )
        self.assertIn(
            'set_default_env IAP_HELM_CHART_VERSION "$IAP_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/identity_aware_proxy.sh"),
        )
        self.assertIn('set_default_env IAP_IMAGE_REGISTRY "$IAP_LOCAL_IMAGE_REGISTRY"', _read("scripts/lib/infra/identity_aware_proxy.sh"))
        self.assertIn("identity_aware_proxy_validate_cookie_secret()", _read("scripts/lib/infra/identity_aware_proxy.sh"))

    def test_local_helm_templates_use_rendered_release_and_image_contracts(self) -> None:
        postgres_values = _read("scripts/templates/infra/bootstrap/infra/local/helm/postgres/values.yaml")
        object_storage_values = _read("scripts/templates/infra/bootstrap/infra/local/helm/object-storage/values.yaml")
        rabbitmq_values = _read("scripts/templates/infra/bootstrap/infra/local/helm/rabbitmq/values.yaml")
        iap_values = _read("scripts/templates/infra/bootstrap/infra/local/helm/identity-aware-proxy/values.yaml")

        self.assertIn('fullnameOverride: "{{POSTGRES_HELM_RELEASE}}"', postgres_values)
        self.assertIn('repository: "{{POSTGRES_IMAGE_REPOSITORY}}"', postgres_values)
        self.assertIn('database: "{{POSTGRES_DB_NAME}}"', postgres_values)

        self.assertIn('fullnameOverride: "{{OBJECT_STORAGE_HELM_RELEASE}}"', object_storage_values)
        self.assertIn("allowInsecureImages: true", object_storage_values)
        self.assertIn('defaultBuckets: "{{OBJECT_STORAGE_BUCKET_NAME}}"', object_storage_values)
        self.assertIn("console:", object_storage_values)
        self.assertIn("enabled: false", object_storage_values)

        self.assertIn('repository: "{{RABBITMQ_IMAGE_REPOSITORY}}"', rabbitmq_values)
        self.assertIn('tag: "{{RABBITMQ_IMAGE_TAG}}"', rabbitmq_values)

        self.assertIn('repository: "{{IAP_IMAGE_REPOSITORY}}"', iap_values)
        self.assertIn('tag: "{{IAP_IMAGE_TAG}}"', iap_values)

    def test_infra_audit_version_checks_local_helm_chart_pin_resolution(self) -> None:
        audit = _read("scripts/bin/infra/audit_version.sh")
        tooling = _read("scripts/lib/infra/tooling.sh")
        self.assertIn('source "$ROOT_DIR/scripts/lib/infra/tooling.sh"', audit)
        self.assertIn('audit_helm_chart_pin "POSTGRES_HELM_CHART_VERSION_PIN" "bitnami/postgresql"', audit)
        self.assertIn('audit_helm_chart_pin "OBJECT_STORAGE_HELM_CHART_VERSION_PIN" "bitnami/minio"', audit)
        self.assertIn('audit_helm_chart_pin "RABBITMQ_HELM_CHART_VERSION_PIN" "bitnami/rabbitmq"', audit)
        self.assertIn('audit_helm_chart_pin "NEO4J_HELM_CHART_VERSION_PIN" "neo4j/neo4j"', audit)
        self.assertIn('audit_helm_chart_pin "PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN" "oci://docker.io/envoyproxy/gateway-helm"', audit)
        self.assertIn('audit_helm_chart_pin "IAP_HELM_CHART_VERSION_PIN" "oauth2-proxy/oauth2-proxy"', audit)
        self.assertIn(
            'audit_container_image_pin "POSTGRES_LOCAL_IMAGE_REGISTRY" "POSTGRES_LOCAL_IMAGE_REPOSITORY" "POSTGRES_LOCAL_IMAGE_TAG"',
            audit,
        )
        self.assertIn(
            'audit_container_image_pin "RABBITMQ_LOCAL_IMAGE_REGISTRY" "RABBITMQ_LOCAL_IMAGE_REPOSITORY" "RABBITMQ_LOCAL_IMAGE_TAG"',
            audit,
        )
        self.assertIn('docker manifest inspect "$image_ref"', audit)
        self.assertIn('helm show chart "$chart_ref" --version "$version"', audit)
        self.assertIn('helm search repo "$chart_ref" --versions', audit)
        self.assertIn('run_cmd helm repo update "$repo_name"', tooling)

    def test_pre_commit_hooks_include_cached_audits_and_shell_syntax(self) -> None:
        pre_commit = _read(".pre-commit-config.yaml")
        template_pre_commit = _read("scripts/templates/blueprint/bootstrap/.pre-commit-config.yaml")

        self.assertIn("- id: check-yaml", pre_commit)
        self.assertIn("- id: check-added-large-files", pre_commit)
        self.assertIn("- id: bash-syntax", pre_commit)
        self.assertIn("entry: bash -n", pre_commit)
        self.assertIn("files: \\.sh$", pre_commit)
        self.assertIn("- id: infra-audit-version-cached", pre_commit)
        self.assertIn("- id: apps-audit-versions-cached", pre_commit)
        self.assertGreaterEqual(pre_commit.count("stages: [pre-push]"), 2)
        self.assertIn("pass_filenames: false", pre_commit)
        self.assertIn("always_run: true", pre_commit)
        self.assertEqual(pre_commit, template_pre_commit)

    def test_validate_command_is_contract_driven(self) -> None:
        validate_sh = _read("scripts/bin/infra/validate.sh")
        self.assertIn("scripts/bin/blueprint/validate_contract.py", validate_sh)
        self.assertIn("--contract-path \"$ROOT_DIR/blueprint/contract.yaml\"", validate_sh)

    def test_contract_template_bootstrap_metadata_is_canonical(self) -> None:
        contract_lines = self._contract_lines()
        repository_section = _extract_yaml_section(contract_lines, "repository")
        self.assertTrue(repository_section, msg="repository section is required in blueprint/contract.yaml")

        branch_naming_section = _extract_yaml_section(repository_section, "branch_naming")
        purpose_prefixes = set(_extract_yaml_list(branch_naming_section, "purpose_prefixes"))
        self.assertEqual(_extract_yaml_scalar(branch_naming_section, "model"), "github-flow")
        self.assertTrue(
            {"feature/", "fix/", "chore/", "docs/"}.issubset(purpose_prefixes),
            msg=f"missing required github-flow branch purpose prefixes: {purpose_prefixes}",
        )

        template_section = _extract_yaml_section(repository_section, "template_bootstrap")
        self.assertEqual(_extract_yaml_scalar(template_section, "model"), "github-template")
        self.assertEqual(_extract_yaml_scalar(template_section, "template_version"), "1.0.0")
        self.assertEqual(_extract_yaml_scalar(template_section, "init_command"), "make blueprint-init-repo")
        self.assertEqual(_extract_yaml_scalar(template_section, "defaults_env_file"), "blueprint/repo.init.env")
        self.assertEqual(
            _extract_yaml_scalar(template_section, "secrets_example_env_file"),
            "blueprint/repo.init.secrets.example.env",
        )
        self.assertEqual(
            _extract_yaml_scalar(template_section, "secrets_env_file"),
            "blueprint/repo.init.secrets.env",
        )
        self.assertEqual(_extract_yaml_scalar(template_section, "force_env_var"), "BLUEPRINT_INIT_FORCE")

        required_inputs = set(_extract_yaml_list(template_section, "required_inputs"))
        self.assertSetEqual(
            required_inputs,
            {
                "BLUEPRINT_REPO_NAME",
                "BLUEPRINT_GITHUB_ORG",
                "BLUEPRINT_GITHUB_REPO",
                "BLUEPRINT_DEFAULT_BRANCH",
                "BLUEPRINT_STACKIT_REGION",
                "BLUEPRINT_STACKIT_TENANT_SLUG",
                "BLUEPRINT_STACKIT_PLATFORM_SLUG",
                "BLUEPRINT_STACKIT_PROJECT_ID",
                "BLUEPRINT_STACKIT_TFSTATE_BUCKET",
                "BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX",
            },
        )

    def test_contract_surface_assets_targets_and_namespaces_are_present(self) -> None:
        contract_lines = self._contract_lines()
        required_files = set(_extract_yaml_list(contract_lines, "required_files"))
        repository_section = _extract_yaml_section(contract_lines, "repository")
        ownership_classes = _extract_yaml_section(repository_section, "ownership_path_classes")
        source_only_paths = set(_extract_yaml_list(ownership_classes, "source_only"))
        consumer_seeded_paths = set(_extract_yaml_list(ownership_classes, "consumer_seeded"))
        init_managed_paths = set(_extract_yaml_list(ownership_classes, "init_managed"))
        conditional_scaffold_paths = set(_extract_yaml_list(ownership_classes, "conditional_scaffold"))
        self.assertTrue(
            {
                ".github/actions/prepare-blueprint-ci/action.yml",
                ".github/CODEOWNERS",
                ".github/ISSUE_TEMPLATE/bug_report.yml",
                ".github/ISSUE_TEMPLATE/feature_request.yml",
                ".github/ISSUE_TEMPLATE/config.yml",
                ".github/pull_request_template.md",
                ".github/workflows/ci.yml",
                ".gitignore",
                ".dockerignore",
                ".editorconfig",
                ".pre-commit-config.yaml",
                "README.md",
                "make/blueprint.generated.mk",
                "make/platform.mk",
                "docs/blueprint/README.md",
                "docs/blueprint/architecture/system_overview.md",
                "docs/blueprint/architecture/execution_model.md",
                "docs/blueprint/governance/ownership_matrix.md",
                "docs/platform/README.md",
                "docs/platform/consumer/first_30_minutes.md",
                "docs/platform/consumer/quickstart.md",
                "docs/platform/consumer/endpoint_exposure_model.md",
                "docs/platform/consumer/protected_api_routes.md",
                "docs/platform/consumer/troubleshooting.md",
                "docs/platform/modules/observability/README.md",
                "docs/platform/modules/workflows/README.md",
                "docs/platform/modules/langfuse/README.md",
                "docs/platform/modules/postgres/README.md",
                "docs/platform/modules/neo4j/README.md",
                "docs/platform/modules/object-storage/README.md",
                "docs/platform/modules/rabbitmq/README.md",
                "docs/platform/modules/dns/README.md",
                "docs/platform/modules/public-endpoints/README.md",
                "docs/platform/modules/secrets-manager/README.md",
                "docs/platform/modules/kms/README.md",
                "docs/platform/modules/identity-aware-proxy/README.md",
                "scripts/templates/blueprint/bootstrap/Makefile",
                "scripts/templates/blueprint/bootstrap/blueprint/contract.yaml",
                "scripts/templates/blueprint/bootstrap/docs/docusaurus.config.js",
                "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl",
                "scripts/templates/blueprint/bootstrap/make/platform.mk",
                "scripts/templates/consumer/init/README.md.tmpl",
                "scripts/templates/consumer/init/AGENTS.md.tmpl",
                "scripts/templates/consumer/init/AGENTS.backlog.md.tmpl",
                "scripts/templates/consumer/init/AGENTS.decisions.md.tmpl",
                "scripts/templates/consumer/init/docs/README.md.tmpl",
                "scripts/templates/consumer/init/.github/CODEOWNERS.tmpl",
                "scripts/templates/consumer/init/.github/ISSUE_TEMPLATE/bug_report.yml.tmpl",
                "scripts/templates/consumer/init/.github/ISSUE_TEMPLATE/feature_request.yml.tmpl",
                "scripts/templates/consumer/init/.github/ISSUE_TEMPLATE/config.yml.tmpl",
                "scripts/templates/consumer/init/.github/pull_request_template.md.tmpl",
                "scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl",
                "scripts/lib/blueprint/bootstrap_templates.sh",
                "scripts/lib/blueprint/contract_schema.py",
                "scripts/lib/blueprint/contract_runtime.sh",
                "scripts/lib/blueprint/contract_runtime_cli.py",
                "scripts/lib/blueprint/cli_support.py",
                "scripts/lib/blueprint/generate_module_wrapper_skeletons.py",
                "scripts/lib/blueprint/init_repo.py",
                "scripts/lib/blueprint/init_repo_contract.py",
                "scripts/lib/blueprint/init_repo_env.py",
                "scripts/lib/blueprint/init_repo_io.py",
                "scripts/lib/blueprint/init_repo_renderers.py",
                "scripts/lib/blueprint/resync_consumer_seeds.py",
                "scripts/lib/docs/generate_contract_docs.py",
                "scripts/lib/docs/sync_module_contract_summaries.py",
                "scripts/lib/infra/k8s_wait.sh",
                "scripts/lib/infra/module_execution.sh",
                "scripts/lib/quality/semver.sh",
                "scripts/lib/quality/test_pyramid_contract.json",
                "scripts/lib/shell/bootstrap.sh",
                "scripts/lib/shell/exec.sh",
                "scripts/lib/shell/logging.sh",
                "scripts/lib/shell/utils.sh",
                "scripts/bin/blueprint/clean_generated.sh",
                "scripts/bin/blueprint/init_repo_interactive.sh",
                "scripts/bin/blueprint/resync_consumer_seeds.sh",
                "scripts/bin/blueprint/render_module_wrapper_skeletons.sh",
                "scripts/bin/infra/destroy_disabled_modules.sh",
                "scripts/bin/infra/local_destroy_all.sh",
                "scripts/bin/infra/workload_health_check.py",
                "scripts/bin/quality/check_test_pyramid.py",
                "scripts/bin/quality/hooks_fast.sh",
                "scripts/bin/quality/hooks_run.sh",
                "scripts/bin/quality/hooks_strict.sh",
                "scripts/bin/quality/lint_docs.py",
                "scripts/bin/quality/render_core_targets_doc.py",
                "docs/docusaurus.config.js",
                "docs/reference/generated/contract_metadata.generated.md",
                "docs/reference/generated/core_targets.generated.md",
                "tests/__init__.py",
                "tests/infra/__init__.py",
                "tests/e2e/__init__.py",
                "tests/_shared/__init__.py",
                "tests/_shared/helpers.py",
            }.issubset(required_files),
            msg="contract required_files is missing canonical blueprint assets",
        )
        self.assertEqual(source_only_paths, {"tests/blueprint", "tests/docs"})
        self.assertTrue(
            {
                "README.md",
                "AGENTS.md",
                "AGENTS.backlog.md",
                "AGENTS.decisions.md",
                "docs/README.md",
                ".github/CODEOWNERS",
                ".github/ISSUE_TEMPLATE/bug_report.yml",
                ".github/ISSUE_TEMPLATE/feature_request.yml",
                ".github/ISSUE_TEMPLATE/config.yml",
                ".github/pull_request_template.md",
                ".github/workflows/ci.yml",
            }.issubset(consumer_seeded_paths)
        )
        self.assertTrue(
            {
                "blueprint/repo.init.env",
                "blueprint/repo.init.secrets.example.env",
                "blueprint/contract.yaml",
                "docs/docusaurus.config.js",
                "infra/gitops/argocd/root/applicationset-platform-environments.yaml",
                "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars",
                "infra/cloud/stackit/terraform/foundation/state-backend/prod.hcl",
            }.issubset(init_managed_paths)
        )
        self.assertIn("dags/", conditional_scaffold_paths)
        self.assertIn("infra/cloud/stackit/terraform/modules/workflows", conditional_scaffold_paths)
        self.assertIn("infra/gitops/argocd/optional/${ENV}/langfuse.yaml", conditional_scaffold_paths)
        self.assertIn("infra/local/helm/identity-aware-proxy/values.yaml", conditional_scaffold_paths)

        consumer_init = _extract_yaml_section(repository_section, "consumer_init")
        self.assertEqual(_extract_yaml_scalar(repository_section, "repo_mode"), "template-source")
        self.assertEqual(
            set(_extract_yaml_list(repository_section, "allowed_repo_modes")),
            {"template-source", "generated-consumer"},
        )
        self.assertEqual(_extract_yaml_scalar(consumer_init, "template_root"), "scripts/templates/consumer/init")
        self.assertEqual(_extract_yaml_scalar(consumer_init, "mode_from"), "template-source")
        self.assertEqual(_extract_yaml_scalar(consumer_init, "mode_to"), "generated-consumer")

        required_namespaces = set(_extract_yaml_list(contract_lines, "required_namespaces"))
        self.assertTrue(
            {"blueprint-", "quality-", "infra-", "apps-", "backend-", "touchpoints-", "test-", "docs-"}
            .issubset(required_namespaces)
        )
        required_paths = set(_extract_yaml_list(contract_lines, "required_paths"))
        self.assertTrue(
            {
                "tests/infra/",
                "tests/e2e/",
                "tests/_shared/",
                "make/",
                "make/platform/",
                "scripts/bin/platform/",
                "scripts/lib/platform/",
            }
            .issubset(required_paths)
        )
        blueprint_managed_roots = set(_extract_yaml_list(contract_lines, "blueprint_managed_roots"))
        self.assertTrue(
            {
                "scripts/bin/blueprint/",
                "scripts/bin/docs/",
                "scripts/bin/infra/",
                "scripts/bin/quality/",
                "scripts/lib/blueprint/",
                "scripts/lib/docs/",
                "scripts/lib/infra/",
                "scripts/lib/quality/",
                "scripts/lib/shell/",
            }.issubset(blueprint_managed_roots)
        )

        required_targets = set(_extract_yaml_list(contract_lines, "required_targets"))
        self.assertTrue(
            {
                "blueprint-init-repo",
                "blueprint-init-repo-interactive",
                "blueprint-resync-consumer-seeds",
                "blueprint-check-placeholders",
                "blueprint-template-smoke",
                "blueprint-bootstrap",
                "blueprint-clean-generated",
                "blueprint-render-makefile",
                "blueprint-render-module-wrapper-skeletons",
                "quality-hooks-fast",
                "quality-hooks-strict",
                "quality-docs-lint",
                "quality-docs-sync-core-targets",
                "quality-docs-check-core-targets-sync",
                "quality-docs-sync-contract-metadata",
                "quality-docs-check-contract-metadata-sync",
                "quality-docs-sync-module-contract-summaries",
                "quality-docs-check-module-contract-summaries-sync",
                "quality-test-pyramid",
                "infra-prereqs",
                "infra-help-reference",
                "infra-local-destroy-all",
                "infra-destroy-disabled-modules",
                "infra-stackit-ci-github-setup",
                "infra-audit-version-cached",
                "apps-audit-versions-cached",
                "apps-publish-ghcr",
                "docs-build",
                "docs-smoke",
            }.issubset(required_targets),
            msg="contract required_targets is missing canonical blueprint/stackit/docs targets",
        )

    def test_make_contract_optional_materialization_is_canonical(self) -> None:
        contract_lines = self._contract_lines()
        make_contract_section = _extract_yaml_section(contract_lines, "make_contract")
        required_targets = set(_extract_yaml_list(contract_lines, "required_targets"))
        required_namespaces = set(_extract_yaml_list(contract_lines, "required_namespaces"))
        optional_target_materialization = _extract_yaml_section(
            make_contract_section,
            "optional_target_materialization",
        )
        self.assertEqual(_extract_yaml_scalar(optional_target_materialization, "mode"), "conditional")
        self.assertEqual(
            _extract_yaml_scalar(optional_target_materialization, "source_template"),
            "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl",
        )
        self.assertEqual(
            _extract_yaml_scalar(optional_target_materialization, "output_file"),
            "make/blueprint.generated.mk",
        )
        self.assertEqual(
            _extract_yaml_scalar(optional_target_materialization, "materialization_command"),
            "make blueprint-render-makefile",
        )

        make_targets = _make_targets()
        self.assertTrue(required_targets.issubset(make_targets), msg="contract required_targets drifted from Makefile")
        for namespace in required_namespaces:
            self.assertTrue(any(target.startswith(namespace) for target in make_targets))

    def test_validator_has_core_contract_sections(self) -> None:
        validate_py = _read("scripts/bin/blueprint/validate_contract.py")
        self.assertIn("load_blueprint_contract", validate_py)
        for marker in (
            "_validate_optional_target_materialization_contract",
            "_validate_template_bootstrap_contract",
            "_validate_branch_naming_contract",
            "_validate_optional_module_make_targets",
            "_validate_module_wrapper_skeleton_templates",
            "_validate_bootstrap_template_sync",
            "_validate_make_ownership_contract",
            "_validate_repository_mode_contract",
            "_validate_script_ownership_contract",
            "_validate_platform_docs_seed_contract",
        ):
            self.assertIn(marker, validate_py)
        self.assertNotIn("def _extract_yaml_list", validate_py)

    def test_docs_generator_uses_schema_driven_contract_loader(self) -> None:
        docs_generator = _read("scripts/lib/docs/generate_contract_docs.py")
        self.assertIn("load_blueprint_contract", docs_generator)
        self.assertIn("load_module_contract", docs_generator)
        self.assertNotIn("def extract_scalar(", docs_generator)

    def test_blueprint_bootstrap_seeds_templates_from_single_list(self) -> None:
        bootstrap = _read("scripts/bin/blueprint/bootstrap.sh")
        self.assertIn("local template_files=(", bootstrap)
        self.assertIn("ensure_blueprint_seed_file()", bootstrap)
        self.assertIn('"make/platform.mk"', bootstrap)
        self.assertIn('"blueprint/repo.init.env"', bootstrap)
        self.assertIn('"blueprint/repo.init.secrets.example.env"', bootstrap)
        self.assertIn('"docs/platform/consumer/quickstart.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/first_30_minutes.md"', bootstrap)
        self.assertIn('"docs/blueprint/governance/ownership_matrix.md"', bootstrap)
        self.assertIn('"docs/platform/modules/identity-aware-proxy/README.md"', bootstrap)
        self.assertIn('ensure_dir "$ROOT_DIR/docs/reference/generated"', bootstrap)
        self.assertIn('scripts/bin/quality/render_core_targets_doc.py', bootstrap)
        self.assertIn('docs/reference/generated/core_targets.generated.md', bootstrap)
        self.assertIn('scripts/lib/docs/generate_contract_docs.py', bootstrap)
        self.assertIn('docs/reference/generated/contract_metadata.generated.md', bootstrap)
        self.assertIn('log_metric "blueprint_template_file_count" "${#template_files[@]}"', bootstrap)
        self.assertIn('blueprint_consumer_seeded_skip_count', bootstrap)
        self.assertIn('missing consumer-initialized file:', bootstrap)
        self.assertIn("make blueprint-resync-consumer-seeds", bootstrap)
        self.assertIn(
            "pre-commit install --install-hooks --hook-type pre-commit --hook-type pre-push",
            bootstrap,
        )

    def test_bootstrap_ignore_templates_cover_generated_outputs(self) -> None:
        bootstrap = _read("scripts/bin/blueprint/bootstrap.sh")
        gitignore_template = _read("scripts/templates/blueprint/bootstrap/.gitignore")
        dockerignore_template = _read("scripts/templates/blueprint/bootstrap/.dockerignore")

        self.assertIn('".gitignore"', bootstrap)
        self.assertIn('".dockerignore"', bootstrap)

        self.assertIn("artifacts/", gitignore_template)
        self.assertIn("blueprint/repo.init.secrets.env", gitignore_template)
        self.assertNotIn("blueprint/repo.init.env", gitignore_template)
        self.assertIn("docs/build/", gitignore_template)
        self.assertIn("docs/.docusaurus/", gitignore_template)

        self.assertIn("artifacts", dockerignore_template)
        self.assertIn("docs/build", dockerignore_template)
        self.assertIn("docs/.docusaurus", dockerignore_template)

    def test_bootstrap_docs_templates_are_synchronized(self) -> None:
        template_root = REPO_ROOT / "scripts/templates/blueprint/bootstrap"
        synced_docs = [
            "blueprint/contract.yaml",
            "docs/docusaurus.config.js",
            "docs/README.md",
            "docs/blueprint/README.md",
            "docs/blueprint/architecture/system_overview.md",
            "docs/blueprint/architecture/execution_model.md",
            "docs/blueprint/governance/ownership_matrix.md",
        ]
        for rel_path in synced_docs:
            self.assertEqual(
                (REPO_ROOT / rel_path).read_text(encoding="utf-8"),
                (template_root / rel_path).read_text(encoding="utf-8"),
                msg=f"bootstrap template drift for {rel_path}",
            )

    def test_platform_docs_are_seeded_but_not_template_synced(self) -> None:
        contract_lines = _read("blueprint/contract.yaml").splitlines()
        docs_contract = _extract_yaml_section(contract_lines, "docs_contract")
        platform_docs = _extract_yaml_section(docs_contract, "platform_docs")
        bootstrap = _read("scripts/bin/blueprint/bootstrap.sh")
        bootstrap_lib = _read("scripts/lib/shell/bootstrap.sh")
        validate_py = _read("scripts/bin/blueprint/validate_contract.py")

        self.assertEqual(_extract_yaml_scalar(platform_docs, "seed_mode"), "create_if_missing")
        self.assertEqual(_extract_yaml_scalar(platform_docs, "bootstrap_command"), "make blueprint-bootstrap")
        self.assertIn("docs/platform/consumer/quickstart.md", _extract_yaml_list(platform_docs, "required_seed_files"))
        self.assertIn(
            "docs/platform/consumer/endpoint_exposure_model.md",
            _extract_yaml_list(platform_docs, "required_seed_files"),
        )
        self.assertIn(
            "docs/platform/consumer/protected_api_routes.md",
            _extract_yaml_list(platform_docs, "required_seed_files"),
        )

        self.assertIn('"docs/platform/consumer/quickstart.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/endpoint_exposure_model.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/protected_api_routes.md"', bootstrap)
        self.assertIn("if [[ -f \"$path\" ]]; then", bootstrap_lib)
        self.assertIn("_validate_platform_docs_seed_contract", validate_py)
        self.assertNotIn('"docs/platform/consumer/quickstart.md",', validate_py)

    def test_platform_make_is_seeded_but_not_template_synced(self) -> None:
        contract_lines = _read("blueprint/contract.yaml").splitlines()
        make_contract = _extract_yaml_section(contract_lines, "make_contract")
        ownership = _extract_yaml_section(make_contract, "ownership")
        bootstrap = _read("scripts/bin/blueprint/bootstrap.sh")
        bootstrap_lib = _read("scripts/lib/shell/bootstrap.sh")
        validate_py = _read("scripts/bin/blueprint/validate_contract.py")

        self.assertEqual(_extract_yaml_scalar(ownership, "platform_seed_mode"), "create_if_missing")
        self.assertEqual(_extract_yaml_scalar(ownership, "platform_editable_file"), "make/platform.mk")
        self.assertEqual(_extract_yaml_scalar(ownership, "blueprint_generated_file"), "make/blueprint.generated.mk")
        self.assertIn('"make/platform.mk"', bootstrap)
        self.assertIn("if [[ -f \"$path\" ]]; then", bootstrap_lib)
        self.assertIn("_validate_make_ownership_contract", validate_py)
        self.assertNotIn('"make/platform.mk",', validate_py)

    def test_docs_readme_points_to_command_discovery(self) -> None:
        docs_readme = _read("docs/README.md")
        self.assertIn("make quality-hooks-fast", docs_readme)
        self.assertIn("make quality-hooks-strict", docs_readme)
        self.assertIn("make quality-hooks-run", docs_readme)
        self.assertIn("make quality-docs-lint", docs_readme)
        self.assertIn("make quality-docs-sync-module-contract-summaries", docs_readme)
        self.assertIn("make quality-test-pyramid", docs_readme)
        self.assertIn("make docs-run", docs_readme)
        self.assertIn("make infra-context", docs_readme)
        self.assertIn("make infra-status-json", docs_readme)
        self.assertIn("make infra-local-destroy-all", docs_readme)
        self.assertIn("make infra-stackit-destroy-all", docs_readme)
        self.assertIn("make blueprint-bootstrap", docs_readme)
        self.assertIn("make blueprint-resync-consumer-seeds", docs_readme)
        self.assertIn("make blueprint-render-module-wrapper-skeletons", docs_readme)
        self.assertIn("make blueprint-clean-generated", docs_readme)
        self.assertIn("BLUEPRINT_INIT_FORCE=true make blueprint-init-repo", docs_readme)
        self.assertIn("make help", docs_readme)
        self.assertIn("make infra-help-reference", docs_readme)
        self.assertIn("make infra-destroy-disabled-modules", docs_readme)
        self.assertIn(
            "materializes enabled optional-module infra scaffolding and preserves disabled-module scaffolding",
            docs_readme,
        )
        self.assertIn("[Blueprint Docs](blueprint/README.md)", docs_readme)
        self.assertIn("[Platform Docs](platform/README.md)", docs_readme)
        self.assertIn("[Endpoint Exposure Model](platform/consumer/endpoint_exposure_model.md)", docs_readme)
        self.assertIn("[Protected API Routes](platform/consumer/protected_api_routes.md)", docs_readme)
        self.assertIn("[Core Make Targets (Generated)](reference/generated/core_targets.generated.md)", docs_readme)
        self.assertIn("artifacts/infra/workload_health.json", docs_readme)

    def test_consumer_quickstart_mentions_status_snapshot_and_no_duplicate_smoke(self) -> None:
        quickstart = _read("docs/platform/consumer/quickstart.md")
        self.assertIn("make blueprint-resync-consumer-seeds", quickstart)
        self.assertIn("make infra-context", quickstart)
        self.assertIn("make infra-provision-deploy", quickstart)
        self.assertIn("make infra-status-json", quickstart)
        self.assertIn("LOCAL_KUBE_CONTEXT", quickstart)
        self.assertIn("[Endpoint Exposure Model](endpoint_exposure_model.md)", quickstart)
        self.assertIn("[Protected API Routes](protected_api_routes.md)", quickstart)
        self.assertIn("artifacts/infra/infra_status_snapshot.json", quickstart)
        self.assertIn("artifacts/infra/workload_health.json", quickstart)
        self.assertNotIn("make infra-smoke", quickstart)

    def test_endpoint_exposure_model_is_seeded_and_template_synced(self) -> None:
        endpoint_model = _read("docs/platform/consumer/endpoint_exposure_model.md")
        endpoint_model_template = _read(
            "scripts/templates/blueprint/bootstrap/docs/platform/consumer/endpoint_exposure_model.md"
        )
        self.assertIn("## Policy Matrix", endpoint_model)
        self.assertIn("Protected touchpoint", endpoint_model)
        self.assertIn("Protected API", endpoint_model)
        self.assertIn("```mermaid", endpoint_model)
        self.assertEqual(endpoint_model, endpoint_model_template)

    def test_protected_api_routes_guide_is_seeded_and_template_synced(self) -> None:
        protected_api_routes = _read("docs/platform/consumer/protected_api_routes.md")
        protected_api_routes_template = _read(
            "scripts/templates/blueprint/bootstrap/docs/platform/consumer/protected_api_routes.md"
        )
        self.assertIn("## Recommended Pattern", protected_api_routes)
        self.assertIn("kind: SecurityPolicy", protected_api_routes)
        self.assertIn("platform-edge-*", protected_api_routes)
        self.assertEqual(protected_api_routes, protected_api_routes_template)

    def test_gateway_module_docs_link_to_endpoint_exposure_model(self) -> None:
        public_endpoints_doc = _read("docs/platform/modules/public-endpoints/README.md")
        public_endpoints_doc_template = _read(
            "scripts/templates/blueprint/bootstrap/docs/platform/modules/public-endpoints/README.md"
        )
        identity_aware_proxy_doc = _read("docs/platform/modules/identity-aware-proxy/README.md")
        identity_aware_proxy_doc_template = _read(
            "scripts/templates/blueprint/bootstrap/docs/platform/modules/identity-aware-proxy/README.md"
        )

        self.assertIn("[Endpoint Exposure Model](../../consumer/endpoint_exposure_model.md)", public_endpoints_doc)
        self.assertIn("[Protected API Routes](../../consumer/protected_api_routes.md)", public_endpoints_doc)
        self.assertIn("[Endpoint Exposure Model](../../consumer/endpoint_exposure_model.md)", identity_aware_proxy_doc)
        self.assertEqual(public_endpoints_doc, public_endpoints_doc_template)
        self.assertEqual(identity_aware_proxy_doc, identity_aware_proxy_doc_template)

    def test_platform_base_namespaces_include_network_for_shared_gateway(self) -> None:
        namespaces = _read("infra/gitops/platform/base/namespaces.yaml")
        namespaces_template = _read("scripts/templates/infra/bootstrap/infra/gitops/platform/base/namespaces.yaml")
        self.assertIn("name: network", namespaces)
        self.assertIn("Shared gateway/route attachment namespace", namespaces)
        self.assertEqual(namespaces, namespaces_template)

    def test_argocd_projects_split_edge_and_route_policy_boundaries(self) -> None:
        for environment in ("local", "dev", "stage", "prod"):
            with self.subTest(environment=environment):
                appproject = _read(f"infra/gitops/argocd/overlays/{environment}/appproject.yaml")
                appproject_template = _read(
                    f"scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/{environment}/appproject.yaml"
                )
                edge_appproject = _read(f"infra/gitops/argocd/overlays/{environment}/appproject-edge.yaml")
                edge_appproject_template = _read(
                    f"scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/{environment}/appproject-edge.yaml"
                )
                kustomization = _read(f"infra/gitops/argocd/overlays/{environment}/kustomization.yaml")
                kustomization_template = _read(
                    f"scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/{environment}/kustomization.yaml"
                )

                self.assertNotIn("namespace: network", appproject)
                self.assertIn("kind: HTTPRoute", appproject)
                self.assertIn("kind: BackendTLSPolicy", appproject)
                self.assertIn("kind: SecurityPolicy", appproject)
                self.assertIn("kind: Backend\n", appproject)
                self.assertNotIn("kind: GatewayClass", appproject)
                self.assertNotIn("kind: Gateway\n", appproject)
                self.assertEqual(appproject, appproject_template)

                self.assertIn(f"name: platform-edge-{environment}", edge_appproject)
                self.assertIn("namespace: network", edge_appproject)
                self.assertIn("namespace: envoy-gateway-system", edge_appproject)
                self.assertIn("kind: GatewayClass", edge_appproject)
                self.assertIn("kind: Gateway\n", edge_appproject)
                self.assertNotIn("kind: SecurityPolicy", edge_appproject)
                self.assertEqual(edge_appproject, edge_appproject_template)

                self.assertIn("- appproject-edge.yaml", kustomization)
                self.assertEqual(kustomization, kustomization_template)

    def test_quality_hooks_split_fast_and_strict_gates(self) -> None:
        hooks_fast = _read("scripts/bin/quality/hooks_fast.sh")
        hooks_run = _read("scripts/bin/quality/hooks_run.sh")
        hooks_strict = _read("scripts/bin/quality/hooks_strict.sh")
        self.assertIn("quality-docs-lint", hooks_fast)
        self.assertIn("quality-docs-check-core-targets-sync", hooks_fast)
        self.assertIn("quality-docs-check-contract-metadata-sync", hooks_fast)
        self.assertIn("quality-docs-check-module-contract-summaries-sync", hooks_fast)
        self.assertIn("quality-test-pyramid", hooks_fast)
        self.assertIn("infra-validate", hooks_fast)
        self.assertIn("infra-audit-version", hooks_strict)
        self.assertIn("apps-audit-versions", hooks_strict)
        self.assertIn("hooks_fast.sh", hooks_run)
        self.assertIn("hooks_strict.sh", hooks_run)

    def test_quality_hooks_run_usage_mentions_composed_gates(self) -> None:
        hooks_run = _read("scripts/bin/quality/hooks_run.sh")
        self.assertIn("hooks_fast.sh", hooks_run)
        self.assertIn("hooks_strict.sh", hooks_run)

    def test_governance_documents_legacy_vendor_registry_exception(self) -> None:
        agents = _read("AGENTS.md")
        decisions = _read("AGENTS.decisions.md")
        versions = _read("scripts/lib/infra/versions.sh")
        postgres_doc = _read("docs/platform/modules/postgres/README.md")
        rabbitmq_doc = _read("docs/platform/modules/rabbitmq/README.md")
        object_storage_doc = _read("docs/platform/modules/object-storage/README.md")

        self.assertIn("vendor repository name that contains `legacy` is allowed", agents)
        self.assertIn("bitnamilegacy/*", decisions)
        self.assertIn("Bitnami publishes some current multi-arch tags under the `bitnamilegacy/*`", versions)
        self.assertIn("despite the registry namespace", postgres_doc)
        self.assertIn("despite the registry namespace", rabbitmq_doc)
        self.assertIn("vendor namespace quirk", object_storage_doc)

    def test_clean_generated_prunes_repo_wide_python_caches(self) -> None:
        clean_generated = _read("scripts/bin/blueprint/clean_generated.sh")
        self.assertIn('find "$ROOT_DIR" -type d -name \'__pycache__\'', clean_generated)
        self.assertIn('-name \'*.pyc\' -o -name \'*.pyo\'', clean_generated)
        self.assertNotIn('find "$ROOT_DIR/tests" -type d -name \'__pycache__\'', clean_generated)

    def test_consumer_troubleshooting_covers_disable_vs_destroy(self) -> None:
        troubleshooting = _read("docs/platform/consumer/troubleshooting.md")
        troubleshooting_template = _read("scripts/templates/blueprint/bootstrap/docs/platform/consumer/troubleshooting.md")
        expected_heading = "## Disabled module but resources still exist"
        self.assertIn(expected_heading, troubleshooting)
        self.assertIn("resources are not destroyed automatically", troubleshooting)
        self.assertIn("blueprint source repository", troubleshooting)
        self.assertIn("repo_mode: generated-consumer", troubleshooting)
        self.assertIn("infra-destroy-disabled-modules", troubleshooting)
        self.assertIn("LOCAL_KUBE_CONTEXT", troubleshooting)
        self.assertIn("artifacts/infra/workload_health.json", troubleshooting)
        self.assertIn("infra-local-destroy-all", troubleshooting)
        self.assertIn("infra-stackit-destroy-all", troubleshooting)
        self.assertEqual(troubleshooting, troubleshooting_template)

    def test_module_wrapper_skeletons_use_explicit_not_implemented_stub(self) -> None:
        generator = _read("scripts/lib/blueprint/generate_module_wrapper_skeletons.py")
        workflows_apply_template = _read("scripts/templates/infra/module_wrappers/workflows/stackit_workflows_apply.sh.tmpl")

        self.assertIn("MODULE_WRAPPER_STUB_EXIT_CODE=64", generator)
        self.assertIn("optional_module_wrapper_stub_invocation", generator)
        self.assertIn('scripts/lib/shell/bootstrap.sh', generator)
        self.assertNotIn("TODO: implement module-specific logic for this action.", workflows_apply_template)
        self.assertIn("status=not_implemented", workflows_apply_template)
        self.assertIn("module wrapper not implemented", workflows_apply_template)
        self.assertIn("exit \"$MODULE_WRAPPER_STUB_EXIT_CODE\"", workflows_apply_template)

    def test_module_lifecycle_runner_is_canonical(self) -> None:
        module_lifecycle = _read("scripts/lib/infra/module_lifecycle.sh")
        provision = _read("scripts/bin/infra/provision.sh")
        deploy = _read("scripts/bin/infra/deploy.sh")
        smoke = _read("scripts/bin/infra/smoke.sh")
        destroy_disabled = _read("scripts/bin/infra/destroy_disabled_modules.sh")

        self.assertIn("run_enabled_modules_action()", module_lifecycle)
        self.assertIn("run_disabled_modules_action()", module_lifecycle)
        self.assertIn("module_action_scripts()", module_lifecycle)
        self.assertIn("source \"$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh\"", provision)
        self.assertIn("source \"$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh\"", deploy)
        self.assertIn("source \"$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh\"", smoke)
        self.assertIn("source \"$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh\"", destroy_disabled)
        self.assertIn("run_enabled_modules_action plan", provision)
        self.assertIn("run_enabled_modules_action apply", provision)
        self.assertIn("run_enabled_modules_action deploy", deploy)
        self.assertIn("run_enabled_modules_action smoke", smoke)
        self.assertIn("run_disabled_modules_action destroy", destroy_disabled)
        self.assertIn('echo "$ROOT_DIR/scripts/bin/infra/public_endpoints_deploy.sh"', module_lifecycle)
        self.assertIn('echo "$ROOT_DIR/scripts/bin/infra/identity_aware_proxy_deploy.sh"', module_lifecycle)
        self.assertIn("module_action_enabled_count", module_lifecycle)
        self.assertIn("module_action_script_count", module_lifecycle)
        self.assertIn("module_action_disabled_count", module_lifecycle)
        self.assertIn("module_action_disabled_script_count", module_lifecycle)

    def test_bootstrap_preserves_disabled_optional_scaffolding(self) -> None:
        bootstrap = _read("scripts/bin/infra/bootstrap.sh")
        self.assertIn(
            'ensure_infra_template_file "tests/infra/modules/observability/README.md"',
            bootstrap,
        )
        self.assertIn("report_disabled_module_scaffolding_preserved()", bootstrap)
        self.assertIn("optional_module_disabled_scaffold_preserved_count", bootstrap)
        self.assertIn("disabled optional-module scaffolding preserved:", bootstrap)
        self.assertNotIn("prune_optional_module_scaffolding()", bootstrap)
        self.assertNotIn("prune_path_if_exists()", bootstrap)
        self.assertNotIn("optional_module_pruned_path_count", bootstrap)

    def test_infra_bootstrap_does_not_recreate_init_managed_files_in_generated_repos(self) -> None:
        bootstrap = _read("scripts/bin/infra/bootstrap.sh")
        self.assertIn("ensure_infra_template_file()", bootstrap)
        self.assertIn("ensure_infra_rendered_file()", bootstrap)
        self.assertIn("missing init-managed file:", bootstrap)
        self.assertIn("BLUEPRINT_INIT_FORCE=true make blueprint-init-repo", bootstrap)
        self.assertIn("infra_init_managed_skip_count", bootstrap)

    def test_init_repo_prunes_disabled_optional_scaffolding_on_first_init(self) -> None:
        init_python = _read("scripts/lib/blueprint/init_repo.py")
        init_contract_helpers = _read("scripts/lib/blueprint/init_repo_contract.py")
        self.assertIn("seed_consumer_owned_files", init_python)
        self.assertIn("prune_disabled_optional_scaffolding", init_contract_helpers)
        self.assertIn("consumer-owned seed already applied", init_contract_helpers)
        self.assertIn("expand_optional_module_path(", init_contract_helpers)

    def test_public_endpoints_smoke_accepts_list_manifest_kind_entries(self) -> None:
        smoke = _read("scripts/bin/infra/public_endpoints_smoke.sh")
        self.assertIn("grep -Eq '^[[:space:]]*kind: GatewayClass$'", smoke)
        self.assertIn("grep -Eq '^[[:space:]]*kind: Gateway$'", smoke)

    def test_public_endpoints_stackit_deploy_waits_for_gateway_api_crds(self) -> None:
        deploy = _read("scripts/bin/infra/public_endpoints_deploy.sh")
        destroy = _read("scripts/bin/infra/public_endpoints_destroy.sh")
        template = _read("scripts/templates/infra/bootstrap/infra/gitops/argocd/optional/public-endpoints.application.yaml.tmpl")

        self.assertIn("public_endpoints_wait_for_gateway_api_crds", deploy)
        self.assertIn('run_manifest_apply "$gateway_manifest_path"', deploy)
        self.assertIn("gateway_api_wait_status=", deploy)
        self.assertIn("public_endpoints_gateway_api_crd_wait_total", _read("scripts/lib/infra/public_endpoints.sh"))
        self.assertIn("public_endpoints_gateway_api_crds_available", destroy)
        self.assertNotIn("kind: GatewayClass", template)
        self.assertNotIn("kind: Gateway", template)

    def test_identity_aware_proxy_smoke_accepts_hostnames_block_fallback(self) -> None:
        smoke = _read("scripts/bin/infra/identity_aware_proxy_smoke.sh")
        self.assertIn("host_binding_check_status=", smoke)
        self.assertIn("grep -Eq '^[[:space:]]*hostnames:'", smoke)
        self.assertIn("hostnames_block_only", smoke)

    def test_docs_scripts_are_docusaurus_only(self) -> None:
        docs_install = _read("scripts/bin/docs/install.sh")
        docs_build = _read("scripts/bin/docs/build.sh")
        docs_run = _read("scripts/bin/docs/run.sh")
        docs_site = _read("scripts/lib/docs/site.sh")

        self.assertIn("source \"$ROOT_DIR/scripts/lib/docs/site.sh\"", docs_install)
        self.assertIn("source \"$ROOT_DIR/scripts/lib/docs/site.sh\"", docs_build)
        self.assertIn("source \"$ROOT_DIR/scripts/lib/docs/site.sh\"", docs_run)
        self.assertIn("docs_pnpm_install", docs_install)
        self.assertIn("docs_pnpm_build", docs_build)
        self.assertIn("docs_pnpm_start", docs_run)
        self.assertIn("require_command pnpm", docs_site)
        self.assertIn("docs_require_workspace()", docs_site)
        self.assertNotIn("markdown contract docs generated only", docs_build)
        self.assertNotIn("python http server", docs_run)

    def test_apps_bootstrap_keeps_only_canonical_app_dirs(self) -> None:
        apps_bootstrap = _read("scripts/bin/platform/apps/bootstrap.sh")
        self.assertIn('ensure_dir "$ROOT_DIR/apps/backend"', apps_bootstrap)
        self.assertIn('ensure_dir "$ROOT_DIR/apps/touchpoints"', apps_bootstrap)
        self.assertIn('ensure_dir "$ROOT_DIR/apps/catalog"', apps_bootstrap)
        self.assertNotIn('ensure_dir "$ROOT_DIR/apps/ingestion"', apps_bootstrap)

    def test_apps_version_baseline_pins_pinia_304(self) -> None:
        versions = _read("scripts/lib/platform/apps/versions.sh")
        baseline = _read("scripts/lib/platform/apps/versions.baseline.sh")
        manifest = _read("apps/catalog/manifest.yaml")
        versions_lock = _read("apps/catalog/versions.lock")

        self.assertIn('PINIA_VERSION="3.0.4"', versions)
        self.assertIn('PINIA_VERSION="3.0.4"', baseline)
        self.assertIn('pinia: 3.0.4', manifest)
        self.assertIn('PINIA_VERSION=3.0.4', versions_lock)

    def test_apps_version_baseline_pins_vue_router_504(self) -> None:
        versions = _read("scripts/lib/platform/apps/versions.sh")
        baseline = _read("scripts/lib/platform/apps/versions.baseline.sh")
        manifest = _read("apps/catalog/manifest.yaml")
        versions_lock = _read("apps/catalog/versions.lock")

        self.assertIn('VUE_ROUTER_VERSION="5.0.4"', versions)
        self.assertIn('VUE_ROUTER_VERSION="5.0.4"', baseline)
        self.assertIn('vue_router: 5.0.4', manifest)
        self.assertIn('VUE_ROUTER_VERSION=5.0.4', versions_lock)

    def test_crossplane_scaffold_is_placeholder_free(self) -> None:
        crossplane_kustomization = _read("infra/local/crossplane/kustomization.yaml")
        template_crossplane_kustomization = _read(
            "scripts/templates/infra/bootstrap/infra/local/crossplane/kustomization.yaml"
        )
        bootstrap = _read("scripts/bin/infra/bootstrap.sh")

        self.assertNotIn("provider-helm-placeholder.yaml", crossplane_kustomization)
        self.assertNotIn("provider-helm-placeholder.yaml", template_crossplane_kustomization)
        self.assertNotIn("provider-helm-placeholder.yaml", bootstrap)

    def test_module_destroy_scripts_execute_cleanup_paths(self) -> None:
        langfuse_destroy = _read("scripts/bin/infra/langfuse_destroy.sh")
        neo4j_destroy = _read("scripts/bin/infra/neo4j_destroy.sh")
        postgres_destroy = _read("scripts/bin/infra/postgres_destroy.sh")
        observability_destroy = _read("scripts/bin/infra/observability_destroy.sh")
        module_execution = _read("scripts/lib/infra/module_execution.sh")
        tooling = _read("scripts/lib/infra/tooling.sh")

        self.assertIn("run_manifest_delete()", tooling)
        self.assertIn("run_helm_uninstall()", tooling)
        self.assertIn("resolve_optional_module_execution", langfuse_destroy)
        self.assertIn("resolve_optional_module_execution", neo4j_destroy)
        self.assertIn("optional_module_destroy_foundation_contract", module_execution)
        self.assertIn("stackit_foundation_apply.sh", module_execution)
        self.assertIn('optional_module_destroy_foundation_contract "postgres"', postgres_destroy)
        self.assertIn("run_helm_uninstall", postgres_destroy)
        self.assertIn('resolve_optional_module_execution "observability" "destroy"', observability_destroy)
        self.assertIn("run_manifest_delete", observability_destroy)
        self.assertIn("run_helm_uninstall", observability_destroy)

    def test_dry_run_toggle_is_canonical(self) -> None:
        tooling = _read("scripts/lib/infra/tooling.sh")
        execution_model = _read("docs/blueprint/architecture/execution_model.md")
        publish_ghcr = _read("scripts/bin/platform/apps/publish_ghcr.sh")

        self.assertIn('${DRY_RUN:-true}', tooling)
        self.assertNotIn("BLUEPRINT_EXECUTE_TOOLING", tooling)
        self.assertIn("set DRY_RUN=false to execute", tooling)
        self.assertIn("`DRY_RUN` controls whether cloud/cluster tools are executed", execution_model)
        self.assertNotIn("BLUEPRINT_EXECUTE_TOOLING", execution_model)
        self.assertIn("Default mode is dry-run unless DRY_RUN=false.", publish_ghcr)

    def test_stackit_runtime_inventory_exports_are_redacted_by_default(self) -> None:
        inventory = _read("scripts/bin/infra/stackit_runtime_inventory.sh")
        self.assertIn("print_export_or_missing()", inventory)
        self.assertIn("STACKIT_RUNTIME_INVENTORY_INCLUDE_SENSITIVE", inventory)
        self.assertIn("# %s=<redacted>", inventory)
        self.assertIn("STACKIT_WORKFLOWS_API_TOKEN", inventory)

    def test_stackit_ci_setup_supports_dry_run_with_missing_secrets(self) -> None:
        stackit_ci_setup = _read("scripts/bin/infra/stackit_github_ci_setup.sh")
        self.assertIn("[dry-run] required secret value missing from environment", stackit_ci_setup)
        self.assertIn("stackit_ci_github_setup_missing_secret_count", stackit_ci_setup)
        self.assertIn('write_state_file "stackit_ci_github_setup"', stackit_ci_setup)

    def test_stackit_runtime_prerequisites_wait_for_kube_api_readiness(self) -> None:
        runtime_prereqs = _read("scripts/bin/infra/stackit_runtime_prerequisites.sh")
        k8s_wait = _read("scripts/lib/infra/k8s_wait.sh")

        self.assertIn('source "$ROOT_DIR/scripts/lib/infra/k8s_wait.sh"', runtime_prereqs)
        self.assertIn('wait_for_kube_api_ready "$kubeconfig_output" "$(k8s_timeout_seconds slow)"', runtime_prereqs)
        self.assertIn("kube_api_server=", runtime_prereqs)
        self.assertIn("kube_api_status=", runtime_prereqs)
        self.assertIn("K8S_TIMEOUT_SLOW_SECONDS", runtime_prereqs)
        self.assertIn("k8s_kubeconfig_server_url()", k8s_wait)
        self.assertIn("wait_for_kube_api_ready()", k8s_wait)
        self.assertIn("k8s_api_readiness_wait_seconds", k8s_wait)
        self.assertIn("k8s_hostname_resolution_attempts", k8s_wait)

    def test_metrics_are_enabled_for_core_wrapper_scripts(self) -> None:
        metric_files = [
            "scripts/bin/blueprint/init_repo.sh",
            "scripts/bin/blueprint/init_repo_interactive.sh",
            "scripts/bin/blueprint/resync_consumer_seeds.sh",
            "scripts/bin/blueprint/check_placeholders.sh",
            "scripts/bin/blueprint/template_smoke.sh",
            "scripts/bin/blueprint/bootstrap.sh",
            "scripts/bin/blueprint/clean_generated.sh",
            "scripts/bin/blueprint/render_makefile.sh",
            "scripts/bin/blueprint/render_module_wrapper_skeletons.sh",
            "scripts/bin/infra/bootstrap.sh",
            "scripts/bin/infra/destroy_disabled_modules.sh",
            "scripts/bin/infra/validate.sh",
            "scripts/bin/infra/provision.sh",
            "scripts/bin/infra/deploy.sh",
            "scripts/bin/infra/smoke.sh",
            "scripts/bin/infra/provision_deploy.sh",
            "scripts/bin/infra/audit_version.sh",
            "scripts/bin/infra/observability_plan.sh",
            "scripts/bin/infra/observability_apply.sh",
            "scripts/bin/infra/observability_deploy.sh",
            "scripts/bin/infra/observability_smoke.sh",
            "scripts/bin/infra/observability_destroy.sh",
            "scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh",
            "scripts/bin/infra/stackit_foundation_refresh_kubeconfig.sh",
            "scripts/bin/infra/stackit_bootstrap_preflight.sh",
            "scripts/bin/infra/stackit_bootstrap_plan.sh",
            "scripts/bin/infra/stackit_bootstrap_apply.sh",
            "scripts/bin/infra/stackit_bootstrap_destroy.sh",
            "scripts/bin/infra/stackit_foundation_preflight.sh",
            "scripts/bin/infra/stackit_foundation_plan.sh",
            "scripts/bin/infra/stackit_foundation_apply.sh",
            "scripts/bin/infra/stackit_foundation_destroy.sh",
            "scripts/bin/infra/stackit_foundation_seed_runtime_secret.sh",
            "scripts/bin/infra/stackit_destroy_all.sh",
            "scripts/bin/infra/stackit_runtime_prerequisites.sh",
            "scripts/bin/infra/stackit_runtime_inventory.sh",
            "scripts/bin/infra/stackit_runtime_deploy.sh",
            "scripts/bin/infra/stackit_smoke_foundation.sh",
            "scripts/bin/infra/stackit_smoke_runtime.sh",
            "scripts/bin/infra/stackit_provision_deploy.sh",
            "scripts/bin/infra/argocd_topology_render.sh",
            "scripts/bin/infra/argocd_topology_validate.sh",
            "scripts/bin/infra/doctor.sh",
            "scripts/bin/infra/context.sh",
            "scripts/bin/infra/status.sh",
            "scripts/bin/infra/status_json.sh",
            "scripts/bin/infra/prereqs.sh",
            "scripts/bin/infra/help_reference.sh",
            "scripts/bin/infra/stackit_github_ci_setup.sh",
            "scripts/bin/platform/apps/audit_versions.sh",
            "scripts/bin/platform/apps/audit_versions_cached.sh",
            "scripts/bin/platform/apps/bootstrap.sh",
            "scripts/bin/platform/apps/publish_ghcr.sh",
            "scripts/bin/platform/apps/smoke.sh",
            "scripts/bin/docs/install.sh",
            "scripts/bin/docs/run.sh",
            "scripts/bin/docs/build.sh",
            "scripts/bin/docs/smoke.sh",
            "scripts/bin/platform/test/unit_all.sh",
            "scripts/bin/platform/test/integration_all.sh",
            "scripts/bin/platform/test/contracts_all.sh",
            "scripts/bin/platform/test/e2e_all_local.sh",
            "scripts/bin/infra/langfuse_plan.sh",
            "scripts/bin/infra/postgres_plan.sh",
            "scripts/bin/infra/neo4j_plan.sh",
            "scripts/bin/infra/stackit_workflows_plan.sh",
            "scripts/bin/infra/object_storage_plan.sh",
            "scripts/bin/infra/object_storage_apply.sh",
            "scripts/bin/infra/object_storage_smoke.sh",
            "scripts/bin/infra/object_storage_destroy.sh",
            "scripts/bin/infra/rabbitmq_plan.sh",
            "scripts/bin/infra/rabbitmq_apply.sh",
            "scripts/bin/infra/rabbitmq_smoke.sh",
            "scripts/bin/infra/rabbitmq_destroy.sh",
            "scripts/bin/infra/dns_plan.sh",
            "scripts/bin/infra/dns_apply.sh",
            "scripts/bin/infra/dns_smoke.sh",
            "scripts/bin/infra/dns_destroy.sh",
            "scripts/bin/infra/public_endpoints_plan.sh",
            "scripts/bin/infra/public_endpoints_apply.sh",
            "scripts/bin/infra/public_endpoints_smoke.sh",
            "scripts/bin/infra/public_endpoints_destroy.sh",
            "scripts/bin/infra/secrets_manager_plan.sh",
            "scripts/bin/infra/secrets_manager_apply.sh",
            "scripts/bin/infra/secrets_manager_smoke.sh",
            "scripts/bin/infra/secrets_manager_destroy.sh",
            "scripts/bin/infra/kms_plan.sh",
            "scripts/bin/infra/kms_apply.sh",
            "scripts/bin/infra/kms_smoke.sh",
            "scripts/bin/infra/kms_destroy.sh",
            "scripts/bin/infra/identity_aware_proxy_plan.sh",
            "scripts/bin/infra/identity_aware_proxy_apply.sh",
            "scripts/bin/infra/identity_aware_proxy_smoke.sh",
            "scripts/bin/infra/identity_aware_proxy_destroy.sh",
            "scripts/bin/infra/audit_version_cached.sh",
        ]
        for path in metric_files:
            self.assertIn("start_script_metric_trap", _read(path), msg=f"missing metric trap in {path}")
        self.assertIn("pytest_lane_duration_seconds", _read("scripts/lib/platform/testing.sh"))

    def test_touchpoints_test_lanes_support_frontend_frameworks(self) -> None:
        testing = _read("scripts/lib/platform/testing.sh")
        unit = _read("scripts/bin/platform/touchpoints/test_unit.sh")
        integration = _read("scripts/bin/platform/touchpoints/test_integration.sh")
        contracts = _read("scripts/bin/platform/touchpoints/test_contracts.sh")
        e2e = _read("scripts/bin/platform/touchpoints/test_e2e.sh")

        self.assertIn("_discover_pnpm_script_project_entries()", testing)
        self.assertIn("run_touchpoints_pnpm_lane()", testing)
        self.assertIn("pnpm_lane_duration_seconds", testing)
        self.assertIn('"node_modules"', testing)
        self.assertIn("script_mode=per_package", testing)

        self.assertIn("run_touchpoints_pnpm_lane", unit)
        self.assertIn('"touchpoints unit"', unit)
        self.assertIn('"vitest"', unit)
        self.assertIn('"test:unit"', unit)
        self.assertNotIn('run_python_pytest_lane "touchpoints unit"', unit)

        self.assertIn("run_touchpoints_pnpm_lane", integration)
        self.assertIn('"touchpoints integration"', integration)
        self.assertIn('"vitest"', integration)
        self.assertIn('"test:integration"', integration)
        self.assertNotIn('run_python_pytest_lane "touchpoints integration"', integration)

        self.assertIn("run_touchpoints_pnpm_lane", contracts)
        self.assertIn('"touchpoints contracts"', contracts)
        self.assertIn('"pact"', contracts)
        self.assertIn('"test:pact"', contracts)
        self.assertIn('run_python_pytest_lane "touchpoints contracts"', contracts)

        self.assertIn("run_touchpoints_pnpm_lane", e2e)
        self.assertIn('"touchpoints e2e"', e2e)
        self.assertIn('"playwright"', e2e)
        self.assertIn('"test:playwright"', e2e)
        self.assertNotIn('run_python_pytest_lane "touchpoints e2e"', e2e)

    def test_blueprint_template_init_assets_exist(self) -> None:
        init_script = _read("scripts/bin/blueprint/init_repo.sh")
        init_interactive_script = _read("scripts/bin/blueprint/init_repo_interactive.sh")
        init_python = _read("scripts/lib/blueprint/init_repo.py")
        smoke_script = _read("scripts/bin/blueprint/template_smoke.sh")
        placeholder_script = _read("scripts/bin/blueprint/check_placeholders.sh")
        init_env_defaults = _read("blueprint/repo.init.env")
        init_env_secrets_example = _read("blueprint/repo.init.secrets.example.env")

        self.assertIn("blueprint_init_repo", init_script)
        self.assertIn("--dry-run", init_script)
        self.assertIn("--force", init_python)
        self.assertIn("BLUEPRINT_INIT_DRY_RUN", init_script)
        self.assertIn("blueprint_init_force_var_name", init_script)
        self.assertIn("blueprint_load_env_defaults", init_script)
        self.assertIn("BLUEPRINT_REPO_NAME", init_script)
        self.assertIn("BLUEPRINT_GITHUB_ORG", init_script)
        self.assertIn("BLUEPRINT_GITHUB_REPO", init_script)
        self.assertIn("BLUEPRINT_DEFAULT_BRANCH", init_script)
        self.assertIn("blueprint_init_repo_interactive", init_interactive_script)
        self.assertIn("BLUEPRINT_INIT_DRY_RUN", init_interactive_script)
        self.assertIn("blueprint_init_force_var_name", init_interactive_script)
        self.assertIn("prompt_with_default", init_interactive_script)
        self.assertIn("contract_runtime.sh", init_script)
        self.assertIn("contract_runtime.sh", init_interactive_script)
        self.assertIn("contract_runtime.sh", placeholder_script)
        self.assertIn("blueprint_load_env_defaults", placeholder_script)
        self.assertIn('scripts/bin/blueprint/render_makefile.sh', init_script)
        self.assertIn("_render_contract", init_python)
        self.assertIn("_render_docusaurus_config", init_python)
        self.assertIn("_ensure_defaults_env_file", init_python)
        self.assertIn("_ensure_secrets_example_env_file", init_python)
        self.assertIn("_ensure_local_secrets_env_file", init_python)
        self.assertIn("init_repo_contract", init_python)
        self.assertIn("init_repo_renderers", init_python)
        self.assertIn("init_repo_env", init_python)
        self.assertIn("init_repo_io", init_python)
        self.assertIn("--dry-run", init_python)
        self.assertIn("blueprint_template_smoke", smoke_script)
        self.assertIn("make blueprint-bootstrap", smoke_script)
        self.assertIn("make blueprint-check-placeholders", smoke_script)
        self.assertIn("make infra-provision-deploy", smoke_script)
        self.assertIn("make infra-status-json", smoke_script)
        self.assertIn("blueprint_sanitize_init_placeholder_defaults", smoke_script)
        self.assertIn("BLUEPRINT_TEMPLATE_SMOKE_SCENARIO", smoke_script)
        self.assertIn("assert_template_smoke_repo_state", smoke_script)
        self.assertIn("blueprint_check_placeholders", placeholder_script)
        self.assertIn("BLUEPRINT_GITHUB_ORG", placeholder_script)
        self.assertIn("BLUEPRINT_REPO_NAME=", init_env_defaults)
        self.assertIn("BLUEPRINT_GITHUB_ORG=", init_env_defaults)
        self.assertIn("BLUEPRINT_GITHUB_REPO=", init_env_defaults)
        self.assertIn("BLUEPRINT_DEFAULT_BRANCH=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_REGION=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_TENANT_SLUG=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_PLATFORM_SLUG=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_PROJECT_ID=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_TFSTATE_BUCKET=", init_env_defaults)
        self.assertIn("BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX=", init_env_defaults)
        self.assertIn("STACKIT_SERVICE_ACCOUNT_KEY=", init_env_secrets_example)
        self.assertIn("STACKIT_TFSTATE_ACCESS_KEY_ID=", init_env_secrets_example)
        self.assertIn("defaults_env_file: blueprint/repo.init.env", _read("blueprint/contract.yaml"))
        self.assertIn(
            "secrets_example_env_file: blueprint/repo.init.secrets.example.env",
            _read("blueprint/contract.yaml"),
        )
        self.assertIn("secrets_env_file: blueprint/repo.init.secrets.env", _read("blueprint/contract.yaml"))
        self.assertIn("force_env_var: BLUEPRINT_INIT_FORCE", _read("blueprint/contract.yaml"))
        self.assertIn("consumer_init:", _read("blueprint/contract.yaml"))
        self.assertIn("ownership_path_classes:", _read("blueprint/contract.yaml"))

    def test_ci_workflows_and_docs_exist(self) -> None:
        ci_workflow = _read(".github/workflows/ci.yml")
        consumer_ci_template = _read("scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl")
        shared_ci_action = _read(".github/actions/prepare-blueprint-ci/action.yml")
        hooks_fast = _read("scripts/bin/quality/hooks_fast.sh")
        source_codeowners = _read(".github/CODEOWNERS")
        source_pr_template = _read(".github/pull_request_template.md")
        source_bug_template = _read(".github/ISSUE_TEMPLATE/bug_report.yml")
        consumer_codeowners_template = _read("scripts/templates/consumer/init/.github/CODEOWNERS.tmpl")
        consumer_pr_template = _read("scripts/templates/consumer/init/.github/pull_request_template.md.tmpl")
        consumer_bug_template = _read("scripts/templates/consumer/init/.github/ISSUE_TEMPLATE/bug_report.yml.tmpl")
        docs_readme = _read("docs/README.md")
        sidebars = _read("docs/sidebars.js")
        docusaurus_config = _read("docs/docusaurus.config.js")

        self.assertIn("Prepare Blueprint CI", shared_ci_action)
        self.assertIn("make blueprint-bootstrap", shared_ci_action)
        self.assertIn("make infra-bootstrap", shared_ci_action)
        self.assertIn("platform-blueprint-maintainers", source_codeowners)
        self.assertIn("Describe the blueprint change.", source_pr_template)
        self.assertIn("Blueprint Bug Report", source_bug_template)
        self.assertIn("generated repository", consumer_codeowners_template)
        self.assertIn("Describe the project change.", consumer_pr_template)
        self.assertIn("Project Bug Report", consumer_bug_template)
        self.assertIn("blueprint-quality:", ci_workflow)
        self.assertIn("generated-consumer-smoke:", ci_workflow)
        self.assertIn('run_cmd make -C "$ROOT_DIR" infra-validate', hooks_fast)
        self.assertIn('pytest -q tests', ci_workflow)
        self.assertNotIn('pytest -q tests/tooling', ci_workflow)
        self.assertIn('Prepare shared CI baseline', ci_workflow)
        self.assertIn('uses: ./.github/actions/prepare-blueprint-ci', ci_workflow)
        self.assertIn('Run fast quality gate', ci_workflow)
        self.assertIn('Run strict audit gate', ci_workflow)
        self.assertIn('Run pre-push hook stage', ci_workflow)
        self.assertIn('pre-commit run --hook-stage pre-push --all-files', ci_workflow)
        self.assertEqual(ci_workflow.count('make quality-hooks-fast'), 1)
        self.assertEqual(ci_workflow.count('make quality-hooks-strict'), 1)
        self.assertIn('Smoke generated consumer baseline', ci_workflow)
        self.assertIn('BLUEPRINT_TEMPLATE_SMOKE_SCENARIO=local-lite-baseline', ci_workflow)
        self.assertIn('make blueprint-template-smoke', ci_workflow)
        self.assertIn('BLUEPRINT_PROFILE=local-lite OBSERVABILITY_ENABLED=false make apps-bootstrap', ci_workflow)
        self.assertIn('BLUEPRINT_PROFILE=local-lite OBSERVABILITY_ENABLED=false make apps-smoke', ci_workflow)
        self.assertIn('make docs-build', ci_workflow)
        self.assertIn('make docs-smoke', ci_workflow)
        self.assertIn('make test-unit-all', ci_workflow)
        self.assertIn('make test-integration-all', ci_workflow)
        self.assertIn('make test-contracts-all', ci_workflow)
        self.assertIn('make test-e2e-all-local', ci_workflow)
        self.assertNotIn('Shell script lint', ci_workflow)
        self.assertNotIn('make apps-audit-versions', ci_workflow)
        self.assertEqual(consumer_ci_template.count('uses: ./.github/actions/prepare-blueprint-ci'), 2)
        self.assertIn('Run fast quality gate', consumer_ci_template)
        self.assertIn('make quality-hooks-fast', consumer_ci_template)
        self.assertIn('Run strict audit gate', consumer_ci_template)
        self.assertIn('make quality-hooks-strict', consumer_ci_template)
        self.assertIn('[Platform Quickstart](platform/consumer/quickstart.md)', docs_readme)
        self.assertIn('[Endpoint Exposure Model](platform/consumer/endpoint_exposure_model.md)', docs_readme)
        self.assertIn('[Protected API Routes](platform/consumer/protected_api_routes.md)', docs_readme)
        self.assertIn('[Platform Troubleshooting](platform/consumer/troubleshooting.md)', docs_readme)
        self.assertIn('dirName: "blueprint"', sidebars)
        self.assertIn('platformSidebar', sidebars)
        self.assertIn('id: "platform/README"', sidebars)
        self.assertIn('dirName: "platform/consumer"', sidebars)
        self.assertIn('dirName: "platform/modules"', sidebars)
        self.assertIn('dirName: "reference"', sidebars)
        self.assertIn('"blueprint/**/*.md"', docusaurus_config)
        self.assertIn('"platform/**/*.md"', docusaurus_config)
        self.assertNotIn('docsPluginId: "platform"', docusaurus_config)

    def test_blueprint_init_python_updates_contract_and_docs(self) -> None:
        init_python_path = REPO_ROOT / "scripts/lib/blueprint/init_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "docs").mkdir(parents=True, exist_ok=True)
            (tmp_root / ".github/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / ".github/ISSUE_TEMPLATE").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/gitops/argocd/root").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/gitops/argocd/environments/dev").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/gitops/argocd/overlays/local").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/foundation/env").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/state-backend").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/foundation/state-backend").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/.github/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/.github/ISSUE_TEMPLATE").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/docs").mkdir(parents=True, exist_ok=True)
            (tmp_root / "blueprint/modules").mkdir(parents=True, exist_ok=True)
            (tmp_root / "dags").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/modules/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / "tests/infra/modules/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / "blueprint/contract.yaml").write_text(
                _read("blueprint/contract.yaml"),
                encoding="utf-8",
            )
            (tmp_root / "README.md").write_text("source readme", encoding="utf-8")
            (tmp_root / "AGENTS.md").write_text("source agents", encoding="utf-8")
            (tmp_root / "AGENTS.backlog.md").write_text("source backlog", encoding="utf-8")
            (tmp_root / "AGENTS.decisions.md").write_text("source decisions", encoding="utf-8")
            (tmp_root / "docs/README.md").write_text("source docs index", encoding="utf-8")
            (tmp_root / ".github/CODEOWNERS").write_text("source codeowners", encoding="utf-8")
            (tmp_root / ".github/pull_request_template.md").write_text("source pr template", encoding="utf-8")
            (tmp_root / ".github/ISSUE_TEMPLATE/bug_report.yml").write_text("source bug template", encoding="utf-8")
            (tmp_root / ".github/ISSUE_TEMPLATE/feature_request.yml").write_text(
                "source feature template",
                encoding="utf-8",
            )
            (tmp_root / ".github/ISSUE_TEMPLATE/config.yml").write_text("blank_issues_enabled: false\n", encoding="utf-8")
            (tmp_root / ".github/workflows/ci.yml").write_text("source ci", encoding="utf-8")
            (tmp_root / "tests/blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "tests/docs").mkdir(parents=True, exist_ok=True)
            (tmp_root / "tests/blueprint/placeholder.py").write_text("source blueprint tests", encoding="utf-8")
            (tmp_root / "tests/docs/placeholder.py").write_text("source docs tests", encoding="utf-8")
            (tmp_root / "dags/.airflowignore").write_text("apps/**\n", encoding="utf-8")
            (tmp_root / "infra/cloud/stackit/terraform/modules/workflows/main.tf").write_text("", encoding="utf-8")
            (tmp_root / "tests/infra/modules/workflows/README.md").write_text("workflow test", encoding="utf-8")
            for template_path in (
                "README.md.tmpl",
                "AGENTS.md.tmpl",
                "AGENTS.backlog.md.tmpl",
                "AGENTS.decisions.md.tmpl",
                "docs/README.md.tmpl",
                ".github/CODEOWNERS.tmpl",
                ".github/pull_request_template.md.tmpl",
                ".github/ISSUE_TEMPLATE/bug_report.yml.tmpl",
                ".github/ISSUE_TEMPLATE/feature_request.yml.tmpl",
                ".github/ISSUE_TEMPLATE/config.yml.tmpl",
                ".github/workflows/ci.yml.tmpl",
            ):
                source_path = REPO_ROOT / "scripts/templates/consumer/init" / template_path
                target_path = tmp_root / "scripts/templates/consumer/init" / template_path
                target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
            for template_path in INIT_MANAGED_RESTORE_TEMPLATE_PATHS:
                _copy_repo_text_path(tmp_root, template_path)
            for source_path in (REPO_ROOT / "blueprint/modules").glob("*/module.contract.yaml"):
                target_path = tmp_root / source_path.relative_to(REPO_ROOT)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
            (tmp_root / "docs/docusaurus.config.js").write_text(
                _read("docs/docusaurus.config.js"),
                encoding="utf-8",
            )
            (tmp_root / "infra/gitops/argocd/root/applicationset-platform-environments.yaml").write_text(
                _read("infra/gitops/argocd/root/applicationset-platform-environments.yaml"),
                encoding="utf-8",
            )
            (tmp_root / "infra/gitops/argocd/environments/dev/platform-application.yaml").write_text(
                _read("infra/gitops/argocd/environments/dev/platform-application.yaml"),
                encoding="utf-8",
            )
            (tmp_root / "infra/gitops/argocd/overlays/local/application-platform-local.yaml").write_text(
                _read("infra/gitops/argocd/overlays/local/application-platform-local.yaml"),
                encoding="utf-8",
            )
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars").write_text(
                _read("infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars"),
                encoding="utf-8",
            )
            (tmp_root / "infra/cloud/stackit/terraform/foundation/env/dev.tfvars").write_text(
                _read("infra/cloud/stackit/terraform/foundation/env/dev.tfvars"),
                encoding="utf-8",
            )
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl").write_text(
                _read("infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl"),
                encoding="utf-8",
            )
            (tmp_root / "infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl").write_text(
                _read("infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl"),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(init_python_path),
                    "--repo-root",
                    str(tmp_root),
                    "--repo-name",
                    "acme-platform",
                    "--github-org",
                    "acme",
                    "--github-repo",
                    "acme-platform",
                    "--default-branch",
                    "main",
                    "--docs-title",
                    "Acme Platform Blueprint",
                    "--docs-tagline",
                    "Acme reusable platform blueprint",
                    "--stackit-region",
                    "eu02",
                    "--stackit-tenant-slug",
                    "acme",
                    "--stackit-platform-slug",
                    "marketplace",
                    "--stackit-project-id",
                    "acme-marketplace-dev",
                    "--stackit-tfstate-bucket",
                    "acme-marketplace-tf-state",
                    "--stackit-tfstate-key-prefix",
                    "iac/tfstate",
                ],
                cwd=REPO_ROOT,
                env={
                    **os.environ,
                    "POSTGRES_ENABLED": "true",
                    "OBJECT_STORAGE_ENABLED": "true",
                    "PUBLIC_ENDPOINTS_ENABLED": "true",
                    "IDENTITY_AWARE_PROXY_ENABLED": "true",
                },
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            updated_contract = (tmp_root / "blueprint/contract.yaml").read_text(encoding="utf-8")
            updated_docs_config = (tmp_root / "docs/docusaurus.config.js").read_text(encoding="utf-8")
            updated_argocd_root = (
                tmp_root / "infra/gitops/argocd/root/applicationset-platform-environments.yaml"
            ).read_text(encoding="utf-8")
            updated_argocd_environment_dev = (
                tmp_root / "infra/gitops/argocd/environments/dev/platform-application.yaml"
            ).read_text(encoding="utf-8")
            updated_argocd_local_application = (
                tmp_root / "infra/gitops/argocd/overlays/local/application-platform-local.yaml"
            ).read_text(encoding="utf-8")
            updated_bootstrap_tfvars = (
                tmp_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars"
            ).read_text(encoding="utf-8")
            updated_foundation_tfvars = (
                tmp_root / "infra/cloud/stackit/terraform/foundation/env/dev.tfvars"
            ).read_text(encoding="utf-8")
            updated_bootstrap_backend = (
                tmp_root / "infra/cloud/stackit/terraform/bootstrap/state-backend/dev.hcl"
            ).read_text(encoding="utf-8")
            updated_foundation_backend = (
                tmp_root / "infra/cloud/stackit/terraform/foundation/state-backend/dev.hcl"
            ).read_text(encoding="utf-8")
            defaults_env = (tmp_root / "blueprint/repo.init.env").read_text(encoding="utf-8")
            local_secrets_env = (tmp_root / "blueprint/repo.init.secrets.env").read_text(encoding="utf-8")
            seeded_readme = (tmp_root / "README.md").read_text(encoding="utf-8")
            seeded_docs_readme = (tmp_root / "docs/README.md").read_text(encoding="utf-8")
            seeded_codeowners = (tmp_root / ".github/CODEOWNERS").read_text(encoding="utf-8")
            seeded_pr_template = (tmp_root / ".github/pull_request_template.md").read_text(encoding="utf-8")
            seeded_bug_template = (tmp_root / ".github/ISSUE_TEMPLATE/bug_report.yml").read_text(encoding="utf-8")
            optional_modules_section = _extract_yaml_section(updated_contract.splitlines(), "optional_modules")
            optional_module_entries = _extract_yaml_section(optional_modules_section, "modules")
            self.assertIn("name: acme-platform", updated_contract)
            self.assertIn("repo_mode: generated-consumer", updated_contract)
            self.assertIn("default_branch: main", updated_contract)
            self.assertEqual(_extract_yaml_scalar(_extract_yaml_section(optional_module_entries, "postgres"), "enabled_by_default"), "true")
            self.assertEqual(
                _extract_yaml_scalar(_extract_yaml_section(optional_module_entries, "object-storage"), "enabled_by_default"),
                "true",
            )
            self.assertEqual(
                _extract_yaml_scalar(_extract_yaml_section(optional_module_entries, "public-endpoints"), "enabled_by_default"),
                "true",
            )
            self.assertEqual(
                _extract_yaml_scalar(
                    _extract_yaml_section(optional_module_entries, "identity-aware-proxy"),
                    "enabled_by_default",
                ),
                "true",
            )
            self.assertIn('title: "Acme Platform Blueprint"', updated_docs_config)
            self.assertIn('tagline: "Acme reusable platform blueprint"', updated_docs_config)
            self.assertIn('organizationName: "acme"', updated_docs_config)
            self.assertIn('projectName: "acme-platform"', updated_docs_config)
            self.assertIn(
                'editUrl: "https://github.com/acme/acme-platform/edit/main/docs/"',
                updated_docs_config,
            )
            self.assertIn("repoURL: https://github.com/acme/acme-platform.git", updated_argocd_root)
            self.assertIn(
                "repoURL: https://github.com/acme/acme-platform.git",
                updated_argocd_environment_dev,
            )
            self.assertIn(
                "repoURL: https://github.com/acme/acme-platform.git",
                updated_argocd_local_application,
            )
            self.assertIn('stackit_region   = "eu02"', updated_bootstrap_tfvars)
            self.assertIn('tenant_slug      = "acme"', updated_bootstrap_tfvars)
            self.assertIn('platform_slug    = "marketplace"', updated_bootstrap_tfvars)
            self.assertIn('stackit_project_id = "acme-marketplace-dev"', updated_bootstrap_tfvars)
            self.assertNotIn("tfstate_bucket_name", updated_bootstrap_tfvars)
            self.assertIn('state_key_prefix = "iac/tfstate"', updated_bootstrap_tfvars)
            self.assertIn('stackit_project_id = "acme-marketplace-dev"', updated_foundation_tfvars)
            self.assertIn('stackit_region     = "eu02"', updated_foundation_tfvars)
            self.assertIn('bucket       = "acme-marketplace-tf-state"', updated_bootstrap_backend)
            self.assertIn('key          = "iac/tfstate/dev/bootstrap.tfstate"', updated_bootstrap_backend)
            self.assertIn('region       = "eu02"', updated_bootstrap_backend)
            self.assertIn('s3 = "https://object.storage.eu02.onstackit.cloud"', updated_bootstrap_backend)
            self.assertIn('bucket       = "acme-marketplace-tf-state"', updated_foundation_backend)
            self.assertIn('key          = "iac/tfstate/dev/foundation.tfstate"', updated_foundation_backend)
            self.assertIn('region       = "eu02"', updated_foundation_backend)
            self.assertIn('s3 = "https://object.storage.eu02.onstackit.cloud"', updated_foundation_backend)
            self.assertIn("BLUEPRINT_REPO_NAME=acme-platform", defaults_env)
            self.assertIn("BLUEPRINT_DOCS_TITLE='Acme Platform Blueprint'", defaults_env)
            self.assertIn("POSTGRES_ENABLED=true", defaults_env)
            self.assertIn("OBJECT_STORAGE_ENABLED=true", defaults_env)
            self.assertIn("PUBLIC_ENDPOINTS_ENABLED=true", defaults_env)
            self.assertIn("IDENTITY_AWARE_PROXY_ENABLED=true", defaults_env)
            self.assertIn("POSTGRES_DB_NAME=", local_secrets_env)
            self.assertIn("KEYCLOAK_CLIENT_ID=", local_secrets_env)
            self.assertIn("platform project created from the STACKIT Platform Blueprint", seeded_readme)
            self.assertIn("Blueprint Reference Track", seeded_docs_readme)
            self.assertIn("generated repository", seeded_codeowners)
            self.assertIn("Describe the project change.", seeded_pr_template)
            self.assertIn("Project Bug Report", seeded_bug_template)
            self.assertFalse((tmp_root / "tests/blueprint").exists())
            self.assertFalse((tmp_root / "tests/docs").exists())
            self.assertFalse((tmp_root / "dags").exists())
            self.assertFalse((tmp_root / "infra/cloud/stackit/terraform/modules/workflows").exists())
            self.assertFalse((tmp_root / "tests/infra/modules/workflows").exists())

            (tmp_root / "docs/docusaurus.config.js").unlink()
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars").unlink()

            restore_result = subprocess.run(
                [
                    sys.executable,
                    str(init_python_path),
                    "--repo-root",
                    str(tmp_root),
                    "--repo-name",
                    "acme-platform",
                    "--github-org",
                    "acme",
                    "--github-repo",
                    "acme-platform",
                    "--default-branch",
                    "main",
                    "--docs-title",
                    "Acme Platform Blueprint",
                    "--docs-tagline",
                    "Acme reusable platform blueprint",
                    "--stackit-region",
                    "eu02",
                    "--stackit-tenant-slug",
                    "acme",
                    "--stackit-platform-slug",
                    "marketplace",
                    "--stackit-project-id",
                    "acme-marketplace-dev",
                    "--stackit-tfstate-bucket",
                    "acme-marketplace-tf-state",
                    "--stackit-tfstate-key-prefix",
                    "iac/tfstate",
                    "--force",
                ],
                cwd=REPO_ROOT,
                env={
                    **os.environ,
                    "POSTGRES_ENABLED": "true",
                    "OBJECT_STORAGE_ENABLED": "true",
                    "PUBLIC_ENDPOINTS_ENABLED": "true",
                    "IDENTITY_AWARE_PROXY_ENABLED": "true",
                },
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(restore_result.returncode, 0, msg=restore_result.stdout + restore_result.stderr)
            self.assertIn('title: "Acme Platform Blueprint"', (tmp_root / "docs/docusaurus.config.js").read_text(encoding="utf-8"))
            self.assertIn(
                'stackit_region   = "eu02"',
                (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env/dev.tfvars").read_text(encoding="utf-8"),
            )

    def test_blueprint_init_python_dry_run_does_not_mutate_files(self) -> None:
        init_python_path = REPO_ROOT / "scripts/lib/blueprint/init_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "docs").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/.github/workflows").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/.github/ISSUE_TEMPLATE").mkdir(parents=True, exist_ok=True)
            (tmp_root / "scripts/templates/consumer/init/docs").mkdir(parents=True, exist_ok=True)
            contract_original = _read("blueprint/contract.yaml")
            docs_original = _read("docs/docusaurus.config.js")
            (tmp_root / "blueprint/contract.yaml").write_text(contract_original, encoding="utf-8")
            (tmp_root / "docs/docusaurus.config.js").write_text(docs_original, encoding="utf-8")
            for template_path in (
                "README.md.tmpl",
                "AGENTS.md.tmpl",
                "AGENTS.backlog.md.tmpl",
                "AGENTS.decisions.md.tmpl",
                "docs/README.md.tmpl",
                ".github/CODEOWNERS.tmpl",
                ".github/pull_request_template.md.tmpl",
                ".github/ISSUE_TEMPLATE/bug_report.yml.tmpl",
                ".github/ISSUE_TEMPLATE/feature_request.yml.tmpl",
                ".github/ISSUE_TEMPLATE/config.yml.tmpl",
                ".github/workflows/ci.yml.tmpl",
            ):
                source_path = REPO_ROOT / "scripts/templates/consumer/init" / template_path
                target_path = tmp_root / "scripts/templates/consumer/init" / template_path
                target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
            for template_path in INIT_MANAGED_RESTORE_TEMPLATE_PATHS:
                _copy_repo_text_path(tmp_root, template_path)

            result = subprocess.run(
                [
                    sys.executable,
                    str(init_python_path),
                    "--repo-root",
                    str(tmp_root),
                    "--repo-name",
                    "acme-platform",
                    "--github-org",
                    "acme",
                    "--github-repo",
                    "acme-platform",
                    "--default-branch",
                    "main",
                    "--docs-title",
                    "Acme Platform Blueprint",
                    "--docs-tagline",
                    "Acme reusable platform blueprint",
                    "--stackit-region",
                    "eu02",
                    "--stackit-tenant-slug",
                    "acme",
                    "--stackit-platform-slug",
                    "marketplace",
                    "--stackit-project-id",
                    "acme-marketplace-dev",
                    "--stackit-tfstate-bucket",
                    "acme-marketplace-tf-state",
                    "--stackit-tfstate-key-prefix",
                    "iac/tfstate",
                    "--dry-run",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("[dry-run] summary:", result.stdout)
            self.assertIn("created:", result.stdout)
            self.assertEqual((tmp_root / "blueprint/contract.yaml").read_text(encoding="utf-8"), contract_original)
            self.assertEqual((tmp_root / "docs/docusaurus.config.js").read_text(encoding="utf-8"), docs_original)
            self.assertFalse((tmp_root / "blueprint/repo.init.secrets.env").exists())

    def test_blueprint_init_python_requires_force_for_generated_consumer_repo(self) -> None:
        init_python_path = REPO_ROOT / "scripts/lib/blueprint/init_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            contract_content = _read("blueprint/contract.yaml").replace("repo_mode: template-source", "repo_mode: generated-consumer", 1)
            (tmp_root / "blueprint/contract.yaml").write_text(contract_content, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(init_python_path),
                    "--repo-root",
                    str(tmp_root),
                    "--repo-name",
                    "acme-platform",
                    "--github-org",
                    "acme",
                    "--github-repo",
                    "acme-platform",
                    "--default-branch",
                    "main",
                    "--docs-title",
                    "Acme Platform Blueprint",
                    "--docs-tagline",
                    "Acme reusable platform blueprint",
                    "--stackit-region",
                    "eu02",
                    "--stackit-tenant-slug",
                    "acme",
                    "--stackit-platform-slug",
                    "marketplace",
                    "--stackit-project-id",
                    "acme-marketplace-dev",
                    "--stackit-tfstate-bucket",
                    "acme-marketplace-tf-state",
                    "--stackit-tfstate-key-prefix",
                    "iac/tfstate",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            self.assertIn("BLUEPRINT_INIT_FORCE=true", result.stderr)

    def test_load_module_contract_resolves_repo_relative_path_through_symlinked_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            real_root = Path(tmpdir) / "real-repo"
            module_dir = real_root / "blueprint/modules/sample"
            module_dir.mkdir(parents=True, exist_ok=True)
            module_path = module_dir / "module.contract.yaml"
            module_path.write_text(
                "\n".join(
                    [
                        "apiVersion: blueprint.module.contract/v1alpha1",
                        "kind: OptionalModuleContract",
                        "metadata:",
                        "  name: sample",
                        "  version: 1.0.0",
                        "spec:",
                        "  module_id: sample",
                        '  purpose: "sample"',
                        "  enabled_by_default: false",
                        "  enable_flag: SAMPLE_ENABLED",
                        "  inputs:",
                        "    required_env: []",
                        "  outputs:",
                        "    produced: []",
                        "  make_targets: {}",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            symlink_root = Path(tmpdir) / "repo-link"
            symlink_root.symlink_to(real_root, target_is_directory=True)

            module = load_module_contract(
                symlink_root / "blueprint/modules/sample/module.contract.yaml",
                real_root.resolve(),
            )

            self.assertEqual(module.contract_path, "blueprint/modules/sample/module.contract.yaml")

    def test_workflows_scaffolding_is_contract_conditional(self) -> None:
        contract = _read("blueprint/contract.yaml")
        bootstrap = _read("scripts/bin/infra/bootstrap.sh")
        makefile_renderer = _read("scripts/bin/blueprint/render_makefile.sh")
        validate_py = _read("scripts/bin/blueprint/validate_contract.py")

        self.assertIn("WORKFLOWS_ENABLED:", contract)
        self.assertIn("disabled_scaffold_policy:", contract)
        self.assertIn("mode: preserve_on_bootstrap", contract)
        self.assertIn("command: make infra-bootstrap", contract)
        self.assertIn("disabled_resource_cleanup_command: make infra-destroy-disabled-modules", contract)
        self.assertIn("materialization_command: make blueprint-render-makefile", contract)
        self.assertIn("enable_flag: WORKFLOWS_ENABLED", contract)
        self.assertIn("scaffolding_mode: conditional", contract)
        self.assertIn("paths_required_when_enabled:", contract)
        self.assertIn("- dags_path", contract)
        self.assertIn("- terraform_path", contract)
        self.assertIn("- gitops_path", contract)
        self.assertIn("- tests_path", contract)

        self.assertIn("if is_module_enabled workflows; then", bootstrap)
        self.assertIn("scaffolding_mode", validate_py)
        self.assertIn("paths_required_when_enabled", validate_py)
        self.assertIn("make_targets_mode: conditional", contract)
        self.assertIn("_validate_optional_module_make_targets", validate_py)
        self.assertIn("optional-module make target must not be materialized when module disabled", validate_py)
        self.assertIn('"make/blueprint.generated.mk.tmpl"', makefile_renderer)
        self.assertIn("updated make/blueprint.generated.mk from template based on enabled modules", makefile_renderer)

    def test_langfuse_postgres_neo4j_and_p0_modules_scaffolding_is_contract_conditional(self) -> None:
        contract = _read("blueprint/contract.yaml")
        bootstrap = _read("scripts/bin/infra/bootstrap.sh")

        self.assertIn("LANGFUSE_ENABLED:", contract)
        self.assertIn("POSTGRES_ENABLED:", contract)
        self.assertIn("NEO4J_ENABLED:", contract)
        self.assertIn("OBJECT_STORAGE_ENABLED:", contract)
        self.assertIn("RABBITMQ_ENABLED:", contract)
        self.assertIn("DNS_ENABLED:", contract)
        self.assertIn("PUBLIC_ENDPOINTS_ENABLED:", contract)
        self.assertIn("SECRETS_MANAGER_ENABLED:", contract)
        self.assertIn("KMS_ENABLED:", contract)
        self.assertIn("IDENTITY_AWARE_PROXY_ENABLED:", contract)
        self.assertIn("enable_flag: LANGFUSE_ENABLED", contract)
        self.assertIn("enable_flag: POSTGRES_ENABLED", contract)
        self.assertIn("enable_flag: NEO4J_ENABLED", contract)
        self.assertIn("enable_flag: OBJECT_STORAGE_ENABLED", contract)
        self.assertIn("enable_flag: RABBITMQ_ENABLED", contract)
        self.assertIn("enable_flag: DNS_ENABLED", contract)
        self.assertIn("enable_flag: PUBLIC_ENDPOINTS_ENABLED", contract)
        self.assertIn("enable_flag: SECRETS_MANAGER_ENABLED", contract)
        self.assertIn("enable_flag: KMS_ENABLED", contract)
        self.assertIn("enable_flag: IDENTITY_AWARE_PROXY_ENABLED", contract)
        self.assertIn("if is_module_enabled langfuse; then", bootstrap)
        self.assertIn("if is_module_enabled postgres; then", bootstrap)
        self.assertIn("if is_module_enabled neo4j; then", bootstrap)
        self.assertIn("if is_module_enabled object-storage; then", bootstrap)
        self.assertIn("if is_module_enabled rabbitmq; then", bootstrap)
        self.assertIn("if is_module_enabled dns; then", bootstrap)
        self.assertIn("if is_module_enabled public-endpoints; then", bootstrap)
        self.assertIn("if is_module_enabled secrets-manager; then", bootstrap)
        self.assertIn("if is_module_enabled kms; then", bootstrap)
        self.assertIn("if is_module_enabled identity-aware-proxy; then", bootstrap)

    def test_iap_contract_requires_keycloak_oidc_configuration(self) -> None:
        contract = _read("blueprint/contract.yaml")
        iap_module_contract = _read("blueprint/modules/identity-aware-proxy/module.contract.yaml")
        iap_lib = _read("scripts/lib/infra/identity_aware_proxy.sh")

        self.assertIn("Keycloak OIDC", contract)
        self.assertIn("required_core_capabilities:", contract)
        self.assertIn("keycloak_oidc_configuration", contract)
        self.assertIn("KEYCLOAK_ISSUER_URL", contract)
        self.assertIn("KEYCLOAK_CLIENT_ID", contract)
        self.assertIn("KEYCLOAK_CLIENT_SECRET", contract)
        self.assertIn("IAP_COOKIE_SECRET", contract)

        self.assertIn("keycloak_available", iap_module_contract)
        self.assertIn("keycloak_oidc_configuration", iap_module_contract)
        self.assertIn("IAP_COOKIE_SECRET", iap_module_contract)
        self.assertIn("KEYCLOAK_ISSUER_URL", iap_module_contract)
        self.assertIn("KEYCLOAK_CLIENT_ID", iap_module_contract)
        self.assertIn("KEYCLOAK_CLIENT_SECRET", iap_module_contract)

        self.assertIn(
            "require_env_vars IAP_UPSTREAM_URL KEYCLOAK_ISSUER_URL KEYCLOAK_CLIENT_ID KEYCLOAK_CLIENT_SECRET IAP_COOKIE_SECRET",
            iap_lib,
        )

    def test_makefile_template_supports_conditional_optional_targets(self) -> None:
        makefile_template = _read("scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl")
        makefile_renderer = _read("scripts/bin/blueprint/render_makefile.sh")

        self.assertIn("{{PHONY_OBSERVABILITY}}", makefile_template)
        self.assertIn("{{PHONY_WORKFLOWS}}", makefile_template)
        self.assertIn("{{PHONY_LANGFUSE}}", makefile_template)
        self.assertIn("{{PHONY_POSTGRES}}", makefile_template)
        self.assertIn("{{PHONY_NEO4J}}", makefile_template)
        self.assertIn("{{PHONY_OBJECT_STORAGE}}", makefile_template)
        self.assertIn("{{PHONY_RABBITMQ}}", makefile_template)
        self.assertIn("{{PHONY_DNS}}", makefile_template)
        self.assertIn("{{PHONY_PUBLIC_ENDPOINTS}}", makefile_template)
        self.assertIn("{{PHONY_SECRETS_MANAGER}}", makefile_template)
        self.assertIn("{{PHONY_KMS}}", makefile_template)
        self.assertIn("{{PHONY_IDENTITY_AWARE_PROXY}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_OBSERVABILITY}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_WORKFLOWS}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_LANGFUSE}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_POSTGRES}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_NEO4J}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_OBJECT_STORAGE}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_RABBITMQ}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_DNS}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_PUBLIC_ENDPOINTS}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_SECRETS_MANAGER}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_KMS}}", makefile_template)
        self.assertIn("{{INFRA_ENV_GUARDED_IDENTITY_AWARE_PROXY}}", makefile_template)
        self.assertIn("INFRA_ENV_GUARDED_TARGETS :=", makefile_template)
        self.assertIn("$(INFRA_ENV_GUARDED_TARGETS): blueprint-check-placeholders", makefile_template)
        self.assertIn("{{TARGETS_OBSERVABILITY}}", makefile_template)
        self.assertIn("{{TARGETS_WORKFLOWS}}", makefile_template)
        self.assertIn("{{TARGETS_LANGFUSE}}", makefile_template)
        self.assertIn("{{TARGETS_POSTGRES}}", makefile_template)
        self.assertIn("{{TARGETS_NEO4J}}", makefile_template)
        self.assertIn("{{TARGETS_OBJECT_STORAGE}}", makefile_template)
        self.assertIn("{{TARGETS_RABBITMQ}}", makefile_template)
        self.assertIn("{{TARGETS_DNS}}", makefile_template)
        self.assertIn("{{TARGETS_PUBLIC_ENDPOINTS}}", makefile_template)
        self.assertIn("{{TARGETS_SECRETS_MANAGER}}", makefile_template)
        self.assertIn("{{TARGETS_KMS}}", makefile_template)
        self.assertIn("{{TARGETS_IDENTITY_AWARE_PROXY}}", makefile_template)
        self.assertIn('"INFRA_ENV_GUARDED_OBSERVABILITY=$phony_observability" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_WORKFLOWS=$phony_workflows" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_LANGFUSE=$phony_langfuse" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_POSTGRES=$phony_postgres" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_NEO4J=$phony_neo4j" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_OBJECT_STORAGE=$phony_object_storage" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_RABBITMQ=$phony_rabbitmq" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_DNS=$phony_dns" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_PUBLIC_ENDPOINTS=$phony_public_endpoints" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_SECRETS_MANAGER=$phony_secrets_manager" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_KMS=$phony_kms" \\', makefile_renderer)
        self.assertIn('"INFRA_ENV_GUARDED_IDENTITY_AWARE_PROXY=$phony_identity_aware_proxy" \\', makefile_renderer)
        self.assertIn("render_makefile()", makefile_renderer)
        self.assertIn('render_bootstrap_template_content \\', makefile_renderer)
        self.assertIn('"blueprint" \\', makefile_renderer)

    def test_shell_contract_helpers_use_reusable_python_cli(self) -> None:
        contract_runtime_sh = _read("scripts/lib/blueprint/contract_runtime.sh")
        profile_sh = _read("scripts/lib/infra/profile.sh")
        runtime_cli = _read("scripts/lib/blueprint/contract_runtime_cli.py")

        self.assertNotIn("<<'PY'", contract_runtime_sh)
        self.assertNotIn("<<'PY'", profile_sh)
        self.assertIn("contract_runtime_cli.py", contract_runtime_sh)
        self.assertIn("contract_runtime_cli.py", profile_sh)
        self.assertIn("runtime-lines", runtime_cli)
        self.assertIn("required-env-vars", runtime_cli)
        self.assertIn("module-defaults", runtime_cli)


if __name__ == "__main__":
    unittest.main()
