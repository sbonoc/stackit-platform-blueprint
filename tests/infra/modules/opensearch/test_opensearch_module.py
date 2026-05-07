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
_OPENSEARCH_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "opensearch.sh"
_APPLY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "opensearch_apply.sh"
_PLAN_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "opensearch_plan.sh"
_DESTROY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "opensearch_destroy.sh"
_SMOKE_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "opensearch_smoke.sh"
_STATE_DIR = REPO_ROOT / "artifacts" / "infra"


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
        self.assertIn("{{OPENSEARCH_PASSWORD_SECRET_NAME}}", content)
        self.assertNotIn("{{OPENSEARCH_USERNAME}}", content)
        self.assertNotIn("{{OPENSEARCH_PASSWORD}}", content)

    def test_opensearch_seed_values_persistence_disabled(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        master = parsed.get("master", {})
        persistence = master.get("persistence", {})
        self.assertFalse(persistence.get("enabled", True), msg="local persistence must be disabled")

    def test_opensearch_seed_values_use_existing_secret(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        security = parsed.get("security", {})
        self.assertTrue(security.get("enabled", False), msg="security must be enabled")
        self.assertEqual(
            security.get("existingSecret", ""),
            "blueprint-opensearch-auth",
            msg="security.existingSecret must reference reconciled K8s Secret, not embed plaintext",
        )
        self.assertNotIn(
            "adminPassword", security,
            msg="adminPassword must not be embedded in values.yaml; use existingSecret",
        )

    def test_opensearch_seed_values_topology_is_minimal_two_pod(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        self.assertEqual(parsed.get("master", {}).get("replicaCount"), 1)
        self.assertFalse(parsed.get("master", {}).get("masterOnly", True),
                         msg="master.masterOnly must be false so master serves data role")
        self.assertEqual(parsed.get("data", {}).get("replicaCount"), 0)
        self.assertFalse(parsed.get("ingest", {}).get("enabled", True))
        self.assertEqual(parsed.get("coordinating", {}).get("replicaCount"), 1)

    def test_opensearch_seed_values_dashboards_disabled(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        self.assertFalse(
            parsed.get("dashboards", {}).get("enabled", True),
            msg="dashboards.enabled must be false explicitly on local lane (dev RAM budget)",
        )

    def test_opensearch_seed_values_total_memory_within_dev_budget(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))

        def _to_mi(mem: str) -> float:
            if mem.endswith("Gi"):
                return float(mem[:-2]) * 1024.0
            if mem.endswith("Mi"):
                return float(mem[:-2])
            raise AssertionError(f"unexpected memory unit: {mem}")

        master_limit = _to_mi(parsed["master"]["resources"]["limits"]["memory"])
        coordinating_limit = _to_mi(parsed["coordinating"]["resources"]["limits"]["memory"])
        total = master_limit + coordinating_limit
        self.assertLessEqual(
            total, 1536.0,
            msg=f"total memory limit (master+coordinating)={total}Mi exceeds 1.5Gi dev budget",
        )

    def test_opensearch_seed_values_image_pinned(self) -> None:
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        image = parsed.get("image", {})
        self.assertEqual(image.get("registry"), "docker.io")
        self.assertEqual(image.get("repository"), "bitnamilegacy/opensearch")
        self.assertTrue(image.get("tag", "").startswith("2.19."),
                        msg=f"image tag must be 2.19.x to match chart 1.6.x app version, got: {image.get('tag')}")


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

    def test_opensearch_chart_version_pinned_to_supported_line(self) -> None:
        content = _VERSIONS_SH.read_text(encoding="utf-8")
        self.assertIn(
            'OPENSEARCH_HELM_CHART_VERSION_PIN="1.6.3"', content,
            msg="chart 1.6.3 (app 2.19.1) is the verified pin matching STACKIT 2.x family",
        )


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


class OpenSearchSmokeScriptTests(unittest.TestCase):
    """Smoke script tests. Backs up and restores any pre-existing canonical
    state file so a developer's local apply state isn't clobbered by the test."""

    def _run_smoke(self, state_content: str) -> int:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        runtime_env = _STATE_DIR / "opensearch_runtime.env"
        backup = None
        if runtime_env.exists():
            backup = runtime_env.read_bytes()
        runtime_env.write_text(state_content, encoding="utf-8")
        try:
            result = run(
                ["bash", str(_SMOKE_SH)],
                {"BLUEPRINT_PROFILE": "local-full", "OPENSEARCH_ENABLED": "true"},
            )
            return result.returncode
        finally:
            if backup is not None:
                runtime_env.write_bytes(backup)
            else:
                runtime_env.unlink(missing_ok=True)

    def test_opensearch_smoke_fails_when_uri_empty(self) -> None:
        rc = self._run_smoke("uri=\ndashboard_url=\n")
        self.assertNotEqual(rc, 0, msg="smoke should fail when uri is empty")

    def test_opensearch_smoke_passes_with_valid_uri_and_empty_dashboard(self) -> None:
        rc = self._run_smoke(
            "uri=http://blueprint-opensearch.search.svc.cluster.local:9200\n"
            "dashboard_url=\n"
        )
        self.assertEqual(rc, 0, msg="smoke should pass with valid URI and empty dashboard_url (local lane)")

    def test_opensearch_smoke_passes_with_https_dashboard(self) -> None:
        rc = self._run_smoke(
            "uri=https://opensearch.example.invalid:443\n"
            "dashboard_url=https://opensearch.example.invalid\n"
        )
        self.assertEqual(rc, 0, msg="smoke should pass with https dashboard URL (STACKIT lane)")


class OpenSearchApplyScriptTests(unittest.TestCase):
    def test_opensearch_apply_local_calls_helm_upgrade(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("helm)", content, msg="opensearch_apply.sh missing helm) case")
        self.assertIn("run_helm_upgrade_install", content)
        self.assertIn("opensearch_render_values_file", content)

    def test_opensearch_apply_reconciles_runtime_secret_before_helm(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("opensearch_reconcile_runtime_secret", content,
                      msg="apply must reconcile the K8s Secret before helm upgrade")
        reconcile_idx = content.index("opensearch_reconcile_runtime_secret")
        helm_idx = content.index("run_helm_upgrade_install")
        self.assertLess(reconcile_idx, helm_idx,
                        msg="secret reconcile must run BEFORE helm upgrade so chart can mount it")

    def test_opensearch_apply_sources_fallback_runtime(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("scripts/lib/infra/fallback_runtime.sh", content,
                      msg="apply must source fallback_runtime.sh explicitly")


class OpenSearchPlanScriptTests(unittest.TestCase):
    def test_opensearch_plan_local_has_helm_case(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("helm)", content, msg="opensearch_plan.sh missing helm) case")
        self.assertIn("run_helm_template", content)

    def test_opensearch_plan_drops_dead_noop_case(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertNotIn("noop)", content,
                         msg="opensearch never resolves to noop driver after dual-lane routing; remove dead arm")

    def test_opensearch_plan_sources_fallback_runtime(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("scripts/lib/infra/fallback_runtime.sh", content)


class OpenSearchDestroyScriptTests(unittest.TestCase):
    def test_opensearch_destroy_local_has_helm_case(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn("helm)", content, msg="opensearch_destroy.sh missing helm) case")
        self.assertIn("run_helm_uninstall", content)

    def test_opensearch_destroy_deletes_runtime_secret_after_uninstall(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn("opensearch_delete_runtime_secret", content,
                      msg="destroy must delete the K8s Secret to leave no residue")
        helm_idx = content.index("run_helm_uninstall")
        delete_idx = content.index("opensearch_delete_runtime_secret")
        self.assertLess(helm_idx, delete_idx,
                        msg="secret delete must run AFTER helm uninstall releases its mount")

    def test_opensearch_destroy_drops_dead_noop_case(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertNotIn("noop)", content,
                         msg="opensearch never resolves to noop driver after dual-lane routing; remove dead arm")

    def test_opensearch_destroy_sources_fallback_runtime(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn("scripts/lib/infra/fallback_runtime.sh", content)


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

    def test_opensearch_username_locked_to_admin_for_local(self) -> None:
        # Bitnami chart hard-codes OPENSEARCH_USERNAME=admin in the StatefulSet
        # env. Even with OPENSEARCH_USERNAME override, the actual auth user is
        # always 'admin'. opensearch_username() must return literal "admin"
        # for local to avoid drift between state file and runtime reality.
        username = _run_opensearch_bash(
            "OPENSEARCH_USERNAME=intruder opensearch_username"
        )
        self.assertEqual(username, "admin",
                         msg="username must be literal 'admin' on local; chart ignores overrides")

    def test_opensearch_dashboard_url_empty_on_local(self) -> None:
        # Local lane runs with dashboards.enabled=false; emit empty so smoke
        # check distinguishes "intentionally empty" from "broken contract".
        url = _run_opensearch_bash("opensearch_dashboard_url")
        self.assertEqual(url, "")

    def test_opensearch_password_secret_name_follows_module_convention(self) -> None:
        secret_name = _run_opensearch_bash("opensearch_password_secret_name")
        self.assertEqual(secret_name, "blueprint-opensearch-auth")

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


class OpenSearchLibraryFunctionPresenceTests(unittest.TestCase):
    def test_opensearch_lib_defines_secret_reconcile_functions(self) -> None:
        content = _OPENSEARCH_LIB.read_text(encoding="utf-8")
        for fn in (
            "opensearch_password_secret_name()",
            "opensearch_reconcile_runtime_secret()",
            "opensearch_delete_runtime_secret()",
        ):
            self.assertIn(fn, content, msg=f"missing function: {fn}")

    def test_opensearch_lib_does_not_pass_user_pass_to_values_render(self) -> None:
        content = _OPENSEARCH_LIB.read_text(encoding="utf-8")
        # Username is locked to "admin"; password is reconciled via Secret.
        # Neither belongs in the rendered values placeholder list.
        render_block = content.split("opensearch_render_values_file()")[1].split("\n}\n")[0]
        self.assertNotIn("OPENSEARCH_USERNAME=", render_block,
                         msg="username must not be a values placeholder; chart hardcodes it")
        self.assertNotIn("OPENSEARCH_PASSWORD=", render_block,
                         msg="password must not be embedded in values.yaml; reconciled via Secret")
        self.assertIn("OPENSEARCH_PASSWORD_SECRET_NAME=", render_block,
                      msg="values must reference the Secret name, not the password value")
