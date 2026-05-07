from __future__ import annotations

import unittest
from tests._shared.helpers import REPO_ROOT, run

_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "postgres"
_VERSIONS_SH = REPO_ROOT / "scripts" / "lib" / "infra" / "versions.sh"
_BOOTSTRAP_TEMPLATE = (
    REPO_ROOT
    / "scripts"
    / "templates"
    / "infra"
    / "bootstrap"
    / "infra"
    / "local"
    / "helm"
    / "postgres"
    / "values.yaml"
)
_SEED_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "postgres" / "values.yaml"
_POSTGRES_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "postgres.sh"
_APPLY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "postgres_apply.sh"
_DESTROY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "postgres_destroy.sh"
_SMOKE_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "postgres_smoke.sh"
_STATE_DIR = REPO_ROOT / "artifacts" / "infra"


class PostgresTerraformModuleTests(unittest.TestCase):
    def test_terraform_module_has_postgresflex_resources(self) -> None:
        main_tf = _MODULE_DIR / "main.tf"
        content = main_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_postgresflex_instance", content)
        self.assertIn("stackit_postgresflex_user", content)
        self.assertIn("stackit_postgresflex_database", content)
        self.assertIn("create_before_destroy", content)

    def test_terraform_module_variables_bind_contract_inputs(self) -> None:
        variables_tf = _MODULE_DIR / "variables.tf"
        content = variables_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_project_id", content)
        self.assertIn("postgres_instance_name", content)
        self.assertIn("postgres_db_name", content)
        self.assertIn("postgres_username", content)
        self.assertIn("postgres_version", content)

    def test_terraform_module_outputs_expose_contract_keys(self) -> None:
        outputs_tf = _MODULE_DIR / "outputs.tf"
        content = outputs_tf.read_text(encoding="utf-8")
        for key in (
            "postgres_instance_id",
            "postgres_host",
            "postgres_port",
            "postgres_username",
            "postgres_password",
            "postgres_database",
        ):
            self.assertIn(key, content, msg=f"missing output: {key}")

    def test_terraform_module_versions_tf_exists_with_provider_constraint(self) -> None:
        versions_tf = _MODULE_DIR / "versions.tf"
        content = versions_tf.read_text(encoding="utf-8")
        self.assertIn("stackitcloud/stackit", content)
        self.assertIn("required_providers", content)


class PostgresLocalHelmChartTests(unittest.TestCase):
    def test_seed_values_use_existing_secret_not_plaintext_auth(self) -> None:
        import yaml

        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        auth = parsed.get("auth", {})
        self.assertIn(
            "existingSecret",
            auth,
            msg="auth.existingSecret must be set; Secret reconciled before helm upgrade",
        )
        self.assertIn(
            "username",
            auth,
            msg="auth.username must be set so Bitnami uses 'password' key from existingSecret (not 'postgres-password')",
        )
        self.assertNotIn(
            "password",
            auth,
            msg="auth.password must not appear in values.yaml; password delivered via existingSecret",
        )

    def test_bootstrap_template_uses_credential_secret_name_placeholder(self) -> None:
        content = _BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "{{POSTGRES_CREDENTIAL_SECRET_NAME}}",
            content,
            msg="bootstrap template must reference credential Secret name placeholder",
        )

    def test_bootstrap_template_has_no_plaintext_password(self) -> None:
        content = _BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "{{POSTGRES_USER}}",
            content,
            msg="bootstrap template must bind POSTGRES_USER so Bitnami uses the 'password' Secret key",
        )
        self.assertNotIn(
            "{{POSTGRES_PASSWORD}}",
            content,
            msg="bootstrap template must not embed plaintext POSTGRES_PASSWORD; password delivered via existingSecret",
        )


class PostgresLibraryFunctionPresenceTests(unittest.TestCase):
    def test_lib_defines_secret_lifecycle_functions(self) -> None:
        content = _POSTGRES_LIB.read_text(encoding="utf-8")
        for fn in (
            "postgres_credential_secret_name()",
            "postgres_reconcile_runtime_secret()",
            "postgres_delete_runtime_secret()",
        ):
            self.assertIn(fn, content, msg=f"missing function: {fn}")

    def test_lib_does_not_pass_password_to_values_render(self) -> None:
        content = _POSTGRES_LIB.read_text(encoding="utf-8")
        render_block = content.split("postgres_render_values_file()")[1].split("\n}\n")[0]
        self.assertIn(
            "POSTGRES_USER=",
            render_block,
            msg="POSTGRES_USER must be bound so auth.username reaches the chart (non-secret identifier)",
        )
        self.assertNotIn(
            "POSTGRES_PASSWORD=",
            render_block,
            msg="POSTGRES_PASSWORD must not be a values placeholder; delivered via existingSecret",
        )
        self.assertIn(
            "POSTGRES_CREDENTIAL_SECRET_NAME=",
            render_block,
            msg="values must reference the Secret name for password delivery",
        )


