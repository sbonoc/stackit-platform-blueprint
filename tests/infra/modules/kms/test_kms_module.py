from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT, run

_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "kms"
_KMS_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "kms.sh"
_APPLY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "kms_apply.sh"
_PLAN_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "kms_plan.sh"
_SMOKE_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "kms_smoke.sh"
_HELM_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "kms" / "values.yaml"
_MODULE_EXEC = REPO_ROOT / "scripts" / "lib" / "infra" / "module_execution.sh"
_STATE_DIR = REPO_ROOT / "artifacts" / "infra"

_SMOKE_ENV = {
    "BLUEPRINT_PROFILE": "local-full",
    "KMS_ENABLED": "true",
    "KMS_KEY_RING_NAME": "marketplace-ring",
    "KMS_KEY_NAME": "marketplace-key",
}


class KmsTerraformModuleTests(unittest.TestCase):
    def test_terraform_module_has_keyring_resource(self) -> None:
        content = (_MODULE_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertIn(
            "stackit_kms_keyring",
            content,
            msg="main.tf must declare stackit_kms_keyring resource (AC-001)",
        )

    def test_terraform_module_has_key_resource(self) -> None:
        content = (_MODULE_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertIn(
            "stackit_kms_key",
            content,
            msg="main.tf must declare stackit_kms_key resource (AC-001)",
        )

    def test_terraform_module_has_lifecycle_create_before_destroy(self) -> None:
        content = (_MODULE_DIR / "main.tf").read_text(encoding="utf-8")
        self.assertIn(
            "create_before_destroy",
            content,
            msg="main.tf stackit_kms_keyring must include lifecycle { create_before_destroy = true } (AC-001, NFR-REL-001)",
        )

    def test_terraform_module_variables_bind_contract_inputs(self) -> None:
        content = (_MODULE_DIR / "variables.tf").read_text(encoding="utf-8")
        for var in (
            "stackit_project_id",
            "stackit_region",
            "kms_key_ring_name",
            "kms_key_name",
        ):
            self.assertIn(var, content, msg=f"variables.tf missing required input: {var} (AC-002)")

    def test_terraform_module_outputs_expose_keyring_id(self) -> None:
        content = (_MODULE_DIR / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            "kms_keyring_id",
            content,
            msg="outputs.tf must expose kms_keyring_id (AC-003)",
        )

    def test_terraform_module_outputs_expose_key_id(self) -> None:
        content = (_MODULE_DIR / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            "kms_key_id",
            content,
            msg="outputs.tf must expose kms_key_id (AC-003)",
        )

    def test_terraform_module_outputs_expose_display_names(self) -> None:
        content = (_MODULE_DIR / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            "kms_keyring_display_name",
            content,
            msg="outputs.tf must expose kms_keyring_display_name (AC-003)",
        )
        self.assertIn(
            "kms_key_display_name",
            content,
            msg="outputs.tf must expose kms_key_display_name (AC-003)",
        )


class KmsLibraryFunctionPresenceTests(unittest.TestCase):
    def test_lib_defines_kms_endpoint_function(self) -> None:
        content = _KMS_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "kms_endpoint()",
            content,
            msg="kms.sh must define kms_endpoint() (AC-005, FR-003)",
        )

    def test_kms_endpoint_local_lane_contains_vault(self) -> None:
        content = _KMS_LIB.read_text(encoding="utf-8")
        fn_start = content.find("kms_endpoint()")
        fn_body = content[fn_start : fn_start + 400]
        self.assertIn(
            "vault",
            fn_body,
            msg="kms_endpoint() local lane must return a Vault Transit URL containing 'vault' (AC-005)",
        )

    def test_kms_endpoint_local_lane_contains_transit(self) -> None:
        content = _KMS_LIB.read_text(encoding="utf-8")
        fn_start = content.find("kms_endpoint()")
        fn_body = content[fn_start : fn_start + 400]
        self.assertIn(
            "transit",
            fn_body,
            msg="kms_endpoint() local lane must return Vault Transit path containing 'transit' (AC-005)",
        )

    def test_kms_endpoint_local_lane_uses_port_8200(self) -> None:
        content = _KMS_LIB.read_text(encoding="utf-8")
        fn_start = content.find("kms_endpoint()")
        fn_body = content[fn_start : fn_start + 400]
        self.assertIn(
            "8200",
            fn_body,
            msg="kms_endpoint() local lane must use Vault default port 8200 (AC-005)",
        )


class KmsApplyScriptTests(unittest.TestCase):
    def test_apply_state_file_write_includes_endpoint_key(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "endpoint=",
            content,
            msg="kms_apply.sh write_state_file must include endpoint= key (AC-006, FR-005)",
        )


class KmsSmokeScriptTests(unittest.TestCase):
    def _run_smoke(self, state_content: str) -> int:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        runtime_env = _STATE_DIR / "kms_runtime.env"
        backup = runtime_env.read_bytes() if runtime_env.exists() else None
        runtime_env.write_text(state_content, encoding="utf-8")
        try:
            result = run(["bash", str(_SMOKE_SH)], _SMOKE_ENV)
            return result.returncode
        finally:
            if backup is not None:
                runtime_env.write_bytes(backup)
            else:
                runtime_env.unlink(missing_ok=True)

    def test_smoke_passes_with_valid_state(self) -> None:
        rc = self._run_smoke(
            "key_ring_id=kms://marketplace-ring\n"
            "key_id=kms://marketplace-ring/marketplace-key\n"
            "key_ring_name=marketplace-ring\n"
            "key_name=marketplace-key\n"
            "endpoint=http://blueprint-vault.kms.svc.cluster.local:8200/v1/transit\n"
        )
        self.assertEqual(rc, 0, msg="smoke should pass with valid state containing all five contract keys (AC-007)")

    def test_smoke_fails_when_key_id_empty(self) -> None:
        rc = self._run_smoke(
            "key_ring_id=kms://marketplace-ring\n"
            "key_id=\n"
            "key_ring_name=marketplace-ring\n"
            "key_name=marketplace-key\n"
            "endpoint=http://blueprint-vault.kms.svc.cluster.local:8200/v1/transit\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when key_id is empty (AC-008)")

    def test_smoke_fails_when_key_ring_id_empty(self) -> None:
        rc = self._run_smoke(
            "key_ring_id=\n"
            "key_id=kms://marketplace-ring/marketplace-key\n"
            "key_ring_name=marketplace-ring\n"
            "key_name=marketplace-key\n"
            "endpoint=http://blueprint-vault.kms.svc.cluster.local:8200/v1/transit\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when key_ring_id is empty (AC-009)")

    def test_smoke_fails_when_endpoint_empty(self) -> None:
        rc = self._run_smoke(
            "key_ring_id=kms://marketplace-ring\n"
            "key_id=kms://marketplace-ring/marketplace-key\n"
            "key_ring_name=marketplace-ring\n"
            "key_name=marketplace-key\n"
            "endpoint=\n"
        )
        self.assertNotEqual(rc, 0, msg="smoke should fail when endpoint is empty (AC-010)")


class KmsHelmValuesTests(unittest.TestCase):
    def test_helm_values_sets_fullname_override_to_blueprint_vault(self) -> None:
        content = _HELM_VALUES.read_text(encoding="utf-8")
        self.assertIn(
            "blueprint-vault",
            content,
            msg="infra/local/helm/kms/values.yaml must set fullnameOverride: blueprint-vault (AC-012)",
        )

    def test_helm_values_enables_dev_mode(self) -> None:
        content = _HELM_VALUES.read_text(encoding="utf-8")
        self.assertIn(
            "enabled: true",
            content,
            msg="infra/local/helm/kms/values.yaml must enable server.dev.enabled: true (AC-012)",
        )


class KmsPlanScriptTests(unittest.TestCase):
    def test_plan_sh_has_helm_driver_case(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn(
            "helm)",
            content,
            msg="kms_plan.sh must have a helm driver case for the local lane (AC-013)",
        )


class KmsModuleExecutionTests(unittest.TestCase):
    def _kms_section(self) -> str:
        content = _MODULE_EXEC.read_text(encoding="utf-8")
        start = content.find("kms:plan")
        end = content.find("langfuse:", start)
        return content[start:end] if end != -1 else content[start:]

    def test_module_execution_kms_local_plan_apply_driver_is_helm(self) -> None:
        section = self._kms_section()
        self.assertIn(
            '"helm"',
            section,
            msg="module_execution.sh kms local-profile driver for plan/apply must be helm, not noop (AC-014)",
        )

    def test_module_execution_kms_local_destroy_driver_is_helm(self) -> None:
        content = _MODULE_EXEC.read_text(encoding="utf-8")
        destroy_start = content.find("kms:destroy")
        destroy_end = content.find("langfuse:", destroy_start)
        section = content[destroy_start:destroy_end] if destroy_end != -1 else content[destroy_start:]
        self.assertIn(
            '"helm"',
            section,
            msg="module_execution.sh kms local-profile driver for destroy must be helm, not noop (AC-014)",
        )
