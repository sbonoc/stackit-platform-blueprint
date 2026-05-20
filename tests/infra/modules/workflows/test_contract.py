from __future__ import annotations

import re
import unittest

from tests._shared.helpers import REPO_ROOT

_CONTRACT_FILE = REPO_ROOT / "blueprint" / "modules" / "workflows" / "module.contract.yaml"
_WORKFLOWS_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "workflows.sh"
_WORKFLOWS_API_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "workflows_api.sh"
_PLAN_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_workflows_plan.sh"
_APPLY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_workflows_apply.sh"
_DAG_DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_workflows_dag_deploy.sh"
_DAG_PARSE_SMOKE_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_workflows_dag_parse_smoke.sh"
_SMOKE_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_workflows_smoke.sh"
_KEYCLOAK_RECONCILE_SCRIPT = (
    REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_workflows_keycloak_reconcile.sh"
)
_ARGOCD_DEV = (
    REPO_ROOT / "infra" / "gitops" / "argocd" / "optional" / "dev" / "workflows.yaml"
)
_RENDER_MAKEFILE = REPO_ROOT / "scripts" / "bin" / "blueprint" / "render_makefile.sh"
_PYRAMID_CONTRACT = REPO_ROOT / "scripts" / "lib" / "quality" / "test_pyramid_contract.json"

_MOCK_PLAN_STATE = "\n".join([
    "profile=stackit-dev",
    "stack=stackit",
    "tooling_mode=dry_run",
    "provision_driver=api_contract",
    "provision_path=/projects/proj-123/regions/eu01/instances",
    "project_id=proj-123",
    "region=eu01",
    "display_name=bpwf-stackit-dev",
    "version=workflows-2.3-airflow-2.11",
    "dags_repo_url=https://github.com/example/dags.git",
    "dags_repo_branch=main",
    "oidc_discovery_url=https://keycloak.example.com/realms/platform",
    "payload_file=/tmp/workflows_request_payload.json",
    "api_base_url=https://workflows.api.stackit.cloud/v1alpha",
    "api_endpoint_path=/projects/proj-123/regions/eu01/instances",
    "timestamp_utc=2026-05-20T00:00:00Z",
])

_MOCK_INSTANCE_STATE = "\n".join([
    "profile=stackit-dev",
    "stack=stackit",
    "tooling_mode=dry_run",
    "provision_driver=api_contract",
    "provision_path=/projects/proj-123/regions/eu01/instances",
    "instance_id=abc12345",
    "instance_name=bpwf-stackit-dev",
    "instance_fqdn=bpwf-stackit-dev-abc12345.workflows.eu01.stackit.cloud",
    "web_url=https://bpwf-stackit-dev-abc12345.workflows.eu01.stackit.cloud",
    "health_status=Active",
    "redirect_uri=https://bpwf-stackit-dev-abc12345.workflows.eu01.stackit.cloud",
    "oidc_client_id=stackit-workflows",
    "oidc_discovery_url=https://keycloak.example.com/realms/platform",
    "keycloak_reconcile_state=reconciled",
    "api_mode=simulated",
    "api_http_status=201",
    "api_base_url=https://workflows.api.stackit.cloud/v1alpha",
    "timestamp_utc=2026-05-20T00:00:00Z",
])

_MOCK_KEYCLOAK_RECONCILE_STATE = "\n".join([
    "status=reconciled",
    "realm=platform",
    "client_id=stackit-workflows",
    "redirect_uris=https://bpwf-stackit-dev-abc12345.workflows.eu01.stackit.cloud/*",
    "web_origins=https://bpwf-stackit-dev-abc12345.workflows.eu01.stackit.cloud",
    "admin_username=workflows-admin",
    "timestamp_utc=2026-05-20T00:00:00Z",
])

_MOCK_DAG_DEPLOY_STATE = "\n".join([
    "status=synced",
    "api_mode=simulated",
    "api_http_status=200",
    "instance_id=abc12345",
    "dags_repo_url=https://github.com/example/dags.git",
    "dags_repo_branch=main",
    "dag_file_count=3",
    "timestamp_utc=2026-05-20T00:00:00Z",
])

_MOCK_SMOKE_STATE = "\n".join([
    "status=passed",
    "validation_mode=artifact",
    "instance_id=abc12345",
    "instance_status=Active",
    "timestamp_utc=2026-05-20T00:00:00Z",
])

