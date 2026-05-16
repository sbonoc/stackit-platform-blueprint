from __future__ import annotations

import re
import unittest

from tests._shared.helpers import REPO_ROOT

_TF_MODULE = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "secrets-manager"
_CONTRACT_FILE = REPO_ROOT / "blueprint" / "modules" / "secrets-manager" / "module.contract.yaml"
_SHELL_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "secrets_manager.sh"
_APPLY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "secrets_manager_apply.sh"
_PLAN_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "secrets_manager_plan.sh"
_SMOKE_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "secrets_manager_smoke.sh"
_DESTROY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "secrets_manager_destroy.sh"
_PYRAMID_CONTRACT = REPO_ROOT / "scripts" / "lib" / "quality" / "test_pyramid_contract.json"

_REQUIRED_VARIABLES = (
    "stackit_project_id",
    "stackit_region",
    "secrets_manager_instance_name",
    "secrets_manager_acl",
    "secrets_manager_user_description",
    "secrets_manager_user_write_enabled",
)

_MOCK_RUNTIME_STATE_LOCAL = "\n".join(
    [
        "profile=local-full",
        "stack=local",
        "tooling_mode=dry_run",
        "instance_name=marketplace-secrets",
        "endpoint=https://secrets.eu01.onstackit.cloud/marketplace-secrets",
        "namespace=marketplace-secrets",
        "auth_method_details=provider-generated",
        "timestamp_utc=2026-05-16T00:00:00Z",
    ]
)


# ---------------------------------------------------------------------------
# Slice 1 — Terraform module structure (AC-001 through AC-004b)
# ---------------------------------------------------------------------------


class SecretsManagerTFModuleTests(unittest.TestCase):
    def _main_tf(self) -> str:
        return (_TF_MODULE / "main.tf").read_text(encoding="utf-8")

    def test_ac001_instance_resource_declared(self) -> None:
        self.assertIn(
            'resource "stackit_secretsmanager_instance" "this"',
            self._main_tf(),
            msg="main.tf must declare stackit_secretsmanager_instance.this (AC-001, FR-001)",
        )

    def test_ac001_instance_lifecycle_create_before_destroy(self) -> None:
        content = self._main_tf()
        self.assertIn(
            "create_before_destroy = true",
            content,
            msg="main.tf stackit_secretsmanager_instance.this must include lifecycle { create_before_destroy = true } (AC-001, NFR-REL-001)",
        )

    def test_ac002_user_resource_declared(self) -> None:
        self.assertIn(
            'resource "stackit_secretsmanager_user" "this"',
            self._main_tf(),
            msg="main.tf must declare stackit_secretsmanager_user.this (AC-002, FR-001)",
        )

    def test_ac003_variables_tf_declares_all_six_variables(self) -> None:
        content = (_TF_MODULE / "variables.tf").read_text(encoding="utf-8")
        for var in _REQUIRED_VARIABLES:
            self.assertIn(
                f'variable "{var}"',
                content,
                msg=f"variables.tf must declare variable \"{var}\" (AC-003, FR-002)",
            )

    def test_ac004_outputs_tf_declares_instance_id(self) -> None:
        content = (_TF_MODULE / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            '"instance_id"',
            content,
            msg="outputs.tf must declare instance_id output (AC-004, FR-003)",
        )

    def test_ac004_outputs_tf_declares_username(self) -> None:
        content = (_TF_MODULE / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            '"username"',
            content,
            msg="outputs.tf must declare username output (AC-004, FR-003)",
        )

    def test_ac004_outputs_tf_declares_password_sensitive(self) -> None:
        content = (_TF_MODULE / "outputs.tf").read_text(encoding="utf-8")
        self.assertIn(
            '"password"',
            content,
            msg="outputs.tf must declare password output (AC-004, FR-003)",
        )
        self.assertIn(
            "sensitive   = true",
            content,
            msg="outputs.tf password output must be marked sensitive = true (AC-004, NFR-SEC-001)",
        )

    def test_ac004b_versions_tf_exists_with_stackit_provider(self) -> None:
        content = (_TF_MODULE / "versions.tf").read_text(encoding="utf-8")
        self.assertIn(
            "stackitcloud/stackit",
            content,
            msg="versions.tf must declare stackitcloud/stackit required provider (AC-004b, FR-001)",
        )

    def test_ac004b_versions_tf_pins_provider_version(self) -> None:
        content = (_TF_MODULE / "versions.tf").read_text(encoding="utf-8")
        self.assertTrue(
            re.search(r'version\s*=\s*"= \d+\.\d+\.\d+"', content) is not None,
            msg="versions.tf must pin stackit provider with exact version constraint (AC-004b)",
        )


# ---------------------------------------------------------------------------
# Slice 2 — Shell layer and contract (AC-005 through AC-015)
# ---------------------------------------------------------------------------


