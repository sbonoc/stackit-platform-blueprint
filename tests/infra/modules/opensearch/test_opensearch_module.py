from __future__ import annotations

import unittest
from tests._shared.helpers import REPO_ROOT, run

_MODULE_DIR = REPO_ROOT / "infra" / "cloud" / "stackit" / "terraform" / "modules" / "opensearch"
_VERSIONS_SH = REPO_ROOT / "scripts" / "lib" / "infra" / "versions.sh"


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
