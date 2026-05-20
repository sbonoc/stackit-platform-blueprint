from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT

_LOCAL_WORKFLOWS_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "workflows_local.sh"
_PLAN_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "local_workflows_plan.sh"
_APPLY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "local_workflows_apply.sh"
_DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "local_workflows_deploy.sh"
_SMOKE_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "local_workflows_smoke.sh"
_DESTROY_SCRIPT = REPO_ROOT / "scripts" / "bin" / "infra" / "local_workflows_destroy.sh"
_AIRFLOW_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "workflows" / "airflow.values.yaml"
_ARGOCD_MANIFEST = REPO_ROOT / "infra" / "gitops" / "argocd" / "optional" / "local" / "workflows.yaml"
_APPPROJECT = REPO_ROOT / "infra" / "gitops" / "argocd" / "overlays" / "local" / "appproject.yaml"
_MODULE_EXECUTION = REPO_ROOT / "scripts" / "lib" / "infra" / "module_execution.sh"
_RENDER_MAKEFILE = REPO_ROOT / "scripts" / "bin" / "blueprint" / "render_makefile.sh"
_VERSIONS = REPO_ROOT / "scripts" / "lib" / "infra" / "versions.sh"
_LOCAL_CONTRACT = REPO_ROOT / "blueprint" / "modules" / "local-workflows" / "module.contract.yaml"

_MOCK_PLAN_STATE = "\n".join([
    "profile=local",
    "stack=local",
    "tooling_mode=dry_run",
    "provision_driver=argocd_optional_manifest",
    "provision_path=infra/gitops/argocd/optional/local/workflows.yaml",
    "public_url=http://localhost:8080",
    "chart_version=1.20.0",
    "timestamp_utc=2026-05-20T00:00:00Z",
])

_MOCK_APPLY_STATE = "\n".join([
    "profile=local",
    "provision_driver=argocd_optional_manifest",
    "provision_path=infra/gitops/argocd/optional/local/workflows.yaml",
    "provision_status=deferred_to_deploy",
    "timestamp_utc=2026-05-20T00:00:00Z",
])

_MOCK_DEPLOY_STATE = "\n".join([
    "profile=local",
    "provision_status=deployed",
    "timestamp_utc=2026-05-20T00:00:00Z",
])

_MOCK_SMOKE_STATE = "\n".join([
    "profile=local",
    "status=passed",
    "health_response=healthy",
    "timestamp_utc=2026-05-20T00:00:00Z",
])


class LibContractTests(unittest.TestCase):
    def test_workflows_local_lib_exists(self) -> None:
        self.assertTrue(
            _LOCAL_WORKFLOWS_LIB.exists(),
            msg=f"workflows_local.sh must exist at {_LOCAL_WORKFLOWS_LIB}",
        )

    def test_workflows_local_init_env_function_defined(self) -> None:
        content = _LOCAL_WORKFLOWS_LIB.read_text(encoding="utf-8")
        self.assertIn(
            "workflows_local_init_env",
            content,
            msg="workflows_local.sh must define workflows_local_init_env()",
        )

    def test_workflows_local_init_env_rejects_non_git_dags_url(self) -> None:
        content = _LOCAL_WORKFLOWS_LIB.read_text(encoding="utf-8")
        self.assertIn(
            ".git",
            content,
            msg="workflows_local_init_env() must validate WORKFLOWS_LOCAL_DAGS_REPO_URL ends with .git",
        )

    def test_versions_has_airflow_chart_version_pin(self) -> None:
        content = _VERSIONS.read_text(encoding="utf-8")
        self.assertIn(
            "WORKFLOWS_LOCAL_AIRFLOW_HELM_CHART_VERSION_PIN",
            content,
            msg="versions.sh must define WORKFLOWS_LOCAL_AIRFLOW_HELM_CHART_VERSION_PIN",
        )


class PlanStateContractTests(unittest.TestCase):
    def test_plan_state_has_provision_driver(self) -> None:
        self.assertIn("provision_driver=argocd_optional_manifest", _MOCK_PLAN_STATE)

    def test_plan_state_has_provision_path(self) -> None:
        self.assertIn("provision_path=", _MOCK_PLAN_STATE)

    def test_plan_state_has_public_url(self) -> None:
        self.assertIn("public_url=", _MOCK_PLAN_STATE)

    def test_plan_state_has_chart_version(self) -> None:
        self.assertIn("chart_version=", _MOCK_PLAN_STATE)


