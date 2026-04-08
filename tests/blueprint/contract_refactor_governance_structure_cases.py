from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class GovernanceStructureCases(RefactorContractBase):
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
        self.assertIn('"--contract-path"', validate_sh)
        self.assertIn('"$ROOT_DIR/blueprint/contract.yaml"', validate_sh)

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
                ".agents/skills/blueprint-consumer-upgrade/SKILL.md",
                ".agents/skills/blueprint-consumer-upgrade/agents/openai.yaml",
                ".agents/skills/blueprint-consumer-upgrade/references/manual_merge_checklist.md",
                ".agents/skills/blueprint-consumer-upgrade/scripts/resolve_latest_stable_ref.sh",
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
                "scripts/templates/consumer/init/.agents/skills/blueprint-consumer-upgrade/SKILL.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-consumer-upgrade/agents/openai.yaml.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-consumer-upgrade/references/manual_merge_checklist.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-consumer-upgrade/scripts/resolve_latest_stable_ref.sh.tmpl",
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
                "scripts/lib/blueprint/upgrade_preflight.py",
                "scripts/lib/blueprint/upgrade_consumer_validate.py",
                "scripts/lib/blueprint/upgrade_report_metrics.py",
                "scripts/lib/blueprint/schemas/upgrade_plan.schema.json",
                "scripts/lib/blueprint/schemas/upgrade_apply.schema.json",
                "scripts/lib/blueprint/schemas/upgrade_validate.schema.json",
                "scripts/lib/docs/generate_contract_docs.py",
                "scripts/lib/docs/sync_blueprint_template_docs.py",
                "scripts/lib/docs/sync_platform_seed_docs.py",
                "scripts/lib/docs/sync_module_contract_summaries.py",
                "scripts/lib/infra/k8s_wait.sh",
                "scripts/lib/infra/module_execution.sh",
                "scripts/lib/quality/semver.sh",
                "scripts/lib/quality/render_ci_workflow.py",
                "scripts/lib/quality/test_pyramid_contract.json",
                "scripts/lib/shell/bootstrap.sh",
                "scripts/lib/shell/exec.sh",
                "scripts/lib/shell/logging.sh",
                "scripts/lib/shell/utils.sh",
                "scripts/bin/blueprint/clean_generated.sh",
                "scripts/bin/blueprint/install_codex_skill.sh",
                "scripts/bin/blueprint/init_repo_interactive.sh",
                "scripts/bin/blueprint/resync_consumer_seeds.sh",
                "scripts/bin/blueprint/upgrade_consumer.sh",
                "scripts/bin/blueprint/upgrade_consumer_preflight.sh",
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
                "tests/_shared/exec.py",
                "tests/_shared/helpers.py",
                "tests/_shared/json_schema.py",
                "tests/blueprint/contract_refactor_governance_structure_cases.py",
                "tests/blueprint/contract_refactor_governance_runtime_cases.py",
                "tests/blueprint/contract_refactor_governance_version_cases.py",
                "tests/blueprint/contract_refactor_governance_init_cases.py",
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
                "blueprint-upgrade-consumer-preflight",
                "blueprint-upgrade-consumer-validate",
                "blueprint-install-codex-skill",
                "blueprint-check-placeholders",
                "blueprint-template-smoke",
                "blueprint-bootstrap",
                "blueprint-clean-generated",
                "blueprint-render-makefile",
                "blueprint-render-module-wrapper-skeletons",
                "quality-hooks-fast",
                "quality-hooks-strict",
                "quality-ci-sync",
                "quality-ci-check-sync",
                "quality-docs-lint",
                "quality-docs-sync-all",
                "quality-docs-sync-blueprint-template",
                "quality-docs-check-blueprint-template-sync",
                "quality-docs-sync-platform-seed",
                "quality-docs-check-platform-seed-sync",
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
                "infra-contract-test-fast",
                "infra-local-destroy-all",
                "infra-destroy-disabled-modules",
                "infra-stackit-ci-github-setup",
                "infra-audit-version-cached",
                "apps-ci-bootstrap",
                "apps-audit-versions-cached",
                "apps-publish-ghcr",
                "quality-ci-fast",
                "quality-ci-full-e2e",
                "quality-ci-strict",
                "quality-ci-blueprint",
                "quality-ci-generated-consumer-smoke",
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
