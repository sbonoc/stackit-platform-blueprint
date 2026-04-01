from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class GovernanceRefactorCases(RefactorContractBase):
    def test_stackit_observability_defaults_omit_unsupported_medium_plan_retentions(self) -> None:
        foundation_vars = _read("infra/cloud/stackit/terraform/foundation/variables.tf")
        template_vars = _read("scripts/templates/infra/bootstrap/infra/cloud/stackit/terraform/foundation/variables.tf")

        self.assertIn('variable "observability_logs_retention_days"', foundation_vars)
        self.assertIn('default     = null', foundation_vars)
        self.assertIn('variable "observability_traces_retention_days"', foundation_vars)
        self.assertIn('default     = null', template_vars)

    def test_optional_module_chart_pins_use_canonical_versions_source(self) -> None:
        versions = _read("scripts/lib/infra/versions.sh")
        self.assertIn('POSTGRES_HELM_CHART_VERSION_PIN="15.5.38"', versions)
        self.assertIn('OBJECT_STORAGE_HELM_CHART_VERSION_PIN="17.0.21"', versions)
        self.assertIn('RABBITMQ_HELM_CHART_VERSION_PIN="15.5.3"', versions)
        self.assertIn('NEO4J_HELM_CHART_VERSION_PIN="2026.1.4"', versions)
        self.assertIn('PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN="1.7.1"', versions)
        self.assertIn('IAP_HELM_CHART_VERSION_PIN="10.4.0"', versions)
        self.assertIn('KEYCLOAK_HELM_CHART_VERSION_PIN="7.1.9"', versions)
        self.assertIn('KEYCLOAK_IMAGE_TAG_PIN="26.5.5"', versions)
        self.assertIn('POSTGRES_LOCAL_IMAGE_REGISTRY="docker.io"', versions)
        self.assertIn('POSTGRES_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/postgresql"', versions)
        self.assertIn('OBJECT_STORAGE_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/minio"', versions)
        self.assertIn('RABBITMQ_LOCAL_IMAGE_REPOSITORY="bitnamilegacy/rabbitmq"', versions)
        self.assertIn('RABBITMQ_LOCAL_IMAGE_TAG="4.0.9-debian-12-r1"', versions)
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
        self.assertIn(
            'set_default_env KEYCLOAK_HELM_CHART_VERSION "$KEYCLOAK_HELM_CHART_VERSION_PIN"',
            _read("scripts/lib/infra/keycloak.sh"),
        )
        self.assertIn('set_default_env KEYCLOAK_IMAGE_TAG "$KEYCLOAK_IMAGE_TAG_PIN"', _read("scripts/lib/infra/keycloak.sh"))

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
                "docs/platform/consumer/event_messaging_baseline.md",
                "docs/platform/consumer/zero_downtime_evolution.md",
                "docs/platform/consumer/tenant_context_propagation.md",
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
                "scripts/templates/consumer/scaffold/messaging/contracts/producer/.gitkeep",
                "scripts/templates/consumer/scaffold/messaging/contracts/consumer/.gitkeep",
                "scripts/templates/consumer/scaffold/messaging/sql/outbox.sql.tmpl",
                "scripts/templates/consumer/scaffold/messaging/sql/inbox.sql.tmpl",
                "scripts/templates/consumer/scaffold/messaging/sql/idempotency_keys.sql.tmpl",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/event_messaging_baseline.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/zero_downtime_evolution.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/tenant_context_propagation.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md",
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
                "scripts/lib/blueprint/merge_markers.py",
                "scripts/lib/blueprint/resync_consumer_seeds.py",
                "scripts/lib/blueprint/runtime_dependency_edges.py",
                "scripts/lib/blueprint/upgrade_consumer.py",
                "scripts/lib/blueprint/upgrade_consumer_validate.py",
                "scripts/lib/blueprint/upgrade_report_metrics.py",
                "scripts/lib/blueprint/schemas/upgrade_plan.schema.json",
                "scripts/lib/blueprint/schemas/upgrade_apply.schema.json",
                "scripts/lib/blueprint/schemas/upgrade_validate.schema.json",
                "scripts/lib/docs/generate_contract_docs.py",
                "scripts/lib/docs/sync_blueprint_template_docs.py",
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
                "scripts/bin/blueprint/upgrade_consumer.sh",
                "scripts/bin/blueprint/upgrade_consumer_validate.sh",
                "scripts/bin/blueprint/test_async_message_contracts_producer.sh",
                "scripts/bin/blueprint/test_async_message_contracts_consumer.sh",
                "scripts/bin/blueprint/test_async_message_contracts_all.sh",
                "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
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
                "docs/blueprint/contracts/async_message_contracts.md",
                "contracts/async/pact/messages/producer/README.md",
                "contracts/async/pact/messages/consumer/README.md",
                "docs/reference/generated/contract_metadata.generated.md",
                "docs/reference/generated/core_targets.generated.md",
                "tests/__init__.py",
                "tests/infra/__init__.py",
                "tests/e2e/__init__.py",
                "tests/_shared/__init__.py",
                "tests/_shared/helpers.py",
                "tests/_shared/json_schema.py",
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
            {"blueprint-", "quality-", "infra-", "apps-", "backend-", "touchpoints-", "test-", "auth-", "docs-"}
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
                "blueprint-upgrade-consumer",
                "blueprint-upgrade-consumer-validate",
                "blueprint-check-placeholders",
                "blueprint-template-smoke",
                "blueprint-bootstrap",
                "blueprint-clean-generated",
                "blueprint-render-makefile",
                "blueprint-render-module-wrapper-skeletons",
                "quality-hooks-fast",
                "quality-hooks-strict",
                "quality-docs-lint",
                "quality-docs-sync-blueprint-template",
                "quality-docs-check-blueprint-template-sync",
                "quality-docs-sync-core-targets",
                "quality-docs-check-core-targets-sync",
                "quality-docs-sync-contract-metadata",
                "quality-docs-check-contract-metadata-sync",
                "quality-docs-sync-runtime-identity-summary",
                "quality-docs-check-runtime-identity-summary-sync",
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
                "auth-reconcile-eso-runtime-secrets",
                "docs-build",
                "docs-smoke",
                "test-contracts-async-producer",
                "test-contracts-async-consumer",
                "test-contracts-async-all",
            }.issubset(required_targets),
            msg="contract required_targets is missing canonical blueprint/stackit/docs targets",
        )
        async_contract = _extract_yaml_section(contract_lines, "async_message_contracts")
        async_make_targets = _extract_yaml_section(async_contract, "make_targets")
        async_hooks = _extract_yaml_section(async_contract, "optional_hooks")
        self.assertEqual(_extract_yaml_scalar(async_contract, "provider"), "pact")
        self.assertEqual(_extract_yaml_scalar(async_contract, "enabled_env_var"), "ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED")
        self.assertEqual(_extract_yaml_scalar(async_make_targets, "producer"), "test-contracts-async-producer")
        self.assertEqual(_extract_yaml_scalar(async_make_targets, "consumer"), "test-contracts-async-consumer")
        self.assertEqual(_extract_yaml_scalar(async_make_targets, "all"), "test-contracts-async-all")
        self.assertEqual(_extract_yaml_scalar(async_make_targets, "aggregate"), "test-contracts-all")
        self.assertEqual(
            _extract_yaml_scalar(async_hooks, "producer_verify_command_env_var"),
            "ASYNC_PACT_PRODUCER_VERIFY_CMD",
        )
        self.assertEqual(
            _extract_yaml_scalar(async_hooks, "consumer_verify_command_env_var"),
            "ASYNC_PACT_CONSUMER_VERIFY_CMD",
        )

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
            "_validate_async_message_contract",
            "_validate_event_messaging_contract",
            "_validate_zero_downtime_evolution_contract",
            "_validate_tenant_context_contract",
        ):
            self.assertIn(marker, validate_py)
        self.assertNotIn("def _extract_yaml_list", validate_py)

    def test_contract_includes_optional_runtime_policy_sections(self) -> None:
        contract_yaml = _read("blueprint/contract.yaml")
        self.assertIn("EVENT_MESSAGING_BASELINE_ENABLED:", contract_yaml)
        self.assertIn("ZERO_DOWNTIME_EVOLUTION_ENABLED:", contract_yaml)
        self.assertIn("TENANT_CONTEXT_PROPAGATION_ENABLED:", contract_yaml)
        self.assertIn("event_messaging_contract:", contract_yaml)
        self.assertIn("zero_downtime_evolution_contract:", contract_yaml)
        self.assertIn("tenant_context_contract:", contract_yaml)

    def test_platform_base_namespaces_include_network_for_shared_gateway(self) -> None:
        namespaces = _read("infra/gitops/platform/base/namespaces.yaml")
        namespaces_template = _read("scripts/templates/infra/bootstrap/infra/gitops/platform/base/namespaces.yaml")
        self.assertIn("name: network", namespaces)
        self.assertIn("Shared gateway/route attachment namespace", namespaces)
        self.assertEqual(namespaces, namespaces_template)

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
        self.assertIn("KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED=true", init_env_defaults)
        self.assertIn("EVENT_MESSAGING_BASELINE_ENABLED=false", init_env_defaults)
        self.assertIn("ZERO_DOWNTIME_EVOLUTION_ENABLED=false", init_env_defaults)
        self.assertIn("TENANT_CONTEXT_PROPAGATION_ENABLED=false", init_env_defaults)
        self.assertIn("RUNTIME_CREDENTIALS_SOURCE_NAMESPACE=security", init_env_defaults)
        self.assertIn("RUNTIME_CREDENTIALS_TARGET_NAMESPACE=apps", init_env_defaults)
        self.assertIn("RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT=180", init_env_defaults)
        self.assertIn("RUNTIME_CREDENTIALS_REQUIRED=false", init_env_defaults)
        self.assertIn("ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED=false", init_env_defaults)
        self.assertIn("ASYNC_PACT_PRODUCER_VERIFY_CMD=", init_env_defaults)
        self.assertIn("ASYNC_PACT_CONSUMER_VERIFY_CMD=", init_env_defaults)
        self.assertIn("ASYNC_PACT_BROKER_PUBLISH_CMD=", init_env_defaults)
        self.assertIn("ASYNC_PACT_CAN_I_DEPLOY_CMD=", init_env_defaults)
        self.assertIn("ASYNC_PACT_PRODUCER_ARTIFACT_DIR=artifacts/contracts/async/pact/producer", init_env_defaults)
        self.assertIn("ASYNC_PACT_CONSUMER_ARTIFACT_DIR=artifacts/contracts/async/pact/consumer", init_env_defaults)
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
            self.assertIn("POSTGRES_INSTANCE_NAME=blueprint-postgres", defaults_env)
            self.assertIn("POSTGRES_DB_NAME=platform", defaults_env)
            self.assertIn("POSTGRES_USER=platform", defaults_env)
            self.assertIn("OBJECT_STORAGE_BUCKET_NAME=marketplace-assets", defaults_env)
            self.assertIn("PUBLIC_ENDPOINTS_BASE_DOMAIN=apps.local", defaults_env)
            self.assertIn("IAP_UPSTREAM_URL=http://catalog.apps.svc.cluster.local:8080", defaults_env)
            self.assertIn("KEYCLOAK_ISSUER_URL=https://auth.example.invalid/realms/iap", defaults_env)
            self.assertIn("KEYCLOAK_CLIENT_ID=iap-client", defaults_env)
            self.assertIn("POSTGRES_PASSWORD=platform-password", local_secrets_env)
            self.assertIn("IAP_COOKIE_SECRET=0123456789abcdef0123456789abcdef", local_secrets_env)
            self.assertIn("KEYCLOAK_CLIENT_SECRET=blueprint-client-secret", local_secrets_env)
            self.assertNotIn("KEYCLOAK_CLIENT_ID=", local_secrets_env)
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

            custom_defaults_env = defaults_env.replace(
                "PUBLIC_ENDPOINTS_BASE_DOMAIN=apps.local",
                "PUBLIC_ENDPOINTS_BASE_DOMAIN=apps.acme.local",
            )
            (tmp_root / "blueprint/repo.init.env").write_text(custom_defaults_env, encoding="utf-8")
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
            self.assertIn(
                "PUBLIC_ENDPOINTS_BASE_DOMAIN=apps.acme.local",
                (tmp_root / "blueprint/repo.init.env").read_text(encoding="utf-8"),
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