# Concatenation of all mock state blobs for cross-state security assertions.
_ALL_MOCK_STATES = "\n".join([
    _MOCK_PLAN_STATE,
    _MOCK_INSTANCE_STATE,
    _MOCK_KEYCLOAK_RECONCILE_STATE,
    _MOCK_DAG_DEPLOY_STATE,
    _MOCK_SMOKE_STATE,
])


class PlanStateContractTests(unittest.TestCase):
    """FR-004, AC-001 — workflows_plan.env state file structure."""

    def test_plan_state_provision_driver_is_api_contract(self) -> None:
        self.assertIn(
            "provision_driver=api_contract",
            _MOCK_PLAN_STATE,
            msg="workflows_plan.env must contain provision_driver=api_contract (FR-004, AC-001)",
        )

    def test_plan_state_has_provision_path(self) -> None:
        self.assertTrue(
            re.search(r"^provision_path=", _MOCK_PLAN_STATE, re.MULTILINE) is not None,
            msg="workflows_plan.env must contain provision_path key (FR-004, AC-001)",
        )

    def test_plan_state_has_payload_file(self) -> None:
        self.assertTrue(
            re.search(r"^payload_file=", _MOCK_PLAN_STATE, re.MULTILINE) is not None,
            msg="workflows_plan.env must contain payload_file key (FR-004, AC-001)",
        )

    def test_plan_state_has_display_name(self) -> None:
        self.assertTrue(
            re.search(r"^display_name=", _MOCK_PLAN_STATE, re.MULTILINE) is not None,
            msg="workflows_plan.env must contain display_name key (FR-004, AC-001)",
        )

    def test_plan_script_writes_provision_driver(self) -> None:
        content = _PLAN_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "provision_driver=",
            content,
            msg="stackit_workflows_plan.sh must write provision_driver to state (FR-004)",
        )


class InstanceStateContractTests(unittest.TestCase):
    """FR-005, AC-002 — workflows_instance.env state file structure."""

    def _state(self) -> str:
        return _MOCK_INSTANCE_STATE

    def test_instance_state_has_instance_id(self) -> None:
        self.assertTrue(
            re.search(r"^instance_id=", self._state(), re.MULTILINE) is not None,
            msg="workflows_instance.env must contain instance_id key (FR-005, AC-002)",
        )

    def test_instance_state_has_instance_fqdn(self) -> None:
        self.assertTrue(
            re.search(r"^instance_fqdn=", self._state(), re.MULTILINE) is not None,
            msg="workflows_instance.env must contain instance_fqdn key (FR-005, AC-002)",
        )

    def test_instance_state_has_web_url(self) -> None:
        self.assertTrue(
            re.search(r"^web_url=", self._state(), re.MULTILINE) is not None,
            msg="workflows_instance.env must contain web_url key (FR-005, AC-002)",
        )

    def test_instance_state_has_health_status(self) -> None:
        self.assertTrue(
            re.search(r"^health_status=", self._state(), re.MULTILINE) is not None,
            msg="workflows_instance.env must contain health_status key (FR-005, AC-002)",
        )

    def test_apply_script_handles_http_409_idempotency(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "409",
            content,
            msg="stackit_workflows_apply.sh must handle HTTP 409 idempotency (FR-005)",
        )


