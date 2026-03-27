from __future__ import annotations

import unittest
from tests._shared.helpers import (
    REPO_ROOT,
    module_flags_env,
    prune_optional_scaffolding,
    run,
    run_render_and_infra_bootstrap,
)


class OptionalModulesTests(unittest.TestCase):
    def setUp(self) -> None:
        prune_optional_scaffolding()

    def tearDown(self) -> None:
        prune_optional_scaffolding()
        reset_env = module_flags_env()
        reset = run_render_and_infra_bootstrap(reset_env)
        self.assertEqual(reset.returncode, 0, msg=reset.stdout + reset.stderr)

    def test_optional_module_make_targets_materialize_only_when_enabled(self) -> None:
        disabled_env = module_flags_env()
        disabled_bootstrap = run_render_and_infra_bootstrap(disabled_env)
        self.assertEqual(disabled_bootstrap.returncode, 0, msg=disabled_bootstrap.stdout + disabled_bootstrap.stderr)
        disabled_help = run(["make", "help"], disabled_env)
        self.assertEqual(disabled_help.returncode, 0, msg=disabled_help.stdout + disabled_help.stderr)
        self.assertNotIn("infra-observability-plan", disabled_help.stdout)
        self.assertNotIn("infra-stackit-workflows-plan", disabled_help.stdout)
        self.assertNotIn("infra-langfuse-plan", disabled_help.stdout)
        self.assertNotIn("infra-postgres-plan", disabled_help.stdout)
        self.assertNotIn("infra-neo4j-plan", disabled_help.stdout)
        self.assertNotIn("infra-object-storage-plan", disabled_help.stdout)
        self.assertNotIn("infra-rabbitmq-plan", disabled_help.stdout)
        self.assertNotIn("infra-dns-plan", disabled_help.stdout)
        self.assertNotIn("infra-public-endpoints-plan", disabled_help.stdout)
        self.assertNotIn("infra-secrets-manager-plan", disabled_help.stdout)
        self.assertNotIn("infra-kms-plan", disabled_help.stdout)
        self.assertNotIn("infra-identity-aware-proxy-plan", disabled_help.stdout)

        langfuse_env = module_flags_env(profile="stackit-dev", langfuse="true")
        langfuse_bootstrap = run_render_and_infra_bootstrap(langfuse_env)
        self.assertEqual(langfuse_bootstrap.returncode, 0, msg=langfuse_bootstrap.stdout + langfuse_bootstrap.stderr)
        langfuse_help = run(["make", "help"], langfuse_env)
        self.assertEqual(langfuse_help.returncode, 0, msg=langfuse_help.stdout + langfuse_help.stderr)
        self.assertIn("infra-langfuse-plan", langfuse_help.stdout)
        self.assertIn("infra-langfuse-apply", langfuse_help.stdout)
        self.assertNotIn("infra-stackit-workflows-plan", langfuse_help.stdout)
        self.assertNotIn("infra-postgres-plan", langfuse_help.stdout)
        self.assertNotIn("infra-neo4j-plan", langfuse_help.stdout)
        self.assertNotIn("infra-object-storage-plan", langfuse_help.stdout)
        self.assertNotIn("infra-rabbitmq-plan", langfuse_help.stdout)
        self.assertNotIn("infra-dns-plan", langfuse_help.stdout)
        self.assertNotIn("infra-public-endpoints-plan", langfuse_help.stdout)
        self.assertNotIn("infra-secrets-manager-plan", langfuse_help.stdout)
        self.assertNotIn("infra-kms-plan", langfuse_help.stdout)
        self.assertNotIn("infra-identity-aware-proxy-plan", langfuse_help.stdout)

    def test_destroy_disabled_modules_target_executes_disabled_module_destroy_flow(self) -> None:
        env = module_flags_env(profile="local-full", postgres="true")
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        destroy = run(["make", "infra-destroy-disabled-modules"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)
        self.assertIn("module_action_disabled_count", destroy.stdout + destroy.stderr)

        state_file = REPO_ROOT / "artifacts" / "infra" / "destroy_disabled_modules.env"
        self.assertTrue(state_file.exists(), msg="disabled-module destroy state file not found")
        state_content = state_file.read_text(encoding="utf-8")
        self.assertIn("enabled_modules=postgres", state_content)
        self.assertIn("disabled_modules=", state_content)
        self.assertNotIn("disabled_modules=none", state_content)
        self.assertNotIn("disabled_modules=postgres", state_content)

    def test_local_destroy_all_writes_state_and_preserves_cluster_scope(self) -> None:
        env = module_flags_env(profile="local-full", postgres="true", object_storage="true")
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        destroy = run(["make", "infra-local-destroy-all"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

        state_file = REPO_ROOT / "artifacts" / "infra" / "local_destroy_all.env"
        self.assertTrue(state_file.exists(), msg="local destroy-all state file not found")
        state_content = state_file.read_text(encoding="utf-8")
        self.assertIn("destroy_scope=local_cluster_resources", state_content)
        self.assertIn(
            "destroyed_modules=observability,langfuse,postgres,neo4j,object-storage,rabbitmq,dns,public-endpoints,secrets-manager,kms,identity-aware-proxy",
            state_content,
        )

    def test_infra_bootstrap_prunes_stale_optional_scaffolding_when_flags_disabled(self) -> None:
        enabled_env = module_flags_env(
            profile="stackit-dev",
            workflows="true",
            langfuse="true",
            postgres="true",
            neo4j="true",
            object_storage="true",
            rabbitmq="true",
            dns="true",
            public_endpoints="true",
            secrets_manager="true",
            kms="true",
            identity_aware_proxy="true",
        )
        enabled = run_render_and_infra_bootstrap(enabled_env)
        self.assertEqual(enabled.returncode, 0, msg=enabled.stdout + enabled.stderr)

        expected_when_enabled = [
            "dags",
            "infra/cloud/stackit/terraform/modules/workflows",
            "infra/cloud/stackit/terraform/modules/langfuse",
            "infra/cloud/stackit/terraform/modules/postgres",
            "infra/cloud/stackit/terraform/modules/neo4j",
            "infra/cloud/stackit/terraform/modules/object-storage",
            "infra/cloud/stackit/terraform/modules/rabbitmq",
            "infra/cloud/stackit/terraform/modules/dns",
            "infra/cloud/stackit/terraform/modules/public-endpoints",
            "infra/cloud/stackit/terraform/modules/secrets-manager",
            "infra/cloud/stackit/terraform/modules/kms",
            "infra/cloud/stackit/terraform/modules/identity-aware-proxy",
            "infra/local/helm/langfuse",
            "infra/local/helm/postgres",
            "infra/local/helm/neo4j",
            "infra/local/helm/object-storage",
            "infra/local/helm/rabbitmq",
            "infra/local/helm/public-endpoints",
            "infra/local/helm/identity-aware-proxy",
            "tests/infra/modules/workflows",
            "tests/infra/modules/langfuse",
            "tests/infra/modules/postgres",
            "tests/infra/modules/neo4j",
            "tests/infra/modules/object-storage",
            "tests/infra/modules/rabbitmq",
            "tests/infra/modules/dns",
            "tests/infra/modules/public-endpoints",
            "tests/infra/modules/secrets-manager",
            "tests/infra/modules/kms",
            "tests/infra/modules/identity-aware-proxy",
            "infra/gitops/argocd/optional/dev/workflows.yaml",
            "infra/gitops/argocd/optional/dev/langfuse.yaml",
            "infra/gitops/argocd/optional/dev/neo4j.yaml",
            "infra/gitops/argocd/optional/dev/public-endpoints.yaml",
            "infra/gitops/argocd/optional/dev/identity-aware-proxy.yaml",
        ]
        for relative in expected_when_enabled:
            self.assertTrue((REPO_ROOT / relative).exists(), msg=f"expected path not materialized: {relative}")

        disabled_env = module_flags_env(profile="stackit-dev")
        disabled = run_render_and_infra_bootstrap(disabled_env)
        self.assertEqual(disabled.returncode, 0, msg=disabled.stdout + disabled.stderr)

        expected_pruned_paths = [
            "dags",
            "infra/cloud/stackit/terraform/modules/workflows",
            "infra/cloud/stackit/terraform/modules/langfuse",
            "infra/cloud/stackit/terraform/modules/postgres",
            "infra/cloud/stackit/terraform/modules/neo4j",
            "infra/cloud/stackit/terraform/modules/object-storage",
            "infra/cloud/stackit/terraform/modules/rabbitmq",
            "infra/cloud/stackit/terraform/modules/dns",
            "infra/cloud/stackit/terraform/modules/public-endpoints",
            "infra/cloud/stackit/terraform/modules/secrets-manager",
            "infra/cloud/stackit/terraform/modules/kms",
            "infra/cloud/stackit/terraform/modules/identity-aware-proxy",
            "infra/local/helm/langfuse",
            "infra/local/helm/postgres",
            "infra/local/helm/neo4j",
            "infra/local/helm/object-storage",
            "infra/local/helm/rabbitmq",
            "infra/local/helm/public-endpoints",
            "infra/local/helm/identity-aware-proxy",
            "tests/infra/modules/workflows",
            "tests/infra/modules/langfuse",
            "tests/infra/modules/postgres",
            "tests/infra/modules/neo4j",
            "tests/infra/modules/object-storage",
            "tests/infra/modules/rabbitmq",
            "tests/infra/modules/dns",
            "tests/infra/modules/public-endpoints",
            "tests/infra/modules/secrets-manager",
            "tests/infra/modules/kms",
            "tests/infra/modules/identity-aware-proxy",
            "infra/gitops/argocd/optional/dev/workflows.yaml",
            "infra/gitops/argocd/optional/dev/langfuse.yaml",
            "infra/gitops/argocd/optional/dev/neo4j.yaml",
            "infra/gitops/argocd/optional/dev/public-endpoints.yaml",
            "infra/gitops/argocd/optional/dev/identity-aware-proxy.yaml",
        ]
        for relative in expected_pruned_paths:
            self.assertFalse((REPO_ROOT / relative).exists(), msg=f"expected path not pruned: {relative}")

    def test_observability_module_flow(self) -> None:
        env = module_flags_env(observability="true")
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)
        steps = [
            "infra-observability-plan",
            "infra-observability-apply",
            "infra-observability-deploy",
            "infra-observability-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_state = (REPO_ROOT / "artifacts" / "infra" / "observability_runtime.env").read_text(encoding="utf-8")
        self.assertIn("otel_endpoint=http", runtime_state)
        self.assertIn("faro_collect_path=/collect", runtime_state)

        destroy = run(["make", "infra-observability-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)
        self.assertFalse((REPO_ROOT / "artifacts" / "infra" / "observability_runtime.env").exists())

    def test_workflows_module_flow(self) -> None:
        env = module_flags_env(profile="stackit-dev", workflows="true")
        env.update(
            {
                "STACKIT_PROJECT_ID": "project-001",
                "STACKIT_REGION": "eu01",
                "STACKIT_WORKFLOWS_DAGS_REPO_URL": "https://github.com/example/platform.git",
                "STACKIT_WORKFLOWS_DAGS_REPO_BRANCH": "main",
                "STACKIT_WORKFLOWS_DAGS_REPO_USERNAME": "github_pat",
                "STACKIT_WORKFLOWS_DAGS_REPO_TOKEN": "token-value",
                "STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL": "https://auth.example/realms/workflows/.well-known/openid-configuration",
                "STACKIT_WORKFLOWS_OIDC_CLIENT_ID": "stackit-workflows-dev",
                "STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET": "secret-value",
                "STACKIT_OBSERVABILITY_INSTANCE_ID": "obs-001",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)
        steps = [
            "infra-stackit-workflows-plan",
            "infra-stackit-workflows-apply",
            "infra-stackit-workflows-reconcile",
            "infra-stackit-workflows-dag-deploy",
            "infra-stackit-workflows-dag-parse-smoke",
            "infra-stackit-workflows-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        self.assertTrue((REPO_ROOT / "artifacts" / "infra" / "workflows_instance.env").exists())
        plan_state = (REPO_ROOT / "artifacts" / "infra" / "workflows_plan.env").read_text(encoding="utf-8")
        self.assertIn("provision_driver=api_contract", plan_state)

        destroy = run(["make", "infra-stackit-workflows-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)
        self.assertFalse((REPO_ROOT / "artifacts" / "infra" / "workflows_instance.env").exists())

    def test_langfuse_module_flow(self) -> None:
        env = module_flags_env(profile="stackit-dev", langfuse="true")
        env.update(
            {
                "LANGFUSE_PUBLIC_DOMAIN": "dhe-langfuse-dev.runs.onstackit.cloud",
                "LANGFUSE_OIDC_ISSUER_URL": "https://auth.example/realms/langfuse",
                "LANGFUSE_OIDC_CLIENT_ID": "langfuse-dev",
                "LANGFUSE_OIDC_CLIENT_SECRET": "secret-value",
                "LANGFUSE_DATABASE_URL": "postgresql://langfuse:secret@postgres:5432/langfuse",
                "LANGFUSE_SALT": "salt-value",
                "LANGFUSE_ENCRYPTION_KEY": "encryption-key",
                "LANGFUSE_NEXTAUTH_SECRET": "nextauth-secret",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)
        steps = [
            "infra-langfuse-plan",
            "infra-langfuse-apply",
            "infra-langfuse-deploy",
            "infra-langfuse-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        self.assertTrue((REPO_ROOT / "artifacts" / "infra" / "langfuse_deploy.env").exists())
        plan_state = (REPO_ROOT / "artifacts" / "infra" / "langfuse_plan.env").read_text(encoding="utf-8")
        self.assertIn("provision_driver=argocd_optional_manifest", plan_state)
        destroy = run(["make", "infra-langfuse-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_postgres_module_flow(self) -> None:
        env = module_flags_env(profile="stackit-dev", postgres="true")
        env.update(
            {
                "POSTGRES_INSTANCE_NAME": "bp-postgres-dev",
                "POSTGRES_DB_NAME": "appdb",
                "POSTGRES_USER": "appuser",
                "POSTGRES_PASSWORD": "apppass",
                "POSTGRES_EXTRA_ALLOWED_CIDRS": "192.168.0.0/24",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)
        steps = [
            "infra-postgres-plan",
            "infra-postgres-apply",
            "infra-postgres-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "postgres_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("dsn=postgresql://", runtime_content)
        self.assertIn("provision_driver=foundation_contract", runtime_content)
        destroy = run(["make", "infra-postgres-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_local_postgres_module_renders_release_aligned_values(self) -> None:
        env = module_flags_env(postgres="true")
        env.update(
            {
                "POSTGRES_INSTANCE_NAME": "bp-postgres-local",
                "POSTGRES_DB_NAME": "appdb",
                "POSTGRES_USER": "appuser",
                "POSTGRES_PASSWORD": "apppass",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        for step in ("infra-postgres-plan", "infra-postgres-apply", "infra-postgres-smoke"):
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        rendered_values = (REPO_ROOT / "artifacts" / "infra" / "rendered" / "postgres.values.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn('fullnameOverride: "blueprint-postgres"', rendered_values)
        self.assertIn('repository: "bitnamilegacy/postgresql"', rendered_values)
        self.assertIn('tag: "16.4.0-debian-12-r14"', rendered_values)
        self.assertIn('database: "appdb"', rendered_values)

        destroy = run(["make", "infra-postgres-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_neo4j_module_flow(self) -> None:
        env = module_flags_env(profile="stackit-dev", neo4j="true")
        env.update(
            {
                "NEO4J_AUTH_USERNAME": "neo4j",
                "NEO4J_AUTH_PASSWORD": "neo4j-pass",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)
        steps = [
            "infra-neo4j-plan",
            "infra-neo4j-apply",
            "infra-neo4j-deploy",
            "infra-neo4j-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "neo4j_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("uri=bolt://", runtime_content)
        self.assertIn("provision_driver=argocd_optional_manifest", runtime_content)
        destroy = run(["make", "infra-neo4j-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_object_storage_module_flow(self) -> None:
        env = module_flags_env(object_storage="true")
        env.update({"OBJECT_STORAGE_BUCKET_NAME": "marketplace-assets-dev"})
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        steps = [
            "infra-object-storage-plan",
            "infra-object-storage-apply",
            "infra-object-storage-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "object_storage_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("endpoint=http://", runtime_content)
        self.assertIn("bucket=marketplace-assets-dev", runtime_content)
        rendered_values = (REPO_ROOT / "artifacts" / "infra" / "rendered" / "object-storage.values.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("docker.io", rendered_values)
        self.assertIn('repository: "bitnamilegacy/minio"', rendered_values)
        self.assertIn("allowInsecureImages: true", rendered_values)
        self.assertIn('defaultBuckets: "marketplace-assets-dev"', rendered_values)
        self.assertIn('fullnameOverride: "blueprint-object-storage"', rendered_values)

        destroy = run(["make", "infra-object-storage-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_rabbitmq_module_flow(self) -> None:
        env = module_flags_env(rabbitmq="true")
        env.update(
            {
                "RABBITMQ_INSTANCE_NAME": "marketplace-rmq",
                "RABBITMQ_USERNAME": "marketplace",
                "RABBITMQ_PASSWORD": "marketplace-secret",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        steps = [
            "infra-rabbitmq-plan",
            "infra-rabbitmq-apply",
            "infra-rabbitmq-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "rabbitmq_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("uri=amqp://", runtime_content)
        self.assertIn("host=blueprint-rabbitmq.messaging.svc.cluster.local", runtime_content)
        self.assertIn("password=marketplace-secret", runtime_content)
        self.assertIn("provision_path=", runtime_content)
        rendered_values = (REPO_ROOT / "artifacts" / "infra" / "rendered" / "rabbitmq.values.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn('repository: "bitnamilegacy/rabbitmq"', rendered_values)
        self.assertIn('tag: "3.13.7-debian-12-r2"', rendered_values)

        secret_manifest = (
            REPO_ROOT / "artifacts" / "infra" / "rendered" / "secrets" / "secret-messaging-blueprint-rabbitmq-auth.yaml"
        )
        self.assertTrue(secret_manifest.exists(), msg="rabbitmq secret manifest not rendered")

        destroy = run(["make", "infra-rabbitmq-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_dns_module_flow(self) -> None:
        env = module_flags_env(dns="true")
        env.update(
            {
                "DNS_ZONE_NAME": "marketplace-dev",
                "DNS_ZONE_FQDN": "marketplace.dev.",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        steps = [
            "infra-dns-plan",
            "infra-dns-apply",
            "infra-dns-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "dns_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("zone_name=marketplace-dev", runtime_content)
        self.assertIn("zone_fqdn=marketplace.dev.", runtime_content)

        destroy = run(["make", "infra-dns-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_public_endpoints_module_flow(self) -> None:
        env = module_flags_env(public_endpoints="true")
        env.update({"PUBLIC_ENDPOINTS_BASE_DOMAIN": "apps.local"})
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        steps = [
            "infra-public-endpoints-plan",
            "infra-public-endpoints-apply",
            "infra-public-endpoints-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "public_endpoints_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("base_domain=apps.local", runtime_content)
        self.assertIn("gateway_name=public-endpoints", runtime_content)
        self.assertIn("gateway_class_name=public-endpoints", runtime_content)
        self.assertIn("edge_mode=gateway_api_envoy", runtime_content)
        self.assertIn("listener_policy=allow_cross_namespace_routes", runtime_content)
        self.assertIn("provision_path=", runtime_content)
        self.assertIn("namespace_manifest_path=", runtime_content)
        self.assertIn("gateway_manifest_path=", runtime_content)

        namespace_manifest = REPO_ROOT / "artifacts" / "infra" / "rendered" / "public-endpoints.namespace.yaml"
        self.assertTrue(namespace_manifest.exists(), msg="public-endpoints namespace manifest not rendered")
        namespace_manifest_content = namespace_manifest.read_text(encoding="utf-8")
        self.assertIn("kind: Namespace", namespace_manifest_content)
        self.assertIn("name: network", namespace_manifest_content)

        smoke_file = REPO_ROOT / "artifacts" / "infra" / "public_endpoints_smoke.env"
        self.assertTrue(smoke_file.exists())
        smoke_content = smoke_file.read_text(encoding="utf-8")
        self.assertIn("gateway_name=public-endpoints", smoke_content)
        self.assertIn("gateway_namespace=network", smoke_content)
        self.assertIn("gateway_manifest_path=", smoke_content)

        destroy = run(["make", "infra-public-endpoints-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_secrets_manager_module_flow(self) -> None:
        env = module_flags_env(secrets_manager="true")
        env.update({"SECRETS_MANAGER_INSTANCE_NAME": "marketplace-secrets-dev"})
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        steps = [
            "infra-secrets-manager-plan",
            "infra-secrets-manager-apply",
            "infra-secrets-manager-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "secrets_manager_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("instance_name=marketplace-secrets-dev", runtime_content)
        self.assertIn("endpoint=https://secrets.", runtime_content)

        destroy = run(["make", "infra-secrets-manager-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_kms_module_flow(self) -> None:
        env = module_flags_env(kms="true")
        env.update(
            {
                "KMS_KEY_RING_NAME": "marketplace-ring-dev",
                "KMS_KEY_NAME": "marketplace-key-dev",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        steps = [
            "infra-kms-plan",
            "infra-kms-apply",
            "infra-kms-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "kms_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("key_id=kms://marketplace-ring-dev/marketplace-key-dev", runtime_content)

        destroy = run(["make", "infra-kms-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_stackit_rabbitmq_module_flow_uses_foundation_contract(self) -> None:
        env = module_flags_env(profile="stackit-dev", rabbitmq="true")
        env.update({"RABBITMQ_INSTANCE_NAME": "marketplace-rmq"})
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        for step in ("infra-rabbitmq-plan", "infra-rabbitmq-apply", "infra-rabbitmq-smoke"):
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "rabbitmq_runtime.env"
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("provision_driver=foundation_contract", runtime_content)
        self.assertIn("host=marketplace-rmq.rabbitmq.eu01.stackit.invalid", runtime_content)
        self.assertIn("username=provider-generated", runtime_content)

        destroy = run(["make", "infra-rabbitmq-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_stackit_kms_module_flow_uses_foundation_contract(self) -> None:
        env = module_flags_env(profile="stackit-dev", kms="true")
        env.update(
            {
                "KMS_KEY_RING_NAME": "marketplace-ring-dev",
                "KMS_KEY_NAME": "marketplace-key-dev",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        for step in ("infra-kms-plan", "infra-kms-apply", "infra-kms-smoke"):
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "kms_runtime.env"
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("provision_driver=foundation_contract", runtime_content)
        self.assertIn("key_ring_id=kms://marketplace-ring-dev", runtime_content)
        self.assertIn("key_id=kms://marketplace-ring-dev/marketplace-key-dev", runtime_content)

        destroy = run(["make", "infra-kms-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)

    def test_identity_aware_proxy_requires_keycloak_oidc_configuration(self) -> None:
        env = module_flags_env(identity_aware_proxy="true")
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        plan = run(["make", "infra-identity-aware-proxy-plan"], env)
        self.assertNotEqual(plan.returncode, 0, msg=plan.stdout + plan.stderr)
        self.assertIn("IAP_COOKIE_SECRET", plan.stderr + plan.stdout)

    def test_identity_aware_proxy_rejects_invalid_cookie_secret_length(self) -> None:
        env = module_flags_env(identity_aware_proxy="true")
        env.update(
            {
                "IAP_UPSTREAM_URL": "http://catalog.apps.svc.cluster.local:8080",
                "IAP_COOKIE_SECRET": "0123456789abcdef0123456789abcdef01234567",
                "KEYCLOAK_ISSUER_URL": "https://keycloak.example/realms/marketplace",
                "KEYCLOAK_CLIENT_ID": "marketplace-iap",
                "KEYCLOAK_CLIENT_SECRET": "marketplace-iap-secret",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        plan = run(["make", "infra-identity-aware-proxy-plan"], env)
        self.assertNotEqual(plan.returncode, 0, msg=plan.stdout + plan.stderr)
        self.assertIn("must be a raw 16, 24, or 32 byte string", plan.stdout + plan.stderr)

    def test_stackit_fallback_modules_materialize_module_specific_argocd_applications(self) -> None:
        env = module_flags_env(
            profile="stackit-dev",
            public_endpoints="true",
            identity_aware_proxy="true",
        )
        env.update(
            {
                "KEYCLOAK_ISSUER_URL": "https://keycloak.example/realms/marketplace",
                "KEYCLOAK_CLIENT_ID": "marketplace-iap",
                "KEYCLOAK_CLIENT_SECRET": "marketplace-iap-secret",
                "IAP_UPSTREAM_URL": "http://catalog.apps.svc.cluster.local:8080",
                "IAP_COOKIE_SECRET": "0123456789abcdef0123456789abcdef",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        public_endpoints_manifest = (
            REPO_ROOT / "infra/gitops/argocd/optional/dev/public-endpoints.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("project: platform-edge-dev", public_endpoints_manifest)
        self.assertIn("repoURL: docker.io/envoyproxy", public_endpoints_manifest)
        self.assertIn("chart: gateway-helm", public_endpoints_manifest)
        self.assertIn("targetRevision: 1.7.1", public_endpoints_manifest)
        self.assertIn("kind: GatewayClass", public_endpoints_manifest)
        self.assertIn("kind: Gateway", public_endpoints_manifest)

        iap_manifest = (REPO_ROOT / "infra/gitops/argocd/optional/dev/identity-aware-proxy.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("repoURL: https://oauth2-proxy.github.io/manifests", iap_manifest)
        self.assertIn("targetRevision: 10.4.0", iap_manifest)
        self.assertIn('existingSecret: "blueprint-iap-config"', iap_manifest)
        self.assertIn('repository: "oauth2-proxy/oauth2-proxy"', iap_manifest)
        self.assertIn('tag: "v7.15.0"', iap_manifest)
        self.assertIn("gatewayApi:", iap_manifest)
        self.assertIn('name: "public-endpoints"', iap_manifest)

    def test_identity_aware_proxy_module_flow(self) -> None:
        env = module_flags_env(identity_aware_proxy="true")
        env.update(
            {
                "IAP_UPSTREAM_URL": "http://catalog.apps.svc.cluster.local:8080",
                "IAP_COOKIE_SECRET": "0123456789abcdef0123456789abcdef",
                "KEYCLOAK_ISSUER_URL": "https://keycloak.example/realms/marketplace",
                "KEYCLOAK_CLIENT_ID": "marketplace-iap",
                "KEYCLOAK_CLIENT_SECRET": "marketplace-iap-secret",
            }
        )
        bootstrap = run_render_and_infra_bootstrap(env)
        self.assertEqual(bootstrap.returncode, 0, msg=bootstrap.stdout + bootstrap.stderr)

        steps = [
            "infra-identity-aware-proxy-plan",
            "infra-identity-aware-proxy-apply",
            "infra-identity-aware-proxy-smoke",
        ]
        for step in steps:
            result = run(["make", step], env)
            self.assertEqual(result.returncode, 0, msg=f"{step}\n{result.stdout}\n{result.stderr}")

        runtime_file = REPO_ROOT / "artifacts" / "infra" / "identity_aware_proxy_runtime.env"
        self.assertTrue(runtime_file.exists())
        runtime_content = runtime_file.read_text(encoding="utf-8")
        self.assertIn("keycloak_issuer=https://keycloak.example/realms/marketplace", runtime_content)
        self.assertIn("keycloak_client_id=marketplace-iap", runtime_content)
        self.assertIn("auth_mode=browser_oidc_proxy", runtime_content)
        self.assertIn("route_mode=gateway_api", runtime_content)
        self.assertIn("provision_path=", runtime_content)

        secret_manifest = REPO_ROOT / "artifacts" / "infra" / "rendered" / "secrets" / "secret-security-blueprint-iap-config.yaml"
        self.assertTrue(secret_manifest.exists(), msg="iap secret manifest not rendered")
        rendered_values = (REPO_ROOT / "artifacts" / "infra" / "rendered" / "identity-aware-proxy.values.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn('repository: "oauth2-proxy/oauth2-proxy"', rendered_values)
        self.assertIn('tag: "v7.15.0"', rendered_values)

        smoke_file = REPO_ROOT / "artifacts" / "infra" / "identity_aware_proxy_smoke.env"
        self.assertTrue(smoke_file.exists())
        smoke_content = smoke_file.read_text(encoding="utf-8")
        self.assertIn("public_host=iap.local", smoke_content)
        self.assertIn("provision_path=", smoke_content)

        destroy = run(["make", "infra-identity-aware-proxy-destroy"], env)
        self.assertEqual(destroy.returncode, 0, msg=destroy.stdout + destroy.stderr)


if __name__ == "__main__":
    unittest.main()
