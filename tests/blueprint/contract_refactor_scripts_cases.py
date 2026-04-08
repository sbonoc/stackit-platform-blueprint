from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class ScriptsRefactorCases(RefactorContractBase):
    def test_quality_hooks_require_shellcheck(self) -> None:
        hooks = _read("scripts/bin/quality/hooks_fast.sh")
        self.assertIn("require_command shellcheck", hooks)
        self.assertIn("--severity=error", hooks)
        self.assertNotIn("shellcheck not installed; skipping", hooks)

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

    def test_local_crossplane_bootstrap_waits_for_chart_deployment_names(self) -> None:
        bootstrap = _read("scripts/bin/infra/local_crossplane_bootstrap.sh")
        self.assertIn("deployment/crossplane", bootstrap)
        self.assertIn("deployment/crossplane-rbac-manager", bootstrap)
        self.assertNotIn('deployment/"$CROSSPLANE_HELM_RELEASE"', bootstrap)

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
        self.assertIn('audit_helm_chart_pin "KEYCLOAK_HELM_CHART_VERSION_PIN" "codecentric/keycloakx"', audit)
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
        self.assertIn('HELM_PREPARED_REPOS_CACHE="|"', tooling)
        self.assertIn('if [[ "$HELM_PREPARED_REPOS_CACHE" == *"|${repo_name}|"* ]]; then', tooling)
        self.assertIn('log_metric "helm_repo_prepare_total" "1" "repo=$repo_name status=cached"', tooling)
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

    def test_blueprint_bootstrap_seeds_templates_from_single_list(self) -> None:
        bootstrap = _read("scripts/bin/blueprint/bootstrap.sh")
        self.assertIn("local template_files=(", bootstrap)
        self.assertIn("ensure_blueprint_seed_file()", bootstrap)
        self.assertIn('"make/platform.mk"', bootstrap)
        self.assertIn('"blueprint/repo.init.env"', bootstrap)
        self.assertIn('"blueprint/repo.init.secrets.example.env"', bootstrap)
        self.assertIn('"contracts/async/pact/messages/producer/README.md"', bootstrap)
        self.assertIn('"contracts/async/pact/messages/consumer/README.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/quickstart.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/event_messaging_baseline.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/zero_downtime_evolution.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/tenant_context_propagation.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/runtime_credentials_eso.md"', bootstrap)
        self.assertIn('"docs/platform/consumer/first_30_minutes.md"', bootstrap)
        self.assertIn('"docs/blueprint/contracts/async_message_contracts.md"', bootstrap)
        self.assertIn('"docs/blueprint/governance/ownership_matrix.md"', bootstrap)
        self.assertIn('"docs/platform/modules/identity-aware-proxy/README.md"', bootstrap)
        self.assertIn('ensure_dir "$ROOT_DIR/docs/reference/generated"', bootstrap)
        self.assertIn('scripts/bin/quality/render_core_targets_doc.py', bootstrap)
        self.assertIn('docs/reference/generated/core_targets.generated.md', bootstrap)
        self.assertIn('scripts/lib/docs/generate_contract_docs.py', bootstrap)
        self.assertIn('docs/reference/generated/contract_metadata.generated.md', bootstrap)
        self.assertIn('scripts/lib/quality/render_ci_workflow.py', bootstrap)
        self.assertIn("blueprint_repo_is_generated_consumer", bootstrap)
        self.assertIn("skipping source CI workflow render in generated-consumer repo", bootstrap)
        self.assertIn("blueprint_ci_workflow_sync_total", bootstrap)
        self.assertIn('scripts/lib/docs/sync_platform_seed_docs.py', bootstrap)
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

    def test_quality_hooks_split_fast_and_strict_gates(self) -> None:
        hooks_fast = _read("scripts/bin/quality/hooks_fast.sh")
        hooks_run = _read("scripts/bin/quality/hooks_run.sh")
        hooks_strict = _read("scripts/bin/quality/hooks_strict.sh")
        self.assertIn("quality-docs-lint", hooks_fast)
        self.assertIn('source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"', hooks_fast)
        self.assertIn("blueprint_repo_is_generated_consumer", hooks_fast)
        self.assertIn("quality-ci-check-sync", hooks_fast)
        self.assertIn("quality_ci_check_sync_total", hooks_fast)
        self.assertIn("skipping quality-ci-check-sync in generated-consumer repo", hooks_fast)
        self.assertIn("quality-docs-check-blueprint-template-sync", hooks_fast)
        self.assertIn("quality-docs-check-platform-seed-sync", hooks_fast)
        self.assertIn("quality-docs-check-core-targets-sync", hooks_fast)
        self.assertIn("quality-docs-check-contract-metadata-sync", hooks_fast)
        self.assertIn("quality-docs-check-runtime-identity-summary-sync", hooks_fast)
        self.assertIn("quality-docs-check-module-contract-summaries-sync", hooks_fast)
        self.assertIn("quality-test-pyramid", hooks_fast)
        self.assertIn("infra-validate", hooks_fast)
        self.assertIn("infra-contract-test-fast", hooks_fast)
        self.assertIn("infra-audit-version", hooks_strict)
        self.assertIn("apps-audit-versions", hooks_strict)
        self.assertIn("hooks_fast.sh", hooks_run)
        self.assertIn("hooks_strict.sh", hooks_run)

    def test_quality_hooks_run_usage_mentions_composed_gates(self) -> None:
        hooks_run = _read("scripts/bin/quality/hooks_run.sh")
        self.assertIn("hooks_fast.sh", hooks_run)
        self.assertIn("hooks_strict.sh", hooks_run)

    def test_clean_generated_prunes_repo_wide_python_caches(self) -> None:
        clean_generated = _read("scripts/bin/blueprint/clean_generated.sh")
        self.assertIn('find "$ROOT_DIR" -type d -name \'__pycache__\'', clean_generated)
        self.assertIn('-name \'*.pyc\' -o -name \'*.pyo\'', clean_generated)
        self.assertNotIn('find "$ROOT_DIR/tests" -type d -name \'__pycache__\'', clean_generated)

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

    def test_argocd_reconcile_does_not_capture_kubectl_stdout_into_state_mode(self) -> None:
        reconcile = _read("scripts/bin/platform/auth/reconcile_argocd_repo_credentials.sh")
        self.assertIn("SOURCE_SECRET_SYNC_MODE_RESULT", reconcile)
        self.assertIn("if seed_argocd_source_secret_properties", reconcile)
        self.assertNotIn('source_secret_sync_mode="$(seed_argocd_source_secret_properties', reconcile)

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
        self.assertIn("resolve_app_catalog_scaffold_contract", init_contract_helpers)
        self.assertIn("consumer-owned seed already applied", init_contract_helpers)
        self.assertIn("expand_optional_module_path(", init_contract_helpers)

    def test_apps_bootstrap_keeps_only_canonical_app_dirs(self) -> None:
        apps_bootstrap = _read("scripts/bin/platform/apps/bootstrap.sh")
        catalog_template = _read("scripts/templates/platform/apps/catalog/manifest.yaml.tmpl")
        self.assertIn('ensure_dir "$ROOT_DIR/apps/backend"', apps_bootstrap)
        self.assertIn('ensure_dir "$ROOT_DIR/apps/touchpoints"', apps_bootstrap)
        self.assertIn('ensure_dir "$ROOT_DIR/apps/catalog"', apps_bootstrap)
        self.assertIn("APP_CATALOG_SCAFFOLD_ENABLED", apps_bootstrap)
        self.assertIn("APP_RUNTIME_GITOPS_ENABLED", apps_bootstrap)
        self.assertIn("catalog_scaffold_renderer.py", apps_bootstrap)
        self.assertIn("scripts/templates/platform/apps/catalog/manifest.yaml.tmpl", apps_bootstrap)
        self.assertIn("scripts/templates/platform/apps/catalog/versions.lock.tmpl", apps_bootstrap)
        self.assertIn("runtimeDeliveryContract", catalog_template)
        self.assertIn("--app-runtime-backend-image", apps_bootstrap)
        self.assertIn("app catalog scaffold disabled", apps_bootstrap)
        self.assertIn("app_catalog_scaffold_enabled_total", apps_bootstrap)
        self.assertIn("app_runtime_gitops_enabled_total", apps_bootstrap)
        self.assertNotIn('ensure_dir "$ROOT_DIR/apps/ingestion"', apps_bootstrap)

    def test_apps_smoke_honors_app_catalog_toggle(self) -> None:
        apps_smoke = _read("scripts/bin/platform/apps/smoke.sh")
        self.assertIn("APP_CATALOG_SCAFFOLD_ENABLED", apps_smoke)
        self.assertIn("APP_RUNTIME_GITOPS_ENABLED", apps_smoke)
        self.assertIn("APP_RUNTIME_MIN_WORKLOADS", apps_smoke)
        self.assertIn("app catalog scaffold mode mismatch", apps_smoke)
        self.assertIn("app runtime GitOps mode mismatch", apps_smoke)
        self.assertIn("run_runtime_workload_presence_check", apps_smoke)
        self.assertIn("empty-runtime-workloads", apps_smoke)
        self.assertIn("app-runtime-gitops-disabled", apps_smoke)
        self.assertIn("app_runtime_live_workload_presence_total", apps_smoke)
        self.assertIn("runtime_workload_check_reason", apps_smoke)
        self.assertIn("state_file_path apps_bootstrap", apps_smoke)
        self.assertIn("app catalog scaffold disabled; skipping apps/catalog smoke assertions", apps_smoke)
        self.assertIn("check_mode=skipped", apps_smoke)

    def test_infra_smoke_emits_empty_runtime_diagnostics(self) -> None:
        infra_smoke = _read("scripts/bin/infra/smoke.sh")
        smoke_artifacts = _read("scripts/lib/infra/smoke_artifacts.py")
        self.assertIn("APP_RUNTIME_MIN_WORKLOADS", infra_smoke)
        self.assertIn("--required-namespace-min-pods", infra_smoke)
        self.assertIn("smoke_artifacts.py", infra_smoke)
        self.assertIn("emptyRuntimeNamespaceCount", smoke_artifacts)
        self.assertIn("emptyRuntimeNamespaces", smoke_artifacts)
        self.assertIn("apps_smoke_failed", infra_smoke)
        self.assertIn("infra_smoke_component_status_total", infra_smoke)

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
            "scripts/bin/blueprint/test_async_message_contracts_producer.sh",
            "scripts/bin/blueprint/test_async_message_contracts_consumer.sh",
            "scripts/bin/blueprint/test_async_message_contracts_all.sh",
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
        async_contract_lib = _read("scripts/lib/blueprint/async_message_contracts.sh")
        self.assertIn("ASYNC_PACT_MESSAGE_CONTRACTS_ENABLED", async_contract_lib)
        self.assertIn("async_message_contracts_run_lane()", async_contract_lib)
        self.assertIn("async_pact_message_contract_lane_duration_seconds", async_contract_lib)

    def test_touchpoints_test_lanes_support_frontend_frameworks(self) -> None:
        testing = _read("scripts/lib/platform/testing.sh")
        pnpm_discovery = _read("scripts/lib/platform/pnpm_script_discovery.py")
        unit = _read("scripts/bin/platform/touchpoints/test_unit.sh")
        integration = _read("scripts/bin/platform/touchpoints/test_integration.sh")
        contracts = _read("scripts/bin/platform/touchpoints/test_contracts.sh")
        e2e = _read("scripts/bin/platform/touchpoints/test_e2e.sh")

        self.assertIn("_discover_pnpm_script_project_entries()", testing)
        self.assertIn("run_touchpoints_pnpm_lane()", testing)
        self.assertIn("pnpm_lane_duration_seconds", testing)
        self.assertIn("pnpm_script_discovery.py", testing)
        self.assertIn('"node_modules"', pnpm_discovery)
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
