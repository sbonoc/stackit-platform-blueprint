from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


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
        hooks = _read("scripts/bin/quality/hooks_run.sh")
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
        self.assertIn('postgres_acl_effective', foundation_locals)
        self.assertIn('distinct(concat(', foundation_locals)
        self.assertIn('stackit_ske_cluster.foundation[0].egress_address_ranges', foundation_locals)
        self.assertIn('dns_zone_dns_names', foundation_locals)
        self.assertIn('trimsuffix(zone, ".")', foundation_locals)
        self.assertIn('object_storage_bucket_name', foundation_locals)
        self.assertIn('object_storage_credentials_group_name', foundation_locals)
        self.assertIn('secrets_manager_instance_name', foundation_locals)
        self.assertIn('name            = local.postgres_instance_name', foundation_main)
        self.assertIn('acl             = local.postgres_acl_effective', foundation_main)
        self.assertIn('enabled = var.dns_enabled && length(local.dns_zone_dns_names) > 0', foundation_main)
        self.assertIn('for_each = var.dns_enabled ? local.dns_zone_dns_names : {}', foundation_main)
        self.assertIn('name       = local.object_storage_bucket_name', foundation_main)
        self.assertIn('name       = local.object_storage_credentials_group_name', foundation_main)
        self.assertIn('name       = local.secrets_manager_instance_name', foundation_main)
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

    def test_local_crossplane_bootstrap_waits_for_chart_deployment_names(self) -> None:
        bootstrap = _read("scripts/bin/infra/local_crossplane_bootstrap.sh")
        self.assertIn("deployment/crossplane", bootstrap)
        self.assertIn("deployment/crossplane-rbac-manager", bootstrap)
        self.assertNotIn('deployment/"$CROSSPLANE_HELM_RELEASE"', bootstrap)

    def test_optional_module_chart_pins_use_canonical_versions_source(self) -> None:
        versions = _read("scripts/lib/infra/versions.sh")
        self.assertIn('POSTGRES_HELM_CHART_VERSION_PIN="15.5.38"', versions)
        self.assertIn('OBJECT_STORAGE_HELM_CHART_VERSION_PIN="17.0.21"', versions)
        self.assertIn('RABBITMQ_HELM_CHART_VERSION_PIN="16.0.14"', versions)
        self.assertIn('NEO4J_HELM_CHART_VERSION_PIN="2026.1.4"', versions)
        self.assertIn('PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN="1.7.1"', versions)
        self.assertIn('IAP_HELM_CHART_VERSION_PIN="10.4.0"', versions)

        self.assertIn(
            'set_default_env POSTGRES_HELM_CHART_VERSION "$POSTGRES_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/postgres.sh"),
        )
        self.assertIn(
            'set_default_env OBJECT_STORAGE_HELM_CHART_VERSION "$OBJECT_STORAGE_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/object_storage.sh"),
        )
        self.assertIn(
            'set_default_env RABBITMQ_HELM_CHART_VERSION "$RABBITMQ_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/rabbitmq.sh"),
        )
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
        self.assertEqual(_extract_yaml_scalar(template_section, "minimum_supported_upgrade_from"), "1.0.0")
        self.assertEqual(_extract_yaml_scalar(template_section, "init_command"), "make blueprint-init-repo")
        self.assertEqual(_extract_yaml_scalar(template_section, "upgrade_command"), "make blueprint-migrate")
        self.assertEqual(_extract_yaml_scalar(template_section, "example_env_file"), "blueprint/repo.init.example.env")

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
        self.assertTrue(
            {
                ".github/workflows/template_release.yml",
                ".gitignore",
                ".dockerignore",
                ".editorconfig",
                ".pre-commit-config.yaml",
                "make/blueprint.generated.mk",
                "make/platform.mk",
                "docs/blueprint/README.md",
                "docs/blueprint/architecture/system_overview.md",
                "docs/blueprint/architecture/execution_model.md",
                "docs/blueprint/governance/template_release_policy.md",
                "docs/blueprint/governance/ownership_matrix.md",
                "docs/platform/README.md",
                "docs/platform/consumer/first_30_minutes.md",
                "docs/platform/consumer/quickstart.md",
                "docs/platform/consumer/troubleshooting.md",
                "docs/platform/consumer/upgrade_runbook.md",
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
                "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl",
                "scripts/templates/blueprint/bootstrap/make/platform.mk",
                "scripts/lib/blueprint/bootstrap_templates.sh",
                "scripts/lib/blueprint/contract_schema.py",
                "scripts/lib/blueprint/generate_module_wrapper_skeletons.py",
                "scripts/lib/docs/generate_contract_docs.py",
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
                "scripts/bin/blueprint/render_module_wrapper_skeletons.sh",
                "scripts/bin/infra/destroy_disabled_modules.sh",
                "scripts/bin/quality/check_test_pyramid.py",
                "scripts/bin/quality/lint_docs.py",
                "scripts/bin/quality/render_core_targets_doc.py",
                "docs/reference/generated/contract_metadata.generated.md",
                "docs/reference/generated/core_targets.generated.md",
                "tests/__init__.py",
                "tests/blueprint/__init__.py",
                "tests/infra/__init__.py",
                "tests/docs/__init__.py",
                "tests/e2e/__init__.py",
                "tests/_shared/__init__.py",
                "tests/_shared/helpers.py",
            }.issubset(required_files),
            msg="contract required_files is missing canonical blueprint assets",
        )

        required_namespaces = set(_extract_yaml_list(contract_lines, "required_namespaces"))
        self.assertTrue(
            {"blueprint-", "quality-", "infra-", "apps-", "backend-", "touchpoints-", "test-", "docs-"}
            .issubset(required_namespaces)
        )
        required_paths = set(_extract_yaml_list(contract_lines, "required_paths"))
        self.assertTrue(
            {
                "tests/blueprint/",
                "tests/infra/",
                "tests/docs/",
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
                "blueprint-check-placeholders",
                "blueprint-template-smoke",
                "blueprint-release-notes",
                "blueprint-migrate",
                "blueprint-bootstrap",
                "blueprint-clean-generated",
                "blueprint-render-makefile",
                "blueprint-render-module-wrapper-skeletons",
                "quality-docs-lint",
                "quality-docs-sync-core-targets",
                "quality-docs-check-core-targets-sync",
                "quality-docs-sync-contract-metadata",
                "quality-docs-check-contract-metadata-sync",
                "quality-test-pyramid",
                "infra-prereqs",
                "infra-help-reference",
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
        self.assertIn('"make/platform.mk"', bootstrap)
        self.assertIn('"blueprint/repo.init.example.env"', bootstrap)
        self.assertIn('"docs/platform/consumer/quickstart.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/first_30_minutes.md"', bootstrap)
        self.assertIn('"docs/blueprint/governance/template_release_policy.md"', bootstrap)
        self.assertIn('"docs/blueprint/governance/ownership_matrix.md"', bootstrap)
        self.assertIn('"docs/platform/modules/identity-aware-proxy/README.md"', bootstrap)
        self.assertIn('log_metric "blueprint_template_file_count" "${#template_files[@]}"', bootstrap)
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
        self.assertIn("docs/build/", gitignore_template)
        self.assertIn("docs/.docusaurus/", gitignore_template)

        self.assertIn("artifacts", dockerignore_template)
        self.assertIn("docs/build", dockerignore_template)
        self.assertIn("docs/.docusaurus", dockerignore_template)

    def test_bootstrap_docs_templates_are_synchronized(self) -> None:
        template_root = REPO_ROOT / "scripts/templates/blueprint/bootstrap"
        synced_docs = [
            "docs/README.md",
                "docs/blueprint/README.md",
                "docs/blueprint/architecture/system_overview.md",
                "docs/blueprint/architecture/execution_model.md",
                "docs/blueprint/governance/template_release_policy.md",
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

        self.assertIn('"docs/platform/consumer/quickstart.md"', bootstrap)
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
        self.assertIn("make quality-hooks-run", docs_readme)
        self.assertIn("make quality-docs-lint", docs_readme)
        self.assertIn("make quality-test-pyramid", docs_readme)
        self.assertIn("make docs-run", docs_readme)
        self.assertIn("make infra-status-json", docs_readme)
        self.assertIn("make blueprint-bootstrap", docs_readme)
        self.assertIn("make blueprint-render-module-wrapper-skeletons", docs_readme)
        self.assertIn("make blueprint-clean-generated", docs_readme)
        self.assertIn("make help", docs_readme)
        self.assertIn("make infra-help-reference", docs_readme)
        self.assertIn("make infra-destroy-disabled-modules", docs_readme)
        self.assertIn("materializes/prunes optional-module infra scaffolding", docs_readme)
        self.assertIn("[Blueprint Docs](blueprint/README.md)", docs_readme)
        self.assertIn("[Platform Docs](platform/README.md)", docs_readme)
        self.assertIn("[Core Make Targets (Generated)](reference/generated/core_targets.generated.md)", docs_readme)

    def test_consumer_quickstart_mentions_status_snapshot_and_no_duplicate_smoke(self) -> None:
        quickstart = _read("docs/platform/consumer/quickstart.md")
        self.assertIn("make infra-provision-deploy", quickstart)
        self.assertIn("make infra-status-json", quickstart)
        self.assertIn("artifacts/infra/infra_status_snapshot.json", quickstart)
        self.assertNotIn("make infra-smoke", quickstart)

    def test_quality_hooks_run_covers_docs_sync_checks_and_test_pyramid(self) -> None:
        hooks_run = _read("scripts/bin/quality/hooks_run.sh")
        self.assertIn("quality-docs-lint", hooks_run)
        self.assertIn("quality-docs-check-core-targets-sync", hooks_run)
        self.assertIn("quality-docs-check-contract-metadata-sync", hooks_run)
        self.assertIn("quality-test-pyramid", hooks_run)

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
        self.assertIn("infra-destroy-disabled-modules", troubleshooting)
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
        self.assertIn("module_action_enabled_count", module_lifecycle)
        self.assertIn("module_action_script_count", module_lifecycle)
        self.assertIn("module_action_disabled_count", module_lifecycle)
        self.assertIn("module_action_disabled_script_count", module_lifecycle)

    def test_bootstrap_prunes_disabled_optional_scaffolding(self) -> None:
        bootstrap = _read("scripts/bin/infra/bootstrap.sh")
        self.assertIn(
            'ensure_file_from_template "$ROOT_DIR/tests/infra/modules/observability/README.md" "infra" "tests/infra/modules/observability/README.md"',
            bootstrap,
        )
        self.assertIn("prune_optional_module_scaffolding()", bootstrap)
        self.assertIn("prune_path_if_exists()", bootstrap)
        self.assertIn("optional_module_pruned_path_count", bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/dags"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/langfuse"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/local/helm/postgres"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/workflows"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/langfuse"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/postgres"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/neo4j"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/gitops/argocd/optional/$env/neo4j.yaml"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/object-storage"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/local/helm/object-storage"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/object-storage"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/rabbitmq"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/local/helm/rabbitmq"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/rabbitmq"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/dns"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/dns"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/public-endpoints"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/local/helm/public-endpoints"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/public-endpoints"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/secrets-manager"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/secrets-manager"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/kms"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/kms"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/cloud/stackit/terraform/modules/identity-aware-proxy"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/infra/local/helm/identity-aware-proxy"', bootstrap)
        self.assertIn('prune_path_if_exists "$ROOT_DIR/tests/infra/modules/identity-aware-proxy"', bootstrap)

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
            "scripts/bin/blueprint/check_placeholders.sh",
            "scripts/bin/blueprint/template_smoke.sh",
            "scripts/bin/blueprint/release_notes.sh",
            "scripts/bin/blueprint/migrate.sh",
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

    def test_blueprint_template_init_assets_exist(self) -> None:
        init_script = _read("scripts/bin/blueprint/init_repo.sh")
        init_interactive_script = _read("scripts/bin/blueprint/init_repo_interactive.sh")
        init_python = _read("scripts/lib/blueprint/init_repo.py")
        migrate_script = _read("scripts/bin/blueprint/migrate.sh")
        migrate_python = _read("scripts/lib/blueprint/migrate_repo.py")
        smoke_script = _read("scripts/bin/blueprint/template_smoke.sh")
        placeholder_script = _read("scripts/bin/blueprint/check_placeholders.sh")
        release_notes_script = _read("scripts/bin/blueprint/release_notes.sh")
        release_notes_python = _read("scripts/lib/blueprint/generate_release_notes.py")
        init_env = _read("blueprint/repo.init.example.env")

        self.assertIn("blueprint_init_repo", init_script)
        self.assertIn("--dry-run", init_script)
        self.assertIn("BLUEPRINT_INIT_DRY_RUN", init_script)
        self.assertIn("BLUEPRINT_REPO_NAME", init_script)
        self.assertIn("BLUEPRINT_GITHUB_ORG", init_script)
        self.assertIn("BLUEPRINT_GITHUB_REPO", init_script)
        self.assertIn("BLUEPRINT_DEFAULT_BRANCH", init_script)
        self.assertIn("blueprint_init_repo_interactive", init_interactive_script)
        self.assertIn("BLUEPRINT_INIT_DRY_RUN", init_interactive_script)
        self.assertIn("prompt_with_default", init_interactive_script)
        self.assertIn("_render_contract", init_python)
        self.assertIn("_render_docusaurus_config", init_python)
        self.assertIn("--dry-run", init_python)
        self.assertIn("blueprint_migrate", migrate_script)
        self.assertIn("TARGET_TEMPLATE_VERSION", migrate_python)
        self.assertIn("_migration_registry", migrate_python)
        self.assertIn("_plan_migration_path", migrate_python)
        self.assertIn("unsupported upgrade path", migrate_python)
        self.assertIn("template_bootstrap.template_version", migrate_python)
        self.assertIn("blueprint_template_smoke", smoke_script)
        self.assertIn("make blueprint-bootstrap", smoke_script)
        self.assertIn("make blueprint-check-placeholders", smoke_script)
        self.assertIn("make infra-provision-deploy", smoke_script)
        self.assertIn("make infra-status-json", smoke_script)
        self.assertIn("BLUEPRINT_TEMPLATE_SMOKE_SCENARIO", smoke_script)
        self.assertIn("assert_template_smoke_repo_state", smoke_script)
        self.assertIn("blueprint_check_placeholders", placeholder_script)
        self.assertIn("BLUEPRINT_GITHUB_ORG", placeholder_script)
        self.assertIn("blueprint_release_notes", release_notes_script)
        self.assertIn("render_release_notes", release_notes_python)
        self.assertIn("BLUEPRINT_REPO_NAME=", init_env)
        self.assertIn("BLUEPRINT_GITHUB_ORG=", init_env)
        self.assertIn("BLUEPRINT_GITHUB_REPO=", init_env)
        self.assertIn("BLUEPRINT_DEFAULT_BRANCH=", init_env)
        self.assertIn("BLUEPRINT_STACKIT_REGION=", init_env)
        self.assertIn("BLUEPRINT_STACKIT_TENANT_SLUG=", init_env)
        self.assertIn("BLUEPRINT_STACKIT_PLATFORM_SLUG=", init_env)
        self.assertIn("BLUEPRINT_STACKIT_PROJECT_ID=", init_env)
        self.assertIn("BLUEPRINT_STACKIT_TFSTATE_BUCKET=", init_env)
        self.assertIn("BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX=", init_env)

    def test_template_release_workflow_and_docs_exist(self) -> None:
        release_workflow = _read(".github/workflows/template_release.yml")
        ci_workflow = _read(".github/workflows/ci.yml")
        docs_readme = _read("docs/README.md")
        sidebars = _read("docs/sidebars.js")
        docusaurus_config = _read("docs/docusaurus.config.js")

        self.assertIn('name: template-release', release_workflow)
        self.assertIn('tags:', release_workflow)
        self.assertIn('"v*"', release_workflow)
        self.assertIn('make blueprint-release-notes', release_workflow)
        self.assertIn('make blueprint-template-smoke', release_workflow)
        self.assertIn('softprops/action-gh-release', release_workflow)
        self.assertIn('Smoke blueprint-migrate end-to-end', ci_workflow)
        self.assertIn('consumer-golden-conformance:', ci_workflow)
        self.assertIn('Golden template-consumer conformance matrix', ci_workflow)
        self.assertIn('BLUEPRINT_TEMPLATE_SMOKE_SCENARIO=${{ matrix.scenario.name }}', ci_workflow)
        self.assertIn('make blueprint-template-smoke', ci_workflow)
        self.assertIn('fail-fast: false', ci_workflow)
        self.assertIn('name: local-lite-baseline', ci_workflow)
        self.assertIn('name: local-full-observability-data', ci_workflow)
        self.assertIn('name: local-full-runtime-edge', ci_workflow)
        self.assertIn('name: stackit-dev-managed-services', ci_workflow)
        self.assertIn('name: stackit-dev-runtime-fallbacks', ci_workflow)
        self.assertIn('name: stackit-dev-workflows', ci_workflow)
        self.assertIn('contract-matrix:', ci_workflow)
        self.assertIn('profile: [local-full, stackit-dev]', ci_workflow)
        self.assertIn('observability_enabled: ["false", "true"]', ci_workflow)
        self.assertIn('Validate contract-critical profile/flag matrix', ci_workflow)
        self.assertIn(
            'tests.blueprint.test_upgrade.BlueprintUpgradeTests.test_blueprint_migrate_make_target_smoke_in_template_copy',
            ci_workflow,
        )
        self.assertIn('make infra-validate', ci_workflow)
        self.assertIn('make infra-smoke', ci_workflow)
        self.assertIn('pytest -q tests', ci_workflow)
        self.assertNotIn('pytest -q tests/tooling', ci_workflow)
        self.assertIn('Run canonical quality gate', ci_workflow)
        self.assertIn('Run pre-push hook stage', ci_workflow)
        self.assertIn('pre-commit run --hook-stage pre-push --all-files', ci_workflow)
        self.assertEqual(ci_workflow.count('make quality-hooks-run'), 1)
        self.assertNotIn('Shell script lint', ci_workflow)
        self.assertNotIn('make apps-audit-versions', ci_workflow)

        self.assertIn('[Platform Quickstart](platform/consumer/quickstart.md)', docs_readme)
        self.assertIn('[Platform Troubleshooting](platform/consumer/troubleshooting.md)', docs_readme)
        self.assertIn('[Platform Upgrade Runbook](platform/consumer/upgrade_runbook.md)', docs_readme)
        self.assertIn('[Template Release Policy](blueprint/governance/template_release_policy.md)', docs_readme)
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
            (tmp_root / "infra/gitops/argocd/root").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/gitops/argocd/environments/dev").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/gitops/argocd/overlays/local").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/env").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/foundation/env").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/bootstrap/state-backend").mkdir(parents=True, exist_ok=True)
            (tmp_root / "infra/cloud/stackit/terraform/foundation/state-backend").mkdir(parents=True, exist_ok=True)
            (tmp_root / "blueprint/contract.yaml").write_text(
                _read("blueprint/contract.yaml"),
                encoding="utf-8",
            )
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
            self.assertIn("name: acme-platform", updated_contract)
            self.assertIn("default_branch: main", updated_contract)
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

    def test_blueprint_init_python_dry_run_does_not_mutate_files(self) -> None:
        init_python_path = REPO_ROOT / "scripts/lib/blueprint/init_repo.py"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "blueprint").mkdir(parents=True, exist_ok=True)
            (tmp_root / "docs").mkdir(parents=True, exist_ok=True)
            contract_original = _read("blueprint/contract.yaml")
            docs_original = _read("docs/docusaurus.config.js")
            (tmp_root / "blueprint/contract.yaml").write_text(contract_original, encoding="utf-8")
            (tmp_root / "docs/docusaurus.config.js").write_text(docs_original, encoding="utf-8")

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
            self.assertIn("[dry-run] would update:", result.stdout)
            self.assertIn("[dry-run] summary:", result.stdout)
            self.assertEqual((tmp_root / "blueprint/contract.yaml").read_text(encoding="utf-8"), contract_original)
            self.assertEqual((tmp_root / "docs/docusaurus.config.js").read_text(encoding="utf-8"), docs_original)

    def test_workflows_scaffolding_is_contract_conditional(self) -> None:
        contract = _read("blueprint/contract.yaml")
        bootstrap = _read("scripts/bin/infra/bootstrap.sh")
        makefile_renderer = _read("scripts/bin/blueprint/render_makefile.sh")
        validate_py = _read("scripts/bin/blueprint/validate_contract.py")

        self.assertIn("WORKFLOWS_ENABLED:", contract)
        self.assertIn("disabled_scaffold_policy:", contract)
        self.assertIn("mode: prune_on_bootstrap", contract)
        self.assertIn("command: make infra-bootstrap", contract)
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
        self.assertIn("render_makefile()", makefile_renderer)
        self.assertIn('render_bootstrap_template_content \\', makefile_renderer)
        self.assertIn('"blueprint" \\', makefile_renderer)


if __name__ == "__main__":
    unittest.main()
