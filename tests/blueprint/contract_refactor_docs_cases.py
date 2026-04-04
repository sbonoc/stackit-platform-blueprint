from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class DocsRefactorCases(RefactorContractBase):
    def test_docs_generator_uses_schema_driven_contract_loader(self) -> None:
        docs_generator = _read("scripts/lib/docs/generate_contract_docs.py")
        self.assertIn("load_blueprint_contract", docs_generator)
        self.assertIn("load_module_contract", docs_generator)
        self.assertNotIn("def extract_scalar(", docs_generator)

    def test_bootstrap_docs_templates_are_synchronized(self) -> None:
        template_root = REPO_ROOT / "scripts/templates/blueprint/bootstrap"
        synced_docs = [
            "blueprint/contract.yaml",
            "docs/docusaurus.config.js",
            "docs/README.md",
            "docs/blueprint/README.md",
            "docs/blueprint/architecture/system_overview.md",
            "docs/blueprint/architecture/execution_model.md",
            "docs/blueprint/contracts/async_message_contracts.md",
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
        self.assertIn(
            "docs/platform/consumer/event_messaging_baseline.md",
            _extract_yaml_list(platform_docs, "required_seed_files"),
        )
        self.assertIn(
            "docs/platform/consumer/zero_downtime_evolution.md",
            _extract_yaml_list(platform_docs, "required_seed_files"),
        )
        self.assertIn(
            "docs/platform/consumer/tenant_context_propagation.md",
            _extract_yaml_list(platform_docs, "required_seed_files"),
        )
        self.assertIn(
            "docs/platform/consumer/runtime_credentials_eso.md",
            _extract_yaml_list(platform_docs, "required_seed_files"),
        )

        self.assertIn('"docs/platform/consumer/quickstart.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/endpoint_exposure_model.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/protected_api_routes.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/event_messaging_baseline.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/zero_downtime_evolution.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/tenant_context_propagation.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/runtime_credentials_eso.md"', bootstrap)
        self.assertIn("if [[ -f \"$path\" ]]; then", bootstrap_lib)
        self.assertIn("_validate_platform_docs_seed_contract", validate_py)
        self.assertNotIn('"docs/platform/consumer/quickstart.md",', validate_py)
        platform_readme = _read("docs/platform/README.md")
        self.assertIn("[Event Messaging Baseline](consumer/event_messaging_baseline.md)", platform_readme)
        self.assertIn("[Zero-Downtime Evolution](consumer/zero_downtime_evolution.md)", platform_readme)
        self.assertIn("[Tenant Context Propagation](consumer/tenant_context_propagation.md)", platform_readme)

    def test_docs_readme_points_to_command_discovery(self) -> None:
        docs_readme = _read("docs/README.md")
        self.assertIn("make quality-hooks-fast", docs_readme)
        self.assertIn("make quality-hooks-strict", docs_readme)
        self.assertIn("make quality-hooks-run", docs_readme)
        self.assertIn("make quality-docs-lint", docs_readme)
        self.assertIn("make quality-docs-check-blueprint-template-sync", docs_readme)
        self.assertIn("make quality-docs-sync-module-contract-summaries", docs_readme)
        self.assertIn("make quality-test-pyramid", docs_readme)
        self.assertIn("make docs-run", docs_readme)
        self.assertIn("make infra-context", docs_readme)
        self.assertIn("make infra-status-json", docs_readme)
        self.assertIn("make infra-local-destroy-all", docs_readme)
        self.assertIn("make infra-stackit-destroy-all", docs_readme)
        self.assertIn("make blueprint-bootstrap", docs_readme)
        self.assertIn("make blueprint-resync-consumer-seeds", docs_readme)
        self.assertIn("make blueprint-upgrade-consumer", docs_readme)
        self.assertIn("make blueprint-upgrade-consumer-validate", docs_readme)
        self.assertIn("make blueprint-install-codex-skill", docs_readme)
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
        self.assertIn("[Event Messaging Baseline](platform/consumer/event_messaging_baseline.md)", docs_readme)
        self.assertIn("[Zero-Downtime Evolution](platform/consumer/zero_downtime_evolution.md)", docs_readme)
        self.assertIn("[Tenant Context Propagation](platform/consumer/tenant_context_propagation.md)", docs_readme)
        self.assertIn("[Core Make Targets (Generated)](reference/generated/core_targets.generated.md)", docs_readme)
        self.assertIn("artifacts/infra/workload_health.json", docs_readme)
        self.assertIn(
            "[Async Message Contracts (Pact)](contracts/async_message_contracts.md)",
            _read("docs/blueprint/README.md"),
        )

    def test_consumer_quickstart_mentions_status_snapshot_and_no_duplicate_smoke(self) -> None:
        quickstart = _read("docs/platform/consumer/quickstart.md")
        self.assertIn("make blueprint-resync-consumer-seeds", quickstart)
        self.assertIn("make blueprint-upgrade-consumer", quickstart)
        self.assertIn("make blueprint-upgrade-consumer-validate", quickstart)
        self.assertIn("make blueprint-install-codex-skill", quickstart)
        self.assertIn("remote.upstream.url", quickstart)
        self.assertIn("remote.origin.url", quickstart)
        self.assertIn("make infra-context", quickstart)
        self.assertIn("make infra-provision-deploy", quickstart)
        self.assertIn("make infra-status-json", quickstart)
        self.assertIn("LOCAL_KUBE_CONTEXT", quickstart)
        self.assertIn("[Endpoint Exposure Model](endpoint_exposure_model.md)", quickstart)
        self.assertIn("[Protected API Routes](protected_api_routes.md)", quickstart)
        self.assertIn("[Event Messaging Baseline](event_messaging_baseline.md)", quickstart)
        self.assertIn("[Zero-Downtime Evolution](zero_downtime_evolution.md)", quickstart)
        self.assertIn("[Tenant Context Propagation](tenant_context_propagation.md)", quickstart)
        self.assertIn("artifacts/infra/infra_status_snapshot.json", quickstart)
        self.assertIn("artifacts/infra/workload_health.json", quickstart)
        self.assertNotIn("make infra-smoke", quickstart)

    def test_blueprint_execution_model_mentions_upgrade_workflow_and_is_template_synced(self) -> None:
        execution_model = _read("docs/blueprint/architecture/execution_model.md")
        execution_model_template = _read(
            "scripts/templates/blueprint/bootstrap/docs/blueprint/architecture/execution_model.md"
        )
        self.assertIn("make blueprint-resync-consumer-seeds", execution_model)
        self.assertIn("make blueprint-upgrade-consumer", execution_model)
        self.assertIn("make blueprint-upgrade-consumer-validate", execution_model)
        self.assertEqual(execution_model, execution_model_template)

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

    def test_runtime_policy_guides_are_seeded_and_template_synced(self) -> None:
        event_messaging = _read("docs/platform/consumer/event_messaging_baseline.md")
        event_messaging_template = _read(
            "scripts/templates/blueprint/bootstrap/docs/platform/consumer/event_messaging_baseline.md"
        )
        zero_downtime = _read("docs/platform/consumer/zero_downtime_evolution.md")
        zero_downtime_template = _read(
            "scripts/templates/blueprint/bootstrap/docs/platform/consumer/zero_downtime_evolution.md"
        )
        tenant_context = _read("docs/platform/consumer/tenant_context_propagation.md")
        tenant_context_template = _read(
            "scripts/templates/blueprint/bootstrap/docs/platform/consumer/tenant_context_propagation.md"
        )

        self.assertIn("EVENT_MESSAGING_BASELINE_ENABLED", event_messaging)
        self.assertIn("Python / FastAPI", event_messaging)
        self.assertIn("JS/TS runtime", event_messaging)
        self.assertEqual(event_messaging, event_messaging_template)

        self.assertIn("ZERO_DOWNTIME_EVOLUTION_ENABLED", zero_downtime)
        self.assertIn("expand", zero_downtime)
        self.assertIn("migrate", zero_downtime)
        self.assertIn("contract", zero_downtime)
        self.assertEqual(zero_downtime, zero_downtime_template)

        self.assertIn("TENANT_CONTEXT_PROPAGATION_ENABLED", tenant_context)
        self.assertIn("X-Tenant-ID", tenant_context)
        self.assertIn("X-Organization-ID", tenant_context)
        self.assertIn("X-Correlation-ID", tenant_context)
        self.assertEqual(tenant_context, tenant_context_template)

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

    def test_ci_workflows_and_docs_exist(self) -> None:
        ci_workflow = _read(".github/workflows/ci.yml")
        consumer_ci_template = _read("scripts/templates/consumer/init/.github/workflows/ci.yml.tmpl")
        shared_ci_action = _read(".github/actions/prepare-blueprint-ci/action.yml")
        platform_make = _read("make/platform.mk")
        platform_make_template = _read("scripts/templates/blueprint/bootstrap/make/platform.mk")
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
        self.assertIn("Bootstrap project dependencies for clean runners", shared_ci_action)
        self.assertIn("make apps-ci-bootstrap", shared_ci_action)
        self.assertIn("BLUEPRINT_PROFILE=local-lite OBSERVABILITY_ENABLED=false make apps-ci-bootstrap", shared_ci_action)
        self.assertIn("Ensure CI CLI prerequisites", shared_ci_action)
        self.assertIn("make infra-prereqs", shared_ci_action)
        self.assertNotIn("discover_python_bootstrap_projects()", shared_ci_action)
        self.assertNotIn("playwright install --with-deps chromium", shared_ci_action)
        self.assertIn("uses: actions/setup-python@v6", shared_ci_action)
        self.assertIn("uses: actions/setup-node@v6", shared_ci_action)
        self.assertNotIn("uses: actions/setup-python@v5", shared_ci_action)
        self.assertNotIn("uses: actions/setup-node@v4", shared_ci_action)
        self.assertIn("platform-blueprint-maintainers", source_codeowners)
        self.assertIn("Describe the blueprint change.", source_pr_template)
        self.assertIn("Blueprint Bug Report", source_bug_template)
        self.assertIn("generated repository", consumer_codeowners_template)
        self.assertIn("Describe the project change.", consumer_pr_template)
        self.assertIn("Project Bug Report", consumer_bug_template)
        self.assertIn("blueprint-quality:", ci_workflow)
        self.assertIn("generated-consumer-smoke:", ci_workflow)
        self.assertIn('run_cmd make -C "$ROOT_DIR" infra-validate', hooks_fast)
        self.assertNotIn('pytest -q tests', ci_workflow)
        self.assertNotIn('pytest -q tests/tooling', ci_workflow)
        self.assertIn('Prepare shared CI baseline', ci_workflow)
        self.assertIn('uses: ./.github/actions/prepare-blueprint-ci', ci_workflow)
        self.assertEqual(ci_workflow.count('uses: actions/checkout@v6'), 2)
        self.assertNotIn('uses: actions/checkout@v4', ci_workflow)
        self.assertIn('Run quality gates', ci_workflow)
        self.assertIn('make quality-ci-blueprint', ci_workflow)
        self.assertIn('Run canonical full e2e lane on main updates', ci_workflow)
        self.assertIn("if: github.event_name == 'push'", ci_workflow)
        self.assertIn('make quality-ci-full-e2e', ci_workflow)
        self.assertIn('Smoke generated consumer baseline', ci_workflow)
        self.assertIn('make quality-ci-generated-consumer-smoke', ci_workflow)
        self.assertNotIn('Shell script lint', ci_workflow)
        self.assertNotIn('make apps-audit-versions', ci_workflow)
        self.assertEqual(consumer_ci_template.count('uses: ./.github/actions/prepare-blueprint-ci'), 2)
        self.assertEqual(consumer_ci_template.count('uses: actions/checkout@v6'), 2)
        self.assertNotIn('uses: actions/checkout@v4', consumer_ci_template)
        self.assertIn('Run fast quality gate', consumer_ci_template)
        self.assertIn('make quality-ci-fast', consumer_ci_template)
        self.assertIn('make quality-ci-full-e2e', consumer_ci_template)
        self.assertIn('Run strict audit gate', consumer_ci_template)
        self.assertIn('make quality-ci-strict', consumer_ci_template)
        self.assertIn('python3 -m pytest -q tests', consumer_ci_template)
        self.assertNotIn('run: pytest -q tests', consumer_ci_template)
        self.assertIn('apps-ci-bootstrap-consumer', platform_make)
        self.assertIn('@$(MAKE) apps-ci-bootstrap-consumer', platform_make)
        self.assertIn('apps-ci-bootstrap-consumer placeholder active', platform_make)
        self.assertNotIn('apps/backend/requirements.txt', platform_make)
        self.assertNotIn('pnpm --dir apps/touchpoints install', platform_make)
        self.assertIn('apps-ci-bootstrap-consumer', platform_make_template)
        self.assertIn('@$(MAKE) apps-ci-bootstrap-consumer', platform_make_template)
        self.assertIn('apps-ci-bootstrap-consumer placeholder active', platform_make_template)
        self.assertNotIn('apps/backend/requirements.txt', platform_make_template)
        self.assertNotIn('pnpm --dir apps/touchpoints install', platform_make_template)
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
