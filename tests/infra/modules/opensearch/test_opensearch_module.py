from __future__ import annotations

import unittest
import yaml
from tests._shared.helpers import REPO_ROOT, run

_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "opensearch"
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
    / "opensearch"
    / "values.yaml"
)
_SEED_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "opensearch" / "values.yaml"


class OpenSearchTerraformModuleTests(unittest.TestCase):
    def test_terraform_module_has_opensearch_resources(self) -> None:
        main_tf = _MODULE_DIR / "main.tf"
        content = main_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_opensearch_instance", content)
        self.assertIn("stackit_opensearch_credential", content)
        self.assertIn("create_before_destroy", content)

    def test_terraform_module_variables_bind_contract_inputs(self) -> None:
        variables_tf = _MODULE_DIR / "variables.tf"
        content = variables_tf.read_text(encoding="utf-8")
        self.assertIn("stackit_project_id", content)
        self.assertIn("opensearch_instance_name", content)
        self.assertIn("opensearch_version", content)
        self.assertIn("opensearch_plan_name", content)

    def test_terraform_module_outputs_expose_contract_keys(self) -> None:
        outputs_tf = _MODULE_DIR / "outputs.tf"
        content = outputs_tf.read_text(encoding="utf-8")
        for key in (
            "opensearch_host",
            "opensearch_hosts",
            "opensearch_port",
            "opensearch_scheme",
            "opensearch_uri",
            "opensearch_dashboard_url",
            "opensearch_username",
            "opensearch_password",
        ):
            self.assertIn(key, content, msg=f"missing output: {key}")

    def test_terraform_module_versions_tf_exists_with_provider_constraint(self) -> None:
        versions_tf = _MODULE_DIR / "versions.tf"
        content = versions_tf.read_text(encoding="utf-8")
        self.assertIn("stackitcloud/stackit", content)
        self.assertIn("required_providers", content)


