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
                ".spec-kit/policy-mapping.md",
                ".spec-kit/control-catalog.yaml",
                ".spec-kit/control-catalog.md",
                ".spec-kit/templates/blueprint/architecture.md",
                ".spec-kit/templates/blueprint/adr.md",
                ".spec-kit/templates/blueprint/spec.md",
                ".spec-kit/templates/blueprint/plan.md",
                ".spec-kit/templates/blueprint/tasks.md",
                ".spec-kit/templates/blueprint/traceability.md",
                ".spec-kit/templates/blueprint/graph.yaml",
                ".spec-kit/templates/blueprint/evidence_manifest.json",
                ".spec-kit/templates/blueprint/context_pack.md",
                ".spec-kit/templates/blueprint/pr_context.md",
                ".spec-kit/templates/blueprint/hardening_review.md",
                ".spec-kit/templates/consumer/architecture.md",
                ".spec-kit/templates/consumer/adr.md",
                ".spec-kit/templates/consumer/spec.md",
                ".spec-kit/templates/consumer/plan.md",
                ".spec-kit/templates/consumer/tasks.md",
                ".spec-kit/templates/consumer/traceability.md",
                ".spec-kit/templates/consumer/graph.yaml",
                ".spec-kit/templates/consumer/evidence_manifest.json",
                ".spec-kit/templates/consumer/context_pack.md",
                ".spec-kit/templates/consumer/pr_context.md",
                ".spec-kit/templates/consumer/hardening_review.md",
                "specs/README.md",
                ".agents/skills/blueprint-consumer-upgrade/SKILL.md",
                ".agents/skills/blueprint-consumer-upgrade/agents/openai.yaml",
                ".agents/skills/blueprint-consumer-upgrade/references/manual_merge_checklist.md",
                ".agents/skills/blueprint-consumer-upgrade/scripts/resolve_latest_stable_ref.sh",
                ".agents/skills/blueprint-consumer-ops/SKILL.md",
                ".agents/skills/blueprint-consumer-ops/agents/openai.yaml",
                ".agents/skills/blueprint-consumer-ops/references/consumer_ops_checklist.md",
                ".agents/skills/blueprint-sdd-intake-decompose/SKILL.md",
                ".agents/skills/blueprint-sdd-intake-decompose/agents/openai.yaml",
                ".agents/skills/blueprint-sdd-intake-decompose/references/intake_checklist.md",
                ".agents/skills/blueprint-sdd-clarification-gate/SKILL.md",
                ".agents/skills/blueprint-sdd-clarification-gate/agents/openai.yaml",
                ".agents/skills/blueprint-sdd-clarification-gate/references/clarification_categories.md",
                ".agents/skills/blueprint-sdd-plan-slicer/SKILL.md",
                ".agents/skills/blueprint-sdd-plan-slicer/agents/openai.yaml",
                ".agents/skills/blueprint-sdd-plan-slicer/references/plan_slice_checklist.md",
                ".agents/skills/blueprint-sdd-traceability-keeper/SKILL.md",
                ".agents/skills/blueprint-sdd-traceability-keeper/agents/openai.yaml",
                ".agents/skills/blueprint-sdd-traceability-keeper/references/traceability_matrix_template.md",
                ".agents/skills/blueprint-sdd-document-sync/SKILL.md",
                ".agents/skills/blueprint-sdd-document-sync/agents/openai.yaml",
                ".agents/skills/blueprint-sdd-document-sync/references/document_phase_checklist.md",
                ".agents/skills/blueprint-sdd-pr-packager/SKILL.md",
                ".agents/skills/blueprint-sdd-pr-packager/agents/openai.yaml",
                ".agents/skills/blueprint-sdd-pr-packager/references/pr_packaging_checklist.md",
                "make/blueprint.generated.mk",
                "make/platform.mk",
                "docs/blueprint/README.md",
                "docs/blueprint/architecture/system_overview.md",
                "docs/blueprint/architecture/execution_model.md",
                "docs/blueprint/architecture/decisions/README.md",
                "docs/blueprint/architecture/north_star.md",
                "docs/blueprint/architecture/tech_stack.md",
                "docs/blueprint/governance/ownership_matrix.md",
                "docs/platform/README.md",
                "docs/platform/architecture/README.md",
                "docs/platform/architecture/decisions/ADR-0000-template.md",
                "docs/platform/architecture/north_star.md",
                "docs/platform/architecture/tech_stack.md",
                "docs/platform/consumer/first_30_minutes.md",
                "docs/platform/consumer/quickstart.md",
                "docs/platform/consumer/app_onboarding.md",
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
                "docs/platform/modules/opensearch/README.md",
                "docs/platform/modules/dns/README.md",
                "docs/platform/modules/public-endpoints/README.md",
                "docs/platform/modules/secrets-manager/README.md",
                "docs/platform/modules/kms/README.md",
                "docs/platform/modules/identity-aware-proxy/README.md",
                "scripts/templates/blueprint/bootstrap/Makefile",
                "scripts/templates/blueprint/bootstrap/blueprint/contract.yaml",
                "scripts/templates/blueprint/bootstrap/docs/docusaurus.config.js",
                "scripts/templates/blueprint/bootstrap/docs/blueprint/architecture/decisions/README.md",
                "scripts/templates/blueprint/bootstrap/docs/blueprint/architecture/north_star.md",
                "scripts/templates/blueprint/bootstrap/docs/blueprint/architecture/tech_stack.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/architecture/README.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/architecture/decisions/ADR-0000-template.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/architecture/north_star.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/architecture/tech_stack.md",
                "scripts/templates/blueprint/bootstrap/make/blueprint.generated.mk.tmpl",
                "scripts/templates/blueprint/bootstrap/make/platform.mk",
                "scripts/templates/consumer/init/README.md.tmpl",
                "scripts/templates/consumer/init/AGENTS.md.tmpl",
                "scripts/templates/consumer/init/AGENTS.backlog.md.tmpl",
                "scripts/templates/consumer/init/AGENTS.decisions.md.tmpl",
                "scripts/templates/consumer/init/docs/README.md.tmpl",
                "scripts/templates/consumer/init/specs/README.md.tmpl",
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
                "scripts/templates/consumer/init/.agents/skills/blueprint-consumer-ops/SKILL.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-consumer-ops/agents/openai.yaml.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-consumer-ops/references/consumer_ops_checklist.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-intake-decompose/SKILL.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-intake-decompose/agents/openai.yaml.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-intake-decompose/references/intake_checklist.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-clarification-gate/SKILL.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-clarification-gate/agents/openai.yaml.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-clarification-gate/references/clarification_categories.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-plan-slicer/SKILL.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-plan-slicer/agents/openai.yaml.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-plan-slicer/references/plan_slice_checklist.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-traceability-keeper/SKILL.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-traceability-keeper/agents/openai.yaml.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-traceability-keeper/references/traceability_matrix_template.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-document-sync/SKILL.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-document-sync/agents/openai.yaml.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-document-sync/references/document_phase_checklist.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-pr-packager/SKILL.md.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-pr-packager/agents/openai.yaml.tmpl",
                "scripts/templates/consumer/init/.agents/skills/blueprint-sdd-pr-packager/references/pr_packaging_checklist.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/policy-mapping.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/control-catalog.yaml.tmpl",
                "scripts/templates/consumer/init/.spec-kit/control-catalog.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/architecture.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/adr.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/spec.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/plan.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/tasks.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/traceability.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/graph.yaml.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/evidence_manifest.json.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/context_pack.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/pr_context.md.tmpl",
                "scripts/templates/consumer/init/.spec-kit/templates/consumer/hardening_review.md.tmpl",
                "scripts/templates/consumer/scaffold/messaging/contracts/producer/.gitkeep",
                "scripts/templates/consumer/scaffold/messaging/contracts/consumer/.gitkeep",
                "scripts/templates/consumer/scaffold/messaging/sql/outbox.sql.tmpl",
                "scripts/templates/consumer/scaffold/messaging/sql/inbox.sql.tmpl",
                "scripts/templates/consumer/scaffold/messaging/sql/idempotency_keys.sql.tmpl",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/event_messaging_baseline.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/zero_downtime_evolution.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/tenant_context_propagation.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/runtime_credentials_eso.md",
                "scripts/templates/blueprint/bootstrap/docs/platform/consumer/app_onboarding.md",
                "scripts/templates/blueprint/bootstrap/docs/blueprint/governance/spec_driven_development.md",
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
                "scripts/bin/blueprint/spec_work_item_tools.py",
                "scripts/bin/infra/port_forward.sh",
                "scripts/lib/blueprint/upgrade_consumer.py",
                "scripts/lib/blueprint/upgrade_consumer_postcheck.py",
                "scripts/lib/blueprint/upgrade_preflight.py",
                "scripts/lib/blueprint/upgrade_reconcile_report.py",
                "scripts/lib/blueprint/upgrade_consumer_validate.py",
                "scripts/lib/blueprint/upgrade_report_metrics.py",
                "scripts/lib/blueprint/schemas/upgrade_plan.schema.json",
                "scripts/lib/blueprint/schemas/upgrade_apply.schema.json",
                "scripts/lib/blueprint/schemas/upgrade_reconcile_report.schema.json",
                "scripts/lib/blueprint/schemas/upgrade_postcheck.schema.json",
                "scripts/lib/blueprint/schemas/upgrade_validate.schema.json",
                "scripts/lib/docs/generate_contract_docs.py",
                "scripts/lib/docs/orchestrate_sync.py",
                "scripts/lib/docs/sync_blueprint_template_docs.py",
                "scripts/lib/docs/sync_platform_seed_docs.py",
                "scripts/lib/docs/sync_module_contract_summaries.py",
                "scripts/lib/spec_kit/render_control_catalog.py",
                "scripts/lib/spec_kit/sync_consumer_init_sdd_assets.py",
                "scripts/lib/spec_kit/render_policy_snippets.py",
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
                "scripts/bin/blueprint/spec_scaffold.py",
                "scripts/bin/blueprint/upgrade_consumer.sh",
                "scripts/bin/blueprint/upgrade_consumer_preflight.sh",
                "scripts/bin/blueprint/upgrade_consumer_validate.sh",
                "scripts/bin/blueprint/upgrade_consumer_postcheck.sh",
                "scripts/bin/blueprint/test_async_message_contracts_producer.sh",
                "scripts/bin/blueprint/test_async_message_contracts_consumer.sh",
                "scripts/bin/blueprint/test_async_message_contracts_all.sh",
                "scripts/bin/platform/auth/reconcile_eso_runtime_secrets.sh",
                "scripts/bin/platform/auth/runtime_identity_doctor.sh",
                "scripts/lib/platform/auth/runtime_identity_doctor_json.py",
                "scripts/bin/blueprint/render_module_wrapper_skeletons.sh",
                "scripts/bin/infra/destroy_disabled_modules.sh",
                "scripts/bin/infra/local_destroy_all.sh",
                "scripts/bin/infra/workload_health_check.py",
                "scripts/bin/quality/check_test_pyramid.py",
                "scripts/bin/quality/check_infra_shell_source_graph.py",
                "scripts/bin/quality/check_sdd_assets.py",
                "scripts/bin/quality/hardening_review.sh",
                "scripts/bin/quality/hooks_fast.sh",
                "scripts/bin/quality/hooks_run.sh",
                "scripts/bin/quality/hooks_strict.sh",
                "scripts/bin/quality/lint_docs.py",
                "scripts/bin/quality/render_core_targets_doc.py",
                "docs/docusaurus.config.js",
                "docs/blueprint/contracts/async_message_contracts.md",
                "docs/blueprint/governance/spec_driven_development.md",
                "docs/blueprint/architecture/north_star.md",
                "docs/blueprint/architecture/tech_stack.md",
                "docs/platform/architecture/north_star.md",
                "docs/platform/architecture/tech_stack.md",
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
                ".spec-kit/policy-mapping.md",
                ".spec-kit/control-catalog.yaml",
                ".spec-kit/control-catalog.md",
                ".spec-kit/templates/consumer/architecture.md",
                ".spec-kit/templates/consumer/adr.md",
                ".spec-kit/templates/consumer/spec.md",
                ".spec-kit/templates/consumer/plan.md",
                ".spec-kit/templates/consumer/tasks.md",
                ".spec-kit/templates/consumer/traceability.md",
                "specs/README.md",
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
        self.assertEqual(
            set(_extract_yaml_list(consumer_init, "source_artifact_prune_globs_on_init")),
            {
                "specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*",
                "docs/blueprint/architecture/decisions/ADR-*.md",
            },
        )

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
                "blueprint-install-codex-skill-consumer-ops",
                "blueprint-install-codex-skill-sdd-intake-decompose",
                "blueprint-install-codex-skill-sdd-clarification-gate",
                "blueprint-install-codex-skill-sdd-plan-slicer",
                "blueprint-install-codex-skill-sdd-traceability-keeper",
                "blueprint-install-codex-skill-sdd-document-sync",
                "blueprint-install-codex-skill-sdd-pr-packager",
                "blueprint-install-codex-skills",
                "blueprint-check-placeholders",
                "blueprint-template-smoke",
                "blueprint-bootstrap",
                "blueprint-clean-generated",
                "blueprint-render-makefile",
                "blueprint-render-module-wrapper-skeletons",
                "spec-scaffold",
                "spec-impact",
                "spec-evidence-manifest",
                "spec-context-pack",
                "spec-pr-context",
                "quality-hooks-fast",
                "quality-hooks-strict",
                "quality-infra-shell-source-graph-check",
                "quality-sdd-sync-control-catalog",
                "quality-sdd-check-control-catalog-sync",
                "quality-sdd-sync-consumer-init-assets",
                "quality-sdd-check-consumer-init-assets-sync",
                "quality-sdd-sync-policy-snippets",
                "quality-sdd-check-policy-snippets-sync",
                "quality-sdd-sync-all",
                "quality-sdd-check-all",
                "quality-sdd-check",
                "quality-hardening-review",
                "quality-ci-sync",
                "quality-ci-check-sync",
                "quality-docs-lint",
                "quality-docs-sync-all",
                "quality-docs-check-changed",
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
                "infra-port-forward-start",
                "infra-port-forward-stop",
                "infra-port-forward-cleanup",
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
                "auth-reconcile-runtime-identity",
                "auth-runtime-identity-doctor",
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

        sdd_contract = _extract_yaml_section(contract_lines, "spec_driven_development_contract")
        sdd_lifecycle = _extract_yaml_section(sdd_contract, "lifecycle")
        sdd_artifacts = _extract_yaml_section(sdd_contract, "artifacts")
        sdd_readiness = _extract_yaml_section(sdd_contract, "readiness_gate")
        sdd_normative = _extract_yaml_section(sdd_contract, "normative_language")
        self.assertEqual(_extract_yaml_scalar(sdd_contract, "enabled_by_default"), "true")
        self.assertEqual(
            _extract_yaml_list(sdd_lifecycle, "phases"),
            [
                "Discover",
                "High-Level Architecture",
                "Specify",
                "Plan",
                "Implement",
                "Verify",
                "Document",
                "Operate",
                "Publish",
            ],
        )
        self.assertEqual(_extract_yaml_scalar(sdd_artifacts, "policy_mapping_file"), ".spec-kit/policy-mapping.md")
        self.assertEqual(
            _extract_yaml_scalar(sdd_artifacts, "control_catalog_source_file"),
            ".spec-kit/control-catalog.yaml",
        )
        self.assertEqual(_extract_yaml_scalar(sdd_artifacts, "control_catalog_file"), ".spec-kit/control-catalog.md")
        self.assertIn("graph.yaml", _extract_yaml_list(sdd_artifacts, "required_work_item_documents"))
        self.assertIn("evidence_manifest.json", _extract_yaml_list(sdd_artifacts, "required_work_item_documents"))
        self.assertIn("context_pack.md", _extract_yaml_list(sdd_artifacts, "required_work_item_documents"))
        self.assertIn("pr_context.md", _extract_yaml_list(sdd_artifacts, "required_work_item_documents"))
        self.assertIn("hardening_review.md", _extract_yaml_list(sdd_artifacts, "required_work_item_documents"))
        self.assertIn(".spec-kit/templates/blueprint/adr.md", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn(".spec-kit/templates/consumer/adr.md", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn(".spec-kit/control-catalog.yaml", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn(".spec-kit/control-catalog.md", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn(
            "scripts/templates/consumer/init/.spec-kit/templates/consumer/adr.md.tmpl",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/templates/consumer/init/.spec-kit/control-catalog.yaml.tmpl",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/templates/consumer/init/.spec-kit/control-catalog.md.tmpl",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/bin/blueprint/spec_scaffold.py",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/bin/blueprint/spec_work_item_tools.py",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(".spec-kit/templates/blueprint/graph.yaml", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn(
            ".spec-kit/templates/blueprint/evidence_manifest.json",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            ".spec-kit/templates/blueprint/context_pack.md",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            ".spec-kit/templates/blueprint/pr_context.md",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            ".spec-kit/templates/blueprint/hardening_review.md",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(".spec-kit/templates/consumer/graph.yaml", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn(
            ".spec-kit/templates/consumer/evidence_manifest.json",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            ".spec-kit/templates/consumer/context_pack.md",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            ".spec-kit/templates/consumer/pr_context.md",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            ".spec-kit/templates/consumer/hardening_review.md",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/templates/consumer/init/.spec-kit/templates/consumer/graph.yaml.tmpl",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/templates/consumer/init/.spec-kit/templates/consumer/evidence_manifest.json.tmpl",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/templates/consumer/init/.spec-kit/templates/consumer/context_pack.md.tmpl",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/templates/consumer/init/.spec-kit/templates/consumer/pr_context.md.tmpl",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/templates/consumer/init/.spec-kit/templates/consumer/hardening_review.md.tmpl",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "scripts/lib/spec_kit/render_control_catalog.py",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn(
            "docs/blueprint/architecture/decisions/README.md",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        self.assertIn("docs/blueprint/architecture/north_star.md", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn("docs/blueprint/architecture/tech_stack.md", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn("docs/platform/architecture/README.md", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn("docs/platform/architecture/north_star.md", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn("docs/platform/architecture/tech_stack.md", _extract_yaml_list(sdd_artifacts, "required_paths"))
        self.assertIn(
            "docs/platform/architecture/decisions/ADR-0000-template.md",
            _extract_yaml_list(sdd_artifacts, "required_paths"),
        )
        sdd_governance = _extract_yaml_section(sdd_contract, "governance")
        sdd_control_catalog = _extract_yaml_section(sdd_governance, "control_catalog")
        sdd_spec_requirements = _extract_yaml_section(sdd_governance, "spec_requirements")
        self.assertEqual(_extract_yaml_scalar(sdd_control_catalog, "id_pattern"), "^SDD-C-[0-9]{3}$")
        self.assertIn("Control ID", _extract_yaml_list(sdd_control_catalog, "required_columns"))
        self.assertIn("fail", _extract_yaml_list(sdd_control_catalog, "allowed_gate_values"))
        self.assertEqual(
            _extract_yaml_scalar(sdd_spec_requirements, "control_section_heading_keyword"),
            "Applicable Guardrail Controls",
        )
        self.assertEqual(
            _extract_yaml_scalar(sdd_spec_requirements, "stack_profile_section_heading_keyword"),
            "Implementation Stack Profile",
        )
        self.assertIn(
            "Agent execution model",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_required_fields"),
        )
        self.assertIn(
            "Managed service preference",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_required_fields"),
        )
        self.assertIn(
            "Managed service exception rationale",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_required_fields"),
        )
        self.assertIn(
            "Runtime profile",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_required_fields"),
        )
        self.assertIn(
            "Local Kubernetes context policy",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_required_fields"),
        )
        self.assertIn(
            "Local provisioning stack",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_required_fields"),
        )
        self.assertIn(
            "Runtime identity baseline",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_required_fields"),
        )
        self.assertIn(
            "Local-first exception rationale",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_required_fields"),
        )
        self.assertIn(
            "specialized-subagents-isolated-worktrees",
            _extract_yaml_list(sdd_spec_requirements, "stack_profile_allowed_agent_execution_models"),
        )
        self.assertIn(
            "stackit-managed-first",
            _extract_yaml_list(sdd_spec_requirements, "managed_service_preference_allowed_values"),
        )
        self.assertIn(
            "local-first-docker-desktop-kubernetes",
            _extract_yaml_list(sdd_spec_requirements, "runtime_profile_allowed_values"),
        )
        self.assertIn(
            "docker-desktop-preferred",
            _extract_yaml_list(sdd_spec_requirements, "local_kube_context_policy_allowed_values"),
        )
        self.assertIn(
            "crossplane-plus-helm",
            _extract_yaml_list(sdd_spec_requirements, "local_provisioning_stack_allowed_values"),
        )
        self.assertIn(
            "eso-plus-argocd-plus-keycloak",
            _extract_yaml_list(sdd_spec_requirements, "runtime_identity_baseline_allowed_values"),
        )
        app_onboarding_contract = _extract_yaml_section(sdd_governance, "app_onboarding_contract")
        self.assertEqual(
            _extract_yaml_scalar(app_onboarding_contract, "required_plan_section_keyword"),
            "App Onboarding Contract",
        )
        self.assertEqual(
            _extract_yaml_scalar(app_onboarding_contract, "required_tasks_section_keyword"),
            "App Onboarding Minimum Targets",
        )
        self.assertIn(
            "infra-port-forward-start",
            _extract_yaml_list(app_onboarding_contract, "required_make_targets"),
        )
        publish_contract = _extract_yaml_section(sdd_governance, "publish_contract")
        self.assertIn("Summary", _extract_yaml_list(publish_contract, "required_pr_context_sections"))
        self.assertIn(
            "Repository-Wide Findings Fixed",
            _extract_yaml_list(publish_contract, "required_hardening_review_sections"),
        )
        self.assertIn("Validation Evidence", _extract_yaml_list(publish_contract, "required_pr_template_headings"))
        self.assertIn(
            ".github/pull_request_template.md",
            _extract_yaml_list(publish_contract, "required_pr_template_paths"),
        )
        escalation_contract = _extract_yaml_section(sdd_governance, "blueprint_defect_escalation_contract")
        self.assertEqual(
            _extract_yaml_scalar(escalation_contract, "required_spec_section_keyword"),
            "Blueprint Upstream Defect Escalation",
        )
        self.assertIn("Upstream issue URL", _extract_yaml_list(escalation_contract, "required_fields"))
        self.assertEqual(_extract_yaml_scalar(sdd_readiness, "status_field"), "SPEC_READY")
        self.assertEqual(_extract_yaml_scalar(sdd_readiness, "required_value"), "true")
        self.assertEqual(_extract_yaml_scalar(sdd_readiness, "blocked_marker"), "BLOCKED_MISSING_INPUTS")
        self.assertIn("Open questions count", _extract_yaml_list(sdd_readiness, "required_zero_fields"))
        self.assertIn("Pending assumptions count", _extract_yaml_list(sdd_readiness, "required_zero_fields"))
        self.assertIn("Open clarification markers count", _extract_yaml_list(sdd_readiness, "required_zero_fields"))
        self.assertIn("Product", _extract_yaml_list(sdd_readiness, "required_signoffs"))
        self.assertEqual(_extract_yaml_scalar(sdd_readiness, "adr_path_field"), "ADR path")
        self.assertEqual(_extract_yaml_scalar(sdd_readiness, "adr_status_field"), "ADR status")
        self.assertIn("approved", _extract_yaml_list(sdd_readiness, "adr_status_approved_values"))
        self.assertIn(
            "docs/blueprint/architecture/decisions/",
            _extract_yaml_list(sdd_readiness, "adr_path_allowed_prefixes"),
        )
        self.assertIn(
            "docs/platform/architecture/decisions/",
            _extract_yaml_list(sdd_readiness, "adr_path_allowed_prefixes"),
        )
        self.assertIn("Implementation", _extract_yaml_list(sdd_readiness, "implementation_sections"))
        self.assertEqual(_extract_yaml_scalar(sdd_readiness, "clarification_marker_token"), "NEEDS CLARIFICATION")
        self.assertEqual(_extract_yaml_scalar(sdd_readiness, "documentation_sync_required"), "true")
        self.assertIn("make docs-build", _extract_yaml_list(sdd_readiness, "documentation_validation_commands"))
        self.assertIn("make docs-smoke", _extract_yaml_list(sdd_readiness, "documentation_validation_commands"))
        self.assertEqual(_extract_yaml_scalar(sdd_normative, "normative_heading_keyword"), "Normative")
        self.assertEqual(_extract_yaml_scalar(sdd_normative, "informative_heading_keyword"), "Informative")
        self.assertIn(
            "should",
            _extract_yaml_list(sdd_normative, "forbidden_ambiguous_terms_in_normative_sections"),
        )
        self.assertIn("TBD", _extract_yaml_list(sdd_normative, "unresolved_marker_tokens"))