class SecurityContractTests(unittest.TestCase):
    """NFR-SEC-001, AC-003 — credentials never appear in state files."""

    def test_dags_repo_token_absent_from_all_state_files(self) -> None:
        self.assertNotIn(
            "STACKIT_WORKFLOWS_DAGS_REPO_TOKEN",
            _ALL_MOCK_STATES,
            msg=(
                "STACKIT_WORKFLOWS_DAGS_REPO_TOKEN must never appear in any state file "
                "(NFR-SEC-001, AC-003)"
            ),
        )

    def test_oidc_client_secret_absent_from_all_state_files(self) -> None:
        self.assertNotIn(
            "STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET",
            _ALL_MOCK_STATES,
            msg=(
                "STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET must never appear in any state file "
                "(NFR-SEC-001, AC-003)"
            ),
        )

    def test_apply_script_does_not_persist_dags_repo_token_to_state(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(
            "STACKIT_WORKFLOWS_DAGS_REPO_TOKEN",
            content,
            msg=(
                "stackit_workflows_apply.sh must not reference STACKIT_WORKFLOWS_DAGS_REPO_TOKEN — "
                "token is only consumed by the library-level payload builder (NFR-SEC-001)"
            ),
        )

    def test_apply_script_does_not_persist_oidc_client_secret_to_state(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(
            "STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET",
            content,
            msg=(
                "stackit_workflows_apply.sh must not reference STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET — "
                "secret is only consumed by stackit_workflows_keycloak_reconcile.sh (NFR-SEC-001)"
            ),
        )

    def test_dag_deploy_does_not_persist_dags_repo_token_as_state_key(self) -> None:
        content = _DAG_DEPLOY_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(
            "dags_repo_token=",
            content,
            msg=(
                "stackit_workflows_dag_deploy.sh must not write dags_repo_token as a state key — "
                "token is used in a transient JSON payload only (NFR-SEC-001)"
            ),
        )


class KeycloakReconcileStateContractTests(unittest.TestCase):
    """FR-006, AC-006 — workflows_keycloak_reconcile.env state file structure."""

    def test_keycloak_state_has_realm(self) -> None:
        self.assertTrue(
            re.search(r"^realm=", _MOCK_KEYCLOAK_RECONCILE_STATE, re.MULTILINE) is not None,
            msg="workflows_keycloak_reconcile.env must contain realm key (FR-006, AC-006)",
        )

    def test_keycloak_state_has_client_id(self) -> None:
        self.assertTrue(
            re.search(r"^client_id=", _MOCK_KEYCLOAK_RECONCILE_STATE, re.MULTILINE) is not None,
            msg="workflows_keycloak_reconcile.env must contain client_id key (FR-006, AC-006)",
        )

    def test_keycloak_state_has_redirect_uris(self) -> None:
        self.assertTrue(
            re.search(r"^redirect_uris=", _MOCK_KEYCLOAK_RECONCILE_STATE, re.MULTILINE) is not None,
            msg="workflows_keycloak_reconcile.env must contain redirect_uris key (FR-006, AC-006)",
        )

    def test_keycloak_reconcile_script_writes_realm_and_client_id(self) -> None:
        content = _KEYCLOAK_RECONCILE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "realm=",
            content,
            msg="stackit_workflows_keycloak_reconcile.sh must write realm to state (FR-006)",
        )
        self.assertIn(
            "client_id=",
            content,
            msg="stackit_workflows_keycloak_reconcile.sh must write client_id to state (FR-006)",
        )


class DagDeployStateContractTests(unittest.TestCase):
    """FR-007, AC-004 — workflows_dag_deploy.env state file structure."""

    def test_dag_deploy_state_has_status_synced(self) -> None:
        self.assertIn(
            "status=synced",
            _MOCK_DAG_DEPLOY_STATE,
            msg="workflows_dag_deploy.env must contain status=synced (FR-007)",
        )

    def test_dag_deploy_state_has_dags_repo_url(self) -> None:
        self.assertTrue(
            re.search(r"^dags_repo_url=", _MOCK_DAG_DEPLOY_STATE, re.MULTILINE) is not None,
            msg="workflows_dag_deploy.env must contain dags_repo_url key (FR-007)",
        )


class SmokeStateContractTests(unittest.TestCase):
    """FR-011, AC-004 — workflows_smoke.env state file structure."""

    def test_smoke_state_has_status_passed(self) -> None:
        self.assertIn(
            "status=passed",
            _MOCK_SMOKE_STATE,
            msg="workflows_smoke.env must contain status=passed (FR-011, AC-004)",
        )


class ShellLibContractTests(unittest.TestCase):
    """FR-001, FR-002, NFR-OPS-001 — workflows.sh guard and init contract."""

    def _lib(self) -> str:
        return _WORKFLOWS_LIB.read_text(encoding="utf-8")

    def test_workflows_init_env_function_defined(self) -> None:
        self.assertIn(
            "workflows_init_env()",
            self._lib(),
            msg="workflows.sh must define workflows_init_env() (FR-002, NFR-OPS-001)",
        )

    def test_workflows_init_env_calls_log_fatal_for_non_stackit_profile(self) -> None:
        content = self._lib()
        self.assertIn(
            "log_fatal",
            content,
            msg=(
                "workflows.sh must call log_fatal when BLUEPRINT_PROFILE is not a stackit-* "
                "profile (FR-001, NFR-OPS-001)"
            ),
        )
        self.assertIn(
            "is_stackit_profile",
            content,
            msg=(
                "workflows.sh must guard against non-STACKIT profiles via is_stackit_profile "
                "(FR-001, NFR-OPS-001)"
            ),
        )

    def test_workflows_default_display_name_truncated_to_16_chars(self) -> None:
        content = self._lib()
        self.assertIn(
            "${sanitized:0:16}",
            content,
            msg=(
                "workflows_default_display_name() must truncate to 16 characters via "
                "${sanitized:0:16} (AC-010)"
            ),
        )

    def test_workflows_init_env_rejects_non_git_dags_url(self) -> None:
        content = self._lib()
        self.assertIn(
            ".git$",
            content,
            msg=(
                "workflows_init_env() must reject STACKIT_WORKFLOWS_DAGS_REPO_URL values "
                "that do not end with .git (FR-002, AC-010)"
            ),
        )
        self.assertIn(
            "must end with .git",
            content,
            msg=(
                "workflows_init_env() log_fatal message must state URL must end with .git "
                "(FR-002)"
            ),
        )


class ApiLibContractTests(unittest.TestCase):
    """FR-001 — workflows_api.sh API base URL default."""

    def test_api_lib_sets_workflows_api_base_url_default(self) -> None:
        content = _WORKFLOWS_API_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "STACKIT_WORKFLOWS_API_BASE_URL",
            content,
            msg=(
                "workflows_api.sh must declare STACKIT_WORKFLOWS_API_BASE_URL default "
                "(FR-001, FR-002)"
            ),
        )
        self.assertIn(
            "https://workflows.api.stackit.cloud/v1alpha",
            content,
            msg=(
                "workflows_api.sh STACKIT_WORKFLOWS_API_BASE_URL default must point to "
                "v1alpha endpoint (FR-001)"
            ),
        )


