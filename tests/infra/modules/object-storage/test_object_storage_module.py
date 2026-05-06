from __future__ import annotations

import unittest
import yaml
from tests._shared.helpers import REPO_ROOT, run

_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "object-storage"
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
    / "object-storage"
    / "values.yaml"
)
_SEED_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "object-storage" / "values.yaml"
_OBJECT_STORAGE_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "object_storage.sh"
_APPLY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "object_storage_apply.sh"
_PLAN_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "object_storage_plan.sh"
_DESTROY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "object_storage_destroy.sh"
_SMOKE_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "object_storage_smoke.sh"
_STATE_DIR = REPO_ROOT / "artifacts" / "infra"


class ObjectStorageTerraformModuleTests(unittest.TestCase):
    def test_terraform_module_declares_bucket_resource(self) -> None:
        main_tf = _MODULE_DIR / "main.tf"
        content = main_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_objectstorage_bucket", content)

    def test_terraform_module_declares_credentials_group_resource(self) -> None:
        main_tf = _MODULE_DIR / "main.tf"
        content = main_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_objectstorage_credentials_group", content)

    def test_terraform_module_declares_credential_resource(self) -> None:
        main_tf = _MODULE_DIR / "main.tf"
        content = main_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_objectstorage_credential", content)

    def test_terraform_module_variables_bind_contract_inputs(self) -> None:
        variables_tf = _MODULE_DIR / "variables.tf"
        self.assertTrue(variables_tf.exists(), msg=f"missing variables.tf: {variables_tf}")
        content = variables_tf.read_text(encoding="utf-8")
        for var in ("stackit_project_id", "stackit_region", "bucket_name", "credentials_group_name"):
            self.assertIn(var, content, msg=f"missing variable: {var}")

    def test_terraform_module_outputs_expose_contract_keys(self) -> None:
        outputs_tf = _MODULE_DIR / "outputs.tf"
        self.assertTrue(outputs_tf.exists(), msg=f"missing outputs.tf: {outputs_tf}")
        content = outputs_tf.read_text(encoding="utf-8")
        for key in ("bucket_name", "endpoint_url", "access_key", "secret_access_key", "region"):
            self.assertIn(key, content, msg=f"missing output: {key}")

    def test_terraform_module_versions_tf_has_stackit_provider(self) -> None:
        versions_tf = _MODULE_DIR / "versions.tf"
        self.assertTrue(versions_tf.exists(), msg=f"missing versions.tf: {versions_tf}")
        content = versions_tf.read_text(encoding="utf-8")
        self.assertIn("stackitcloud/stackit", content)
        self.assertIn("required_providers", content)


class ObjectStorageLocalHelmChartTests(unittest.TestCase):
    def test_seed_values_use_existing_secret_not_root_user(self) -> None:
        self.assertTrue(_SEED_VALUES.exists(), msg=f"missing seed file: {_SEED_VALUES}")
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        auth = parsed.get("auth", {})
        self.assertIn(
            "existingSecret", auth,
            msg="auth.existingSecret must be present; Secret reconciled via K8s, not embedded",
        )
        self.assertNotIn(
            "rootPassword", auth,
            msg="auth.rootPassword must not be present in seed values; use existingSecret",
        )
        self.assertNotIn(
            "rootUser", auth,
            msg="auth.rootUser must not be present in seed values; use existingSecret",
        )

    def test_seed_values_existing_secret_resolves_to_correct_name(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        auth = parsed.get("auth", {})
        self.assertEqual(
            auth.get("existingSecret", ""),
            "blueprint-object-storage-auth",
            msg="auth.existingSecret must point to the reconciled K8s Secret name",
        )

    def test_bootstrap_template_uses_credential_secret_name_placeholder(self) -> None:
        self.assertTrue(
            _BOOTSTRAP_TEMPLATE.exists(), msg=f"missing bootstrap template: {_BOOTSTRAP_TEMPLATE}"
        )
        content = _BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "{{OBJECT_STORAGE_CREDENTIAL_SECRET_NAME}}", content,
            msg="template must reference the Secret name placeholder, not hardcode the secret",
        )
        self.assertNotIn(
            "{{OBJECT_STORAGE_ACCESS_KEY}}", content,
            msg="template must not embed access key placeholder; credential reconciled via Secret",
        )
        self.assertNotIn(
            "{{OBJECT_STORAGE_SECRET_KEY}}", content,
            msg="template must not embed secret key placeholder; credential reconciled via Secret",
        )

    def test_bootstrap_template_has_no_root_user_or_root_password(self) -> None:
        content = _BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")
        self.assertNotIn(
            "rootUser", content,
            msg="template must not contain rootUser; auth uses existingSecret",
        )
        self.assertNotIn(
            "rootPassword", content,
            msg="template must not contain rootPassword; auth uses existingSecret",
        )


class ObjectStorageVersionPinsTests(unittest.TestCase):
    def test_version_pins_declared(self) -> None:
        content = _VERSIONS_SH.read_text(encoding="utf-8")
        for pin in (
            "OBJECT_STORAGE_HELM_CHART_VERSION_PIN",
            "OBJECT_STORAGE_LOCAL_IMAGE_TAG",
            "OBJECT_STORAGE_LOCAL_CLIENT_IMAGE_TAG",
        ):
            self.assertIn(pin, content, msg=f"missing version pin: {pin}")


