from __future__ import annotations

from tests.blueprint.contract_refactor_shared import *  # noqa: F401,F403


class RuntimeIdentityRefactorCases(RefactorContractBase):
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

    def test_stackit_foundation_apply_retries_known_postgres_provider_race(self) -> None:
        foundation_apply = _read("scripts/bin/infra/stackit_foundation_apply.sh")

        self.assertIn('STACKIT_FOUNDATION_APPLY_MAX_ATTEMPTS', foundation_apply)
        self.assertIn('STACKIT_FOUNDATION_APPLY_RETRY_DELAY_SECONDS', foundation_apply)
        self.assertIn('stackit_foundation_apply_is_transient_postgres_notfound()', foundation_apply)
        self.assertIn('stackit_foundation_apply_attempt_total', foundation_apply)
        self.assertIn('stackit_foundation_apply_clear_transient_postgres_taint()', foundation_apply)
        self.assertIn('stackit_foundation_apply_untaint_total', foundation_apply)
        self.assertIn('transient STACKIT PostgresFlex create/read race detected', foundation_apply)

    def test_rabbitmq_smoke_accepts_managed_tls_uris(self) -> None:
        rabbitmq_smoke = _read("scripts/bin/infra/rabbitmq_smoke.sh")
        rabbitmq_lib = _read("scripts/lib/infra/rabbitmq.sh")

        self.assertIn("^uri=amqps?://", rabbitmq_smoke)
        self.assertIn('amqps://provider-generated:provider-generated@', rabbitmq_lib)

    def test_runtime_credentials_security_slice_is_seeded_and_template_synced(self) -> None:
        base_kustomization = _read("infra/gitops/platform/base/kustomization.yaml")
        base_kustomization_template = _read(
            "scripts/templates/infra/bootstrap/infra/gitops/platform/base/kustomization.yaml"
        )
        security_kustomization = _read("infra/gitops/platform/base/security/kustomization.yaml")
        security_kustomization_template = _read(
            "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/kustomization.yaml"
        )
        source_store = _read("infra/gitops/platform/base/security/runtime-source-store.yaml")
        source_store_template = _read(
            "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-source-store.yaml"
        )
        external_secret = _read("infra/gitops/platform/base/security/runtime-external-secrets-core.yaml")
        external_secret_template = _read(
            "scripts/templates/infra/bootstrap/infra/gitops/platform/base/security/runtime-external-secrets-core.yaml"
        )
        extensions_kustomization = _read("infra/gitops/platform/base/extensions/kustomization.yaml")

        self.assertIn("- security", base_kustomization)
        self.assertIn("- extensions", base_kustomization)
        self.assertEqual(base_kustomization, base_kustomization_template)
        self.assertIn("- runtime-source-store.yaml", security_kustomization)
        self.assertIn("- runtime-external-secrets-core.yaml", security_kustomization)
        self.assertEqual(security_kustomization, security_kustomization_template)
        self.assertIn("kind: ClusterSecretStore", source_store)
        self.assertIn("name: runtime-credentials-source-store", source_store)
        self.assertIn("- get", source_store)
        self.assertNotIn("- list", source_store)
        self.assertNotIn("- watch", source_store)
        self.assertEqual(source_store, source_store_template)
        self.assertIn("kind: ExternalSecret", external_secret)
        self.assertIn("name: runtime-credentials", external_secret)
        self.assertIn("name: keycloak-runtime-credentials", external_secret)
        self.assertIn("name: iap-runtime-credentials", external_secret)
        self.assertEqual(external_secret, external_secret_template)
        self.assertIn("resources: []", extensions_kustomization)

    def test_keycloak_is_mandatory_in_argocd_overlays(self) -> None:
        keycloak_template = _read("scripts/templates/infra/bootstrap/infra/gitops/argocd/core/keycloak.application.yaml.tmpl")
        self.assertIn("chart: keycloakx", keycloak_template)
        self.assertIn("namespace: {{KEYCLOAK_NAMESPACE}}", keycloak_template)
        self.assertIn("existingSecret: keycloak-runtime-credentials", keycloak_template)
        self.assertIn("{{KEYCLOAK_EXTRA_MANIFESTS_BLOCK}}", keycloak_template)

        local_overlay = _read("infra/gitops/argocd/overlays/local/kustomization.yaml")
        local_overlay_template = _read("scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/local/kustomization.yaml")
        dev_overlay = _read("infra/gitops/argocd/overlays/dev/kustomization.yaml")
        dev_overlay_template = _read("scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/dev/kustomization.yaml")
        stage_overlay = _read("infra/gitops/argocd/overlays/stage/kustomization.yaml")
        stage_overlay_template = _read("scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/stage/kustomization.yaml")
        prod_overlay = _read("infra/gitops/argocd/overlays/prod/kustomization.yaml")
        prod_overlay_template = _read("scripts/templates/infra/bootstrap/infra/gitops/argocd/overlays/prod/kustomization.yaml")

        self.assertIn("../../core/local/keycloak.yaml", local_overlay)
        self.assertIn("../../core/dev/keycloak.yaml", dev_overlay)
        self.assertIn("../../core/stage/keycloak.yaml", stage_overlay)
        self.assertIn("../../core/prod/keycloak.yaml", prod_overlay)
        self.assertEqual(local_overlay, local_overlay_template)
        self.assertEqual(dev_overlay, dev_overlay_template)
        self.assertEqual(stage_overlay, stage_overlay_template)
        self.assertEqual(prod_overlay, prod_overlay_template)

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
                self.assertIn("kind: Gateway\n", appproject)
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

    def test_stackit_runtime_inventory_exports_are_redacted_by_default(self) -> None:
        inventory = _read("scripts/bin/infra/stackit_runtime_inventory.sh")
        self.assertIn("print_export_or_missing()", inventory)
        self.assertIn("STACKIT_RUNTIME_INVENTORY_INCLUDE_SENSITIVE", inventory)
        self.assertIn("# %s=<redacted>", inventory)
        self.assertIn("STACKIT_WORKFLOWS_API_TOKEN", inventory)

    def test_keycloak_runtime_reconcile_and_credentials_contract_hardening(self) -> None:
        keycloak_identity_contract = _read("scripts/lib/infra/keycloak_identity_contract.sh")
        keycloak_lib = _read("scripts/lib/infra/keycloak.sh")
        workflows_lib = _read("scripts/lib/infra/workflows.sh")
        workflows_reconcile = _read("scripts/bin/infra/stackit_workflows_keycloak_reconcile.sh")
        foundation_seed = _read("scripts/bin/infra/stackit_foundation_seed_runtime_secret.sh")

        self.assertIn("keycloak_wait_for_runtime_pod()", keycloak_identity_contract)
        self.assertIn("KEYCLOAK_RUNTIME_WAIT_TIMEOUT_SECONDS", keycloak_identity_contract)
        self.assertIn("keycloak_runtime_pod_wait_seconds", keycloak_identity_contract)
        self.assertIn('normalize_bool "${PUBLIC_ENDPOINTS_ENABLED:-false}"', keycloak_lib)
        self.assertIn("keycloak_extra_manifests_block()", keycloak_lib)
        self.assertIn('set_default_env STACKIT_WORKFLOWS_ADMIN_PASSWORD ""', workflows_lib)
        self.assertIn('set_default_env STACKIT_WORKFLOWS_ADMIN_PASSWORD ""', workflows_reconcile)
        self.assertIn("KEYCLOAK_ADMIN_PASSWORD", foundation_seed)

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