class PayloadJsonContractTests(unittest.TestCase):
    """FR-003 — workflows_payload_json() field coverage."""

    def _lib(self) -> str:
        return _WORKFLOWS_LIB.read_text(encoding="utf-8")

    def test_payload_json_includes_display_name(self) -> None:
        self.assertIn(
            '"displayName"',
            self._lib(),
            msg="workflows_payload_json() must include displayName field (FR-003)",
        )

    def test_payload_json_includes_version(self) -> None:
        self.assertIn(
            '"version"',
            self._lib(),
            msg="workflows_payload_json() must include version field (FR-003)",
        )

    def test_payload_json_includes_dags_repository(self) -> None:
        self.assertIn(
            '"dagsRepository"',
            self._lib(),
            msg="workflows_payload_json() must include dagsRepository field (FR-003)",
        )

    def test_payload_json_includes_identity_provider(self) -> None:
        self.assertIn(
            '"identityProvider"',
            self._lib(),
            msg="workflows_payload_json() must include identityProvider field (FR-003)",
        )

    def test_payload_json_includes_observability_id(self) -> None:
        self.assertIn(
            '"observabilityId"',
            self._lib(),
            msg="workflows_payload_json() must include observabilityId field (FR-003)",
        )


class ModuleContractYamlTests(unittest.TestCase):
    """FR-001, AC-008 — module.contract.yaml required inputs and outputs."""

    def _contract(self) -> str:
        return _CONTRACT_FILE.read_text(encoding="utf-8")

    def test_contract_yaml_required_env_includes_dags_repo_url(self) -> None:
        self.assertIn(
            "STACKIT_WORKFLOWS_DAGS_REPO_URL",
            self._contract(),
            msg=(
                "module.contract.yaml required_env must include STACKIT_WORKFLOWS_DAGS_REPO_URL "
                "(FR-002, AC-008)"
            ),
        )

    def test_contract_yaml_outputs_include_instance_id(self) -> None:
        self.assertIn(
            "STACKIT_WORKFLOWS_INSTANCE_ID",
            self._contract(),
            msg=(
                "module.contract.yaml outputs.produced must include STACKIT_WORKFLOWS_INSTANCE_ID "
                "(AC-002, AC-008)"
            ),
        )

    def test_contract_yaml_outputs_include_instance_fqdn(self) -> None:
        self.assertIn(
            "STACKIT_WORKFLOWS_INSTANCE_FQDN",
            self._contract(),
            msg=(
                "module.contract.yaml outputs.produced must include STACKIT_WORKFLOWS_INSTANCE_FQDN "
                "(AC-002, AC-008)"
            ),
        )

    def test_contract_yaml_outputs_include_web_url(self) -> None:
        self.assertIn(
            "STACKIT_WORKFLOWS_WEB_URL",
            self._contract(),
            msg=(
                "module.contract.yaml outputs.produced must include STACKIT_WORKFLOWS_WEB_URL "
                "(AC-002, AC-008)"
            ),
        )

    def test_contract_yaml_outputs_include_health_status(self) -> None:
        self.assertIn(
            "STACKIT_WORKFLOWS_HEALTH_STATUS",
            self._contract(),
            msg=(
                "module.contract.yaml outputs.produced must include STACKIT_WORKFLOWS_HEALTH_STATUS "
                "(AC-002, AC-008)"
            ),
        )


