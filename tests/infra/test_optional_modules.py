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

    def test_infra_bootstrap_prunes_stale_optional_scaffolding_when_flags_disabled(self) -> None:
        enabled_env = module_flags_env(
            profile="stackit-dev",
            workflows="true",
            langfuse="true",
            postgres="true",
            neo4j="true",
        )
        enabled = run_render_and_infra_bootstrap(enabled_env)
        self.assertEqual(enabled.returncode, 0, msg=enabled.stdout + enabled.stderr)

        expected_when_enabled = [
            "dags",
            "infra/cloud/stackit/terraform/modules/workflows",
            "infra/cloud/stackit/terraform/modules/langfuse",
            "infra/cloud/stackit/terraform/modules/postgres",
            "infra/cloud/stackit/terraform/modules/neo4j",
            "infra/local/helm/langfuse",
            "infra/local/helm/postgres",
            "infra/local/helm/neo4j",
            "tests/infra/modules/workflows",
            "tests/infra/modules/langfuse",
            "tests/infra/modules/postgres",
            "tests/infra/modules/neo4j",
            "infra/gitops/argocd/optional/dev/workflows.yaml",
            "infra/gitops/argocd/optional/dev/langfuse.yaml",
            "infra/gitops/argocd/optional/dev/neo4j.yaml",
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
            "infra/local/helm/langfuse",
            "infra/local/helm/postgres",
            "infra/local/helm/neo4j",
            "tests/infra/modules/workflows",
            "tests/infra/modules/langfuse",
            "tests/infra/modules/postgres",
            "tests/infra/modules/neo4j",
            "infra/gitops/argocd/optional/dev/workflows.yaml",
            "infra/gitops/argocd/optional/dev/langfuse.yaml",
            "infra/gitops/argocd/optional/dev/neo4j.yaml",
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
        self.assertIn("provision_driver=terraform_plus_api", plan_state)

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
        self.assertIn("provision_driver=terraform", runtime_content)
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


if __name__ == "__main__":
    unittest.main()