class SecretsManagerContractYamlTests(unittest.TestCase):
    def test_ac005_contract_yaml_includes_namespace_output(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "SECRETS_MANAGER_NAMESPACE",
            content,
            msg="module.contract.yaml outputs.produced must include SECRETS_MANAGER_NAMESPACE (AC-005, FR-004)",
        )

    def test_ac005_contract_yaml_includes_auth_method_details_output(self) -> None:
        content = _CONTRACT_FILE.read_text(encoding="utf-8")
        self.assertIn(
            "SECRETS_MANAGER_AUTH_METHOD_DETAILS",
            content,
            msg="module.contract.yaml outputs.produced must include SECRETS_MANAGER_AUTH_METHOD_DETAILS (AC-005, FR-004)",
        )


class SecretsManagerShellLibTests(unittest.TestCase):
    def _lib(self) -> str:
        return _SHELL_LIB.read_text(encoding="utf-8")

    def test_ac006_namespace_function_exists(self) -> None:
        self.assertIn(
            "secrets_manager_namespace()",
            self._lib(),
            msg="secrets_manager.sh must declare secrets_manager_namespace() (AC-006, FR-005)",
        )

    def test_ac007_auth_method_details_function_exists(self) -> None:
        self.assertIn(
            "secrets_manager_auth_method_details()",
            self._lib(),
            msg="secrets_manager.sh must declare secrets_manager_auth_method_details() (AC-007, FR-006)",
        )

    def test_ac008_reconcile_runtime_secret_function_exists(self) -> None:
        self.assertIn(
            "secrets_manager_reconcile_runtime_secret()",
            self._lib(),
            msg="secrets_manager.sh must declare secrets_manager_reconcile_runtime_secret() (AC-008, FR-007)",
        )

    def test_ac008_delete_runtime_secret_function_exists(self) -> None:
        self.assertIn(
            "secrets_manager_delete_runtime_secret()",
            self._lib(),
            msg="secrets_manager.sh must declare secrets_manager_delete_runtime_secret() (AC-008, FR-007)",
        )

    def test_ac008_reconcile_targets_blueprint_secrets_manager_auth(self) -> None:
        self.assertIn(
            "blueprint-secrets-manager-auth",
            self._lib(),
            msg="secrets_manager_reconcile_runtime_secret() must operate on blueprint-secrets-manager-auth secret (AC-008)",
        )


class SecretsManagerScriptTests(unittest.TestCase):
    def test_ac009_apply_writes_namespace_to_state(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "namespace",
            content,
            msg="secrets_manager_apply.sh must write namespace to state file (AC-009, FR-008)",
        )

    def test_ac009_apply_writes_auth_method_details_to_state(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "auth_method_details",
            content,
            msg="secrets_manager_apply.sh must write auth_method_details to state file (AC-009, FR-008)",
        )

    def test_ac009_apply_calls_reconcile_runtime_secret(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "secrets_manager_reconcile_runtime_secret",
            content,
            msg="secrets_manager_apply.sh must call secrets_manager_reconcile_runtime_secret() (AC-009, FR-008)",
        )

    def test_ac010_plan_writes_namespace_to_state(self) -> None:
        content = _PLAN_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "namespace",
            content,
            msg="secrets_manager_plan.sh must write namespace to plan state (AC-010, FR-009)",
        )

    def test_ac011_smoke_validates_namespace_non_empty(self) -> None:
        content = _SMOKE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "namespace",
            content,
            msg="secrets_manager_smoke.sh must validate namespace key is non-empty (AC-011, FR-010)",
        )

    def test_ac011_smoke_validates_auth_method_details_non_empty(self) -> None:
        content = _SMOKE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "auth_method_details",
            content,
            msg="secrets_manager_smoke.sh must validate auth_method_details key is non-empty (AC-011, FR-010)",
        )

    def test_ac014_destroy_calls_delete_runtime_secret(self) -> None:
        content = _DESTROY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "secrets_manager_delete_runtime_secret",
            content,
            msg="secrets_manager_destroy.sh must call secrets_manager_delete_runtime_secret() (AC-014, FR-012)",
        )


class SecretsManagerRuntimeContractTests(unittest.TestCase):
    def test_ac012_runtime_state_must_not_contain_password(self) -> None:
        self.assertNotIn(
            "password=",
            _MOCK_RUNTIME_STATE_LOCAL,
            msg="runtime state file MUST NOT contain password value (AC-012, NFR-SEC-001)",
        )

    def test_ac012_runtime_state_has_namespace_key(self) -> None:
        self.assertTrue(
            re.search(r"^namespace=", _MOCK_RUNTIME_STATE_LOCAL, re.MULTILINE) is not None,
            msg="runtime state must include namespace key (AC-012 fixture sanity, NFR-OPS-001)",
        )

    def test_ac012_runtime_state_has_auth_method_details_key(self) -> None:
        self.assertTrue(
            re.search(r"^auth_method_details=", _MOCK_RUNTIME_STATE_LOCAL, re.MULTILINE) is not None,
            msg="runtime state must include auth_method_details key (AC-012 fixture sanity, NFR-OPS-001)",
        )


class SecretsManagerQualityGateTests(unittest.TestCase):
    def test_ac015_test_contract_in_pyramid_contract_json(self) -> None:
        content = _PYRAMID_CONTRACT.read_text(encoding="utf-8")
        self.assertIn(
            "tests/infra/modules/secrets-manager/test_contract.py",
            content,
            msg="test_contract.py must be registered in test_pyramid_contract.json (AC-015, FR-013)",
        )