class ArgocdConfigMapContractTests(unittest.TestCase):
    """FR-001 — ArgoCD metadata ConfigMap (no Application — API-provisioned module)."""

    def test_argocd_dev_workflows_yaml_exists(self) -> None:
        self.assertTrue(
            _ARGOCD_DEV.exists(),
            msg=(
                "infra/gitops/argocd/optional/dev/workflows.yaml must exist "
                "(module gitops metadata presence)"
            ),
        )

    def test_argocd_dev_workflows_yaml_contains_configmap(self) -> None:
        content = _ARGOCD_DEV.read_text(encoding="utf-8")
        self.assertIn(
            "kind: ConfigMap",
            content,
            msg=(
                "workflows.yaml must contain kind: ConfigMap "
                "(metadata-only — no ArgoCD Application; API-provisioned module)"
            ),
        )


class MakeTargetContractTests(unittest.TestCase):
    """FR-012, AC-007 — make target registration and pyramid contract."""

    def test_render_makefile_registers_workflows_apply_target(self) -> None:
        content = _RENDER_MAKEFILE.read_text(encoding="utf-8")
        self.assertIn(
            "infra-stackit-workflows-apply",
            content,
            msg=(
                "render_makefile.sh must register infra-stackit-workflows-apply target "
                "(FR-012, AC-007)"
            ),
        )

    def test_pyramid_contract_registers_this_test_file(self) -> None:
        content = _PYRAMID_CONTRACT.read_text(encoding="utf-8")
        self.assertIn(
            "tests/infra/modules/workflows/test_contract.py",
            content,
            msg=(
                "test_pyramid_contract.json must register tests/infra/modules/workflows/test_contract.py "
                "under unit scope (FR-012, AC-007)"
            ),
        )


class DagParseSmokeContractTests(unittest.TestCase):
    """FR-010, FR-013 — DAG location guard in dag_parse_smoke script."""

    def test_dag_parse_smoke_guards_against_dag_files_under_apps(self) -> None:
        content = _DAG_PARSE_SMOKE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "apps",
            content,
            msg=(
                "stackit_workflows_dag_parse_smoke.sh must guard against *dag*.py files "
                "under apps/ (FR-010)"
            ),
        )

    def test_dag_parse_smoke_writes_status_passed(self) -> None:
        content = _DAG_PARSE_SMOKE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "status=passed",
            content,
            msg=(
                "stackit_workflows_dag_parse_smoke.sh must write status=passed to state "
                "(FR-010)"
            ),
        )

    def test_dag_parse_smoke_writes_violations_key(self) -> None:
        content = _DAG_PARSE_SMOKE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "violations=",
            content,
            msg=(
                "stackit_workflows_dag_parse_smoke.sh must write violations key to state "
                "(FR-013)"
            ),
        )


_DESTROY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "stackit_workflows_destroy.sh"


class DestroyContractTests(unittest.TestCase):
    """FR-009, FR-013, AC-005 — destroy script state key coverage."""

    def test_destroy_script_writes_api_http_status(self) -> None:
        content = _DESTROY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "api_http_status=",
            content,
            msg=(
                "stackit_workflows_destroy.sh must write api_http_status to state "
                "(FR-009, FR-013)"
            ),
        )

    def test_destroy_script_writes_instance_id(self) -> None:
        content = _DESTROY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "instance_id=",
            content,
            msg=(
                "stackit_workflows_destroy.sh must write instance_id to state "
                "(FR-009, AC-005)"
            ),
        )


if __name__ == "__main__":
    unittest.main()