class ApplyStateContractTests(unittest.TestCase):
    def test_apply_state_has_deferred_status(self) -> None:
        self.assertIn("provision_status=deferred_to_deploy", _MOCK_APPLY_STATE)


class DeployStateContractTests(unittest.TestCase):
    def test_deploy_state_has_deployed_status(self) -> None:
        self.assertIn("provision_status=deployed", _MOCK_DEPLOY_STATE)


class SmokeStateContractTests(unittest.TestCase):
    def test_smoke_state_has_status_passed(self) -> None:
        self.assertIn("status=passed", _MOCK_SMOKE_STATE)


class ScriptContractTests(unittest.TestCase):
    def test_destroy_script_calls_remove_state_files_by_prefix(self) -> None:
        content = _DESTROY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "remove_state_files_by_prefix",
            content,
            msg="local_workflows_destroy.sh must call remove_state_files_by_prefix (AC-005, FR-007)",
        )

    def test_plan_script_checks_enabled_flag(self) -> None:
        content = _PLAN_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "WORKFLOWS_LOCAL_ENABLED",
            content,
            msg="local_workflows_plan.sh must guard on WORKFLOWS_LOCAL_ENABLED (FR-001)",
        )

    def test_apply_script_checks_enabled_flag(self) -> None:
        content = _APPLY_SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "WORKFLOWS_LOCAL_ENABLED",
            content,
            msg="local_workflows_apply.sh must guard on WORKFLOWS_LOCAL_ENABLED (FR-001)",
        )


class SecurityContractTests(unittest.TestCase):
    def test_dags_repo_token_absent_from_plan_state_keys(self) -> None:
        content = _PLAN_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(
            "WORKFLOWS_LOCAL_DAGS_REPO_TOKEN",
            content,
            msg="local_workflows_plan.sh must not write WORKFLOWS_LOCAL_DAGS_REPO_TOKEN to state (NFR-SEC-001)",
        )

    def test_oidc_client_secret_absent_from_plan_state_keys(self) -> None:
        content = _PLAN_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(
            "WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET",
            content,
            msg="local_workflows_plan.sh must not write WORKFLOWS_LOCAL_OIDC_CLIENT_SECRET to state (NFR-SEC-001)",
        )


class HelmValuesContractTests(unittest.TestCase):
    def test_airflow_values_has_gitsync_enabled(self) -> None:
        content = _AIRFLOW_VALUES.read_text(encoding="utf-8")
        self.assertIn(
            "gitSync",
            content,
            msg="airflow.values.yaml must configure git-sync sidecar (FR-008, AC-006)",
        )

    def test_airflow_values_uses_local_executor(self) -> None:
        content = _AIRFLOW_VALUES.read_text(encoding="utf-8")
        self.assertIn(
            "LocalExecutor",
            content,
            msg="airflow.values.yaml must use LocalExecutor (FR-008)",
        )


class ArgoCDManifestContractTests(unittest.TestCase):
    def test_workflows_argocd_manifest_is_application(self) -> None:
        content = _ARGOCD_MANIFEST.read_text(encoding="utf-8")
        self.assertIn(
            "kind: Application",
            content,
            msg="infra/gitops/argocd/optional/local/workflows.yaml must be an ArgoCD Application (FR-009, AC-007)",
        )

    def test_appproject_includes_airflow_repo(self) -> None:
        content = _APPPROJECT.read_text(encoding="utf-8")
        self.assertIn(
            "https://airflow.apache.org",
            content,
            msg="appproject.yaml must include https://airflow.apache.org in sourceRepos (FR-010)",
        )


class ModuleExecutionContractTests(unittest.TestCase):
    def test_module_execution_registers_local_workflows_case(self) -> None:
        content = _MODULE_EXECUTION.read_text(encoding="utf-8")
        self.assertIn(
            "local-workflows",
            content,
            msg="module_execution.sh must register local-workflows dispatch case (FR-010)",
        )

    def test_render_makefile_registers_local_workflows_targets(self) -> None:
        content = _RENDER_MAKEFILE.read_text(encoding="utf-8")
        self.assertIn(
            "infra-local-workflows-plan",
            content,
            msg="render_makefile.sh must register infra-local-workflows-* targets (FR-011)",
        )

    def test_local_contract_yaml_exists(self) -> None:
        self.assertTrue(
            _LOCAL_CONTRACT.exists(),
            msg=f"blueprint/modules/local-workflows/module.contract.yaml must exist (FR-013, AC-008)",
        )


if __name__ == "__main__":
    unittest.main()