class ObjectStorageApplyScriptTests(unittest.TestCase):
    def test_apply_has_helm_case(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("helm)", content, msg="object_storage_apply.sh missing helm) case")
        self.assertIn("run_helm_upgrade_install", content)

    def test_apply_reconciles_secret_before_helm(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "object_storage_reconcile_runtime_secret", content,
            msg="apply must reconcile the K8s Secret before helm upgrade (FR-004)",
        )
        reconcile_idx = content.index("object_storage_reconcile_runtime_secret")
        helm_idx = content.index("run_helm_upgrade_install")
        self.assertLess(
            reconcile_idx, helm_idx,
            msg="secret reconcile must run BEFORE helm upgrade so chart can mount it at pod start",
        )

    def test_apply_sources_fallback_runtime(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "scripts/lib/infra/fallback_runtime.sh", content,
            msg="apply must source fallback_runtime.sh explicitly",
        )


class ObjectStorageDestroyScriptTests(unittest.TestCase):
    def test_destroy_has_helm_case(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn("helm)", content, msg="object_storage_destroy.sh missing helm) case")
        self.assertIn("run_helm_uninstall", content)

    def test_destroy_deletes_runtime_secret_after_uninstall(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "object_storage_delete_runtime_secret", content,
            msg="destroy must delete the K8s Secret to leave no credential residue (FR-007)",
        )
        helm_idx = content.index("run_helm_uninstall")
        delete_idx = content.index("object_storage_delete_runtime_secret")
        self.assertLess(
            helm_idx, delete_idx,
            msg="secret delete must run AFTER helm uninstall releases its Secret mount",
        )

    def test_destroy_sources_fallback_runtime(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "scripts/lib/infra/fallback_runtime.sh", content,
            msg="destroy must source fallback_runtime.sh explicitly",
        )


class ObjectStorageSmokeScriptTests(unittest.TestCase):
    def _run_smoke(self, state_content: str) -> int:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        runtime_env = _STATE_DIR / "object_storage_runtime.env"
        backup = None
        if runtime_env.exists():
            backup = runtime_env.read_bytes()
        runtime_env.write_text(state_content, encoding="utf-8")
        try:
            result = run(
                ["bash", str(_SMOKE_SH)],
                {"BLUEPRINT_PROFILE": "local-full", "OBJECT_STORAGE_ENABLED": "true"},
            )
            return result.returncode
        finally:
            if backup is not None:
                runtime_env.write_bytes(backup)
            else:
                runtime_env.unlink(missing_ok=True)

    def test_smoke_fails_when_endpoint_empty(self) -> None:
        rc = self._run_smoke("endpoint=\nbucket=marketplace-assets\n")
        self.assertNotEqual(rc, 0, msg="smoke should fail when endpoint is empty")

    def test_smoke_fails_when_bucket_missing(self) -> None:
        rc = self._run_smoke("endpoint=http://blueprint-object-storage.data.svc.cluster.local:9000\n")
        self.assertNotEqual(rc, 0, msg="smoke should fail when bucket key is absent")

    def test_smoke_passes_with_valid_state(self) -> None:
        rc = self._run_smoke(
            "endpoint=http://blueprint-object-storage.data.svc.cluster.local:9000\n"
            "bucket=marketplace-assets\n"
        )
        self.assertEqual(rc, 0, msg="smoke should pass with valid endpoint and bucket (local lane)")

    def test_smoke_passes_with_https_endpoint(self) -> None:
        rc = self._run_smoke(
            "endpoint=https://object-storage.eu01.onstackit.cloud\n"
            "bucket=marketplace-assets\n"
        )
        self.assertEqual(rc, 0, msg="smoke should pass with STACKIT https endpoint")


class ObjectStorageLibraryFunctionPresenceTests(unittest.TestCase):
    def test_lib_defines_secret_lifecycle_functions(self) -> None:
        content = _OBJECT_STORAGE_LIB.read_text(encoding="utf-8")
        for fn in (
            "object_storage_credential_secret_name()",
            "object_storage_reconcile_runtime_secret()",
            "object_storage_delete_runtime_secret()",
        ):
            self.assertIn(fn, content, msg=f"missing function: {fn}")

    def test_lib_does_not_pass_credentials_to_values_render(self) -> None:
        content = _OBJECT_STORAGE_LIB.read_text(encoding="utf-8")
        render_block = content.split("object_storage_render_values_file()")[1].split("\n}\n")[0]
        self.assertNotIn(
            "OBJECT_STORAGE_ACCESS_KEY=", render_block,
            msg="access key must not be passed to values render; credential reconciled via Secret",
        )
        self.assertNotIn(
            "OBJECT_STORAGE_SECRET_KEY=", render_block,
            msg="secret key must not be passed to values render; credential reconciled via Secret",
        )
        self.assertIn(
            "OBJECT_STORAGE_CREDENTIAL_SECRET_NAME=", render_block,
            msg="values render must pass the Secret name so chart can reference it via existingSecret",
        )