class OpenSearchLocalHelmChartTests(unittest.TestCase):
    def test_opensearch_local_helm_values_file_exists_and_parses(self) -> None:
        self.assertTrue(_SEED_VALUES.exists(), msg=f"missing seed file: {_SEED_VALUES}")
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        self.assertIsInstance(parsed, dict)
        self.assertIn("fullnameOverride", parsed)

    def test_opensearch_bootstrap_template_exists_with_placeholders(self) -> None:
        self.assertTrue(
            _BOOTSTRAP_TEMPLATE.exists(), msg=f"missing bootstrap template: {_BOOTSTRAP_TEMPLATE}"
        )
        content = _BOOTSTRAP_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("{{OPENSEARCH_HELM_RELEASE}}", content)
        self.assertIn("{{OPENSEARCH_IMAGE_REPOSITORY}}", content)
        self.assertIn("{{OPENSEARCH_USERNAME}}", content)
        self.assertIn("{{OPENSEARCH_PASSWORD}}", content)

    def test_opensearch_seed_values_persistence_disabled(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        master = parsed.get("master", {})
        persistence = master.get("persistence", {})
        self.assertFalse(persistence.get("enabled", True), msg="local persistence must be disabled")

    def test_opensearch_seed_values_memory_within_1gb(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        master = parsed.get("master", {})
        limits = master.get("resources", {}).get("limits", {})
        memory = limits.get("memory", "")
        self.assertTrue(
            memory.endswith("Gi") or memory.endswith("Mi"),
            msg=f"unexpected memory unit: {memory}",
        )
        if memory.endswith("Gi"):
            self.assertLessEqual(float(memory[:-2]), 1.0, msg="memory limit must be ≤1 Gi")
        else:
            self.assertLessEqual(float(memory[:-2]), 1024.0, msg="memory limit must be ≤1024 Mi")


class OpenSearchVersionPinsTests(unittest.TestCase):
    def test_opensearch_version_pins_declared(self) -> None:
        content = _VERSIONS_SH.read_text(encoding="utf-8")
        for pin in (
            "OPENSEARCH_HELM_CHART_VERSION_PIN",
            "OPENSEARCH_LOCAL_IMAGE_REGISTRY",
            "OPENSEARCH_LOCAL_IMAGE_REPOSITORY",
            "OPENSEARCH_LOCAL_IMAGE_TAG",
        ):
            self.assertIn(pin, content, msg=f"missing version pin: {pin}")


def _resolve_opensearch_module_execution(action: str, *, profile: str) -> str:
    script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/stack_paths.sh"
source "{REPO_ROOT}/scripts/lib/infra/opensearch.sh"
source "{REPO_ROOT}/scripts/lib/infra/module_execution.sh"
opensearch_seed_env_defaults
resolve_optional_module_execution "opensearch" "{action}"
printf 'class=%s\\ndriver=%s\\npath=%s\\n' \\
  "$OPTIONAL_MODULE_EXECUTION_CLASS" \\
  "$OPTIONAL_MODULE_EXECUTION_DRIVER" \\
  "$OPTIONAL_MODULE_EXECUTION_PATH"
"""
    result = run(["bash", "-lc", script], {"BLUEPRINT_PROFILE": profile})
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout + result.stderr


class OpenSearchModuleExecutionRoutingTests(unittest.TestCase):
    def test_opensearch_local_profile_routes_to_helm_driver(self) -> None:
        out = _resolve_opensearch_module_execution("apply", profile="local-full")
        self.assertIn("driver=helm", out)

    def test_opensearch_local_destroy_routes_to_helm_driver(self) -> None:
        out = _resolve_opensearch_module_execution("destroy", profile="local-full")
        self.assertIn("driver=helm", out)

    def test_opensearch_stackit_profile_routes_to_foundation_contract(self) -> None:
        out = _resolve_opensearch_module_execution("apply", profile="stackit-dev")
        self.assertIn("driver=foundation_contract", out)


def _run_opensearch_bash(fn_expr: str, *, profile: str = "local-full") -> str:
    script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/opensearch.sh"
opensearch_seed_env_defaults
printf '%s' "$({fn_expr})"
"""
    result = run(["bash", "-lc", script], {"BLUEPRINT_PROFILE": profile})
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout.strip()


_APPLY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "opensearch_apply.sh"


class OpenSearchApplyScriptTests(unittest.TestCase):
    def test_opensearch_apply_local_calls_helm_upgrade(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("helm)", content, msg="opensearch_apply.sh missing helm) case")
        self.assertIn("run_helm_upgrade_install", content)
        self.assertIn("opensearch_render_values_file", content)


class OpenSearchLocalLaneFunctionTests(unittest.TestCase):
    def test_opensearch_local_host_returns_service_hostname(self) -> None:
        host = _run_opensearch_bash("opensearch_local_service_host")
        self.assertEqual(host, "blueprint-opensearch.search.svc.cluster.local")

    def test_opensearch_local_port_returns_9200(self) -> None:
        port = _run_opensearch_bash("opensearch_local_port")
        self.assertEqual(port, "9200")

    def test_opensearch_local_scheme_returns_http(self) -> None:
        scheme = _run_opensearch_bash("opensearch_local_scheme")
        self.assertEqual(scheme, "http")

    def test_opensearch_init_env_sets_helm_defaults(self) -> None:
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/opensearch.sh"
opensearch_seed_env_defaults
printf 'release=%s\\nnamespace=%s\\nchart=%s\\n' \\
  "$OPENSEARCH_HELM_RELEASE" \\
  "$OPENSEARCH_NAMESPACE" \\
  "$OPENSEARCH_HELM_CHART"
"""
        result = run(["bash", "-lc", script], {"BLUEPRINT_PROFILE": "local-full"})
        if result.returncode != 0:
            raise AssertionError(result.stdout + result.stderr)
        out = result.stdout + result.stderr
        self.assertIn("release=blueprint-opensearch", out)
        self.assertIn("namespace=search", out)
        self.assertIn("chart=bitnami/opensearch", out)