class PostgresApplyScriptTests(unittest.TestCase):
    def test_apply_has_helm_case(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("helm)", content, msg="postgres_apply.sh missing helm) case")
        self.assertIn("run_helm_upgrade_install", content)

    def test_apply_reconciles_secret_before_helm(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "postgres_reconcile_runtime_secret",
            content,
            msg="apply must reconcile the K8s Secret before helm upgrade",
        )
        reconcile_idx = content.index("postgres_reconcile_runtime_secret")
        helm_idx = content.index("run_helm_upgrade_install")
        self.assertLess(
            reconcile_idx,
            helm_idx,
            msg="secret reconcile must run BEFORE helm upgrade so the chart can mount it",
        )


class PostgresDestroyScriptTests(unittest.TestCase):
    def test_destroy_has_helm_case(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn("helm)", content, msg="postgres_destroy.sh missing helm) case")
        self.assertIn("run_helm_uninstall", content)

    def test_destroy_deletes_runtime_secret_after_uninstall(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "postgres_delete_runtime_secret",
            content,
            msg="destroy must delete the K8s Secret to leave no residue",
        )
        helm_idx = content.index("run_helm_uninstall")
        delete_idx = content.index("postgres_delete_runtime_secret")
        self.assertLess(
            helm_idx,
            delete_idx,
            msg="secret delete must run AFTER helm uninstall releases its mount",
        )


class PostgresSmokeScriptTests(unittest.TestCase):
    def _run_smoke(self, state_content: str) -> int:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        runtime_env = _STATE_DIR / "postgres_runtime.env"
        backup = None
        if runtime_env.exists():
            backup = runtime_env.read_bytes()
        runtime_env.write_text(state_content, encoding="utf-8")
        try:
            result = run(
                ["bash", str(_SMOKE_SH)],
                {
                    "BLUEPRINT_PROFILE": "local-full",
                    "POSTGRES_ENABLED": "true",
                    "POSTGRES_INSTANCE_NAME": "blueprint-postgres",
                    "POSTGRES_DB_NAME": "platform",
                    "POSTGRES_USER": "platform",
                    "POSTGRES_PASSWORD": "platform-password",
                },
            )
            return result.returncode
        finally:
            if backup is not None:
                runtime_env.write_bytes(backup)
            else:
                runtime_env.unlink(missing_ok=True)

    def test_smoke_passes_with_valid_state(self) -> None:
        rc = self._run_smoke(
            "host=blueprint-postgres.data.svc.cluster.local\n"
            "port=5432\n"
            "db_name=platform\n"
            "user=platform\n"
            "password=platform-password\n"
            "dsn=postgresql://platform:platform-password@blueprint-postgres.data.svc.cluster.local:5432/platform\n"
        )
        self.assertEqual(rc, 0, msg="smoke should pass with valid state containing all six contract keys")

    def test_smoke_fails_when_dsn_invalid(self) -> None:
        rc = self._run_smoke(
            "host=blueprint-postgres.data.svc.cluster.local\n"
            "port=5432\n"
            "db_name=platform\n"
            "user=platform\n"
            "password=platform-password\n"
            "dsn=postgres://invalid-scheme\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when DSN does not start with postgresql://")

    def test_smoke_fails_when_host_empty(self) -> None:
        rc = self._run_smoke(
            "host=\n"
            "port=5432\n"
            "db_name=platform\n"
            "user=platform\n"
            "password=platform-password\n"
            "dsn=postgresql://platform:platform-password@:5432/platform\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when host is empty")

    def test_smoke_fails_when_db_name_empty(self) -> None:
        rc = self._run_smoke(
            "host=blueprint-postgres.data.svc.cluster.local\n"
            "port=5432\n"
            "db_name=\n"
            "user=platform\n"
            "password=platform-password\n"
            "dsn=postgresql://platform:platform-password@blueprint-postgres.data.svc.cluster.local:5432/\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when db_name is empty")
