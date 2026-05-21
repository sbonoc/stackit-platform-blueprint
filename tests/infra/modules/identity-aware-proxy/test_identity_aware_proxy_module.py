from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from tests._shared.helpers import REPO_ROOT, run

_IAP_LIB = REPO_ROOT / "scripts" / "lib" / "infra" / "identity_aware_proxy.sh"
_PLAN_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "identity_aware_proxy_plan.sh"
_APPLY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "identity_aware_proxy_apply.sh"
_DEPLOY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "identity_aware_proxy_deploy.sh"
_SMOKE_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "identity_aware_proxy_smoke.sh"
_DESTROY_SH = REPO_ROOT / "scripts" / "bin" / "infra" / "identity_aware_proxy_destroy.sh"
_SEED_VALUES = REPO_ROOT / "infra" / "local" / "helm" / "identity-aware-proxy" / "values.yaml"
_VERSIONS_SH = REPO_ROOT / "scripts" / "lib" / "infra" / "versions.sh"
_STATE_DIR = REPO_ROOT / "artifacts" / "infra"

_ALL_SCRIPTS = [_PLAN_SH, _APPLY_SH, _DEPLOY_SH, _SMOKE_SH, _DESTROY_SH]


class IdentityAwareProxyLibraryFunctionPresenceTests(unittest.TestCase):
    def test_lib_defines_seed_env_defaults(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_seed_env_defaults()", content)

    def test_lib_defines_validate_cookie_secret(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_validate_cookie_secret()", content)

    def test_lib_defines_init_env(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_init_env()", content)

    def test_lib_defines_config_secret_name(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_config_secret_name()", content)

    def test_lib_defines_render_values_file(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_render_values_file()", content)

    def test_lib_defines_reconcile_runtime_secret(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_reconcile_runtime_secret()", content)

    def test_lib_defines_delete_runtime_secret(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_delete_runtime_secret()", content)

    def test_validate_cookie_secret_accepts_16_bytes(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("16", content, msg="validate_cookie_secret must accept 16-byte secrets")

    def test_validate_cookie_secret_accepts_24_bytes(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("24", content, msg="validate_cookie_secret must accept 24-byte secrets")

    def test_validate_cookie_secret_accepts_32_bytes(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("32", content, msg="validate_cookie_secret must accept 32-byte secrets")

    def test_validate_cookie_secret_calls_log_fatal_on_invalid_length(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        self.assertIn("log_fatal", content)
        self.assertIn("IAP_COOKIE_SECRET must be a raw 16, 24, or 32 byte string", content)

    def test_reconcile_secret_does_not_embed_credentials_in_values_render(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        render_block = content.split("identity_aware_proxy_render_values_file()")[1].split("\n}\n")[0]
        self.assertNotIn(
            "IAP_COOKIE_SECRET=", render_block,
            msg="cookie secret must not be embedded in rendered values; delivered via K8s Secret",
        )
        self.assertNotIn(
            "KEYCLOAK_CLIENT_SECRET=", render_block,
            msg="client secret must not be embedded in rendered values; delivered via K8s Secret",
        )
        self.assertIn(
            "IAP_CONFIG_SECRET_NAME=", render_block,
            msg="values render must pass the Secret name so chart can reference it via existingSecret",
        )

    def test_config_secret_name_derived_from_helm_release(self) -> None:
        content = _IAP_LIB.read_text(encoding="utf-8")
        fn_block = content.split("identity_aware_proxy_config_secret_name()")[1].split("\n}\n")[0]
        self.assertIn("IAP_HELM_RELEASE", fn_block)
        self.assertIn("-config", fn_block)


class IdentityAwareProxyScriptInvariantTests(unittest.TestCase):
    def test_all_scripts_source_identity_aware_proxy_lib(self) -> None:
        for script in _ALL_SCRIPTS:
            content = script.read_text(encoding="utf-8")
            self.assertIn(
                "identity_aware_proxy.sh", content,
                msg=f"{script.name} must source identity_aware_proxy.sh",
            )

    def test_all_scripts_have_metric_trap(self) -> None:
        for script in _ALL_SCRIPTS:
            content = script.read_text(encoding="utf-8")
            self.assertIn(
                "start_script_metric_trap", content,
                msg=f"{script.name} must call start_script_metric_trap",
            )

    def test_lifecycle_scripts_guard_on_module_enabled(self) -> None:
        # destroy relies on resolve_optional_module_execution for the skip path
        guarded = [_PLAN_SH, _APPLY_SH, _DEPLOY_SH, _SMOKE_SH]
        for script in guarded:
            content = script.read_text(encoding="utf-8")
            self.assertIn(
                "is_module_enabled", content,
                msg=f"{script.name} must check is_module_enabled before any side effects",
            )


class IdentityAwareProxySkipPathTests(unittest.TestCase):
    def _run_script(self, script: Path) -> int:
        result = run(
            ["bash", str(script)],
            {"IDENTITY_AWARE_PROXY_ENABLED": "false"},
        )
        return result.returncode

    def test_plan_exits_0_when_module_disabled(self) -> None:
        self.assertEqual(
            self._run_script(_PLAN_SH), 0,
            msg="identity_aware_proxy_plan.sh must exit 0 when IDENTITY_AWARE_PROXY_ENABLED=false",
        )

    def test_apply_exits_0_when_module_disabled(self) -> None:
        self.assertEqual(
            self._run_script(_APPLY_SH), 0,
            msg="identity_aware_proxy_apply.sh must exit 0 when IDENTITY_AWARE_PROXY_ENABLED=false",
        )

    def test_deploy_exits_0_when_module_disabled(self) -> None:
        self.assertEqual(
            self._run_script(_DEPLOY_SH), 0,
            msg="identity_aware_proxy_deploy.sh must exit 0 when IDENTITY_AWARE_PROXY_ENABLED=false",
        )

    def test_smoke_exits_0_when_module_disabled(self) -> None:
        self.assertEqual(
            self._run_script(_SMOKE_SH), 0,
            msg="identity_aware_proxy_smoke.sh must exit 0 when IDENTITY_AWARE_PROXY_ENABLED=false",
        )

    def test_destroy_exits_0_when_module_disabled(self) -> None:
        self.assertEqual(
            self._run_script(_DESTROY_SH), 0,
            msg="identity_aware_proxy_destroy.sh must exit 0 when IDENTITY_AWARE_PROXY_ENABLED=false",
        )


class IdentityAwareProxyPlanStateContractTests(unittest.TestCase):
    def test_plan_script_writes_provision_driver_to_state(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("provision_driver=", content)

    def test_plan_script_writes_public_host_to_state(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("public_host=", content)

    def test_plan_script_writes_public_url_to_state(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("public_url=", content)

    def test_plan_script_writes_gateway_name_to_state(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("gateway_name=", content)

    def test_plan_script_writes_keycloak_issuer_to_state(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("keycloak_issuer=", content)

    def test_plan_script_writes_keycloak_client_id_to_state(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("keycloak_client_id=", content)

    def test_plan_script_does_not_write_cookie_secret_to_state(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        state_block = content.split("write_state_file")[1].split(")")[0]
        self.assertNotIn(
            "IAP_COOKIE_SECRET", state_block,
            msg="IAP_COOKIE_SECRET must never be written to the plan state file (NFR-SEC-001)",
        )

    def test_plan_script_does_not_write_client_secret_to_state(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        state_block = content.split("write_state_file")[1].split(")")[0]
        self.assertNotIn(
            "KEYCLOAK_CLIENT_SECRET", state_block,
            msg="KEYCLOAK_CLIENT_SECRET must never be written to the plan state file (NFR-SEC-001)",
        )

    def test_plan_script_writes_auth_mode_browser_oidc_proxy(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("auth_mode=browser_oidc_proxy", content)

    def test_plan_script_writes_route_mode_gateway_api(self) -> None:
        content = _PLAN_SH.read_text(encoding="utf-8")
        self.assertIn("route_mode=gateway_api", content)


class IdentityAwareProxyApplyScriptTests(unittest.TestCase):
    def test_apply_reconciles_secret_before_helm_install(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_reconcile_runtime_secret", content)
        reconcile_idx = content.index("identity_aware_proxy_reconcile_runtime_secret")
        helm_idx = content.index("run_helm_upgrade_install")
        self.assertLess(
            reconcile_idx, helm_idx,
            msg="secret reconcile must run BEFORE helm upgrade so chart can mount it at pod start",
        )

    def test_apply_writes_auth_mode_and_route_mode_to_runtime_state(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("auth_mode=browser_oidc_proxy", content)
        self.assertIn("route_mode=gateway_api", content)

    def test_apply_writes_provision_status_to_runtime_state(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("provision_status=", content)

    def test_apply_requires_plan_state_before_proceeding(self) -> None:
        content = _APPLY_SH.read_text(encoding="utf-8")
        self.assertIn("identity_aware_proxy_plan", content,
                      msg="apply must check for plan state file before running")


class IdentityAwareProxyDestroyScriptTests(unittest.TestCase):
    def test_destroy_uninstalls_helm_before_deleting_secret_in_helm_case(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        # Extract the helm) case block specifically; ordering only applies within that branch
        helm_case = content.split("helm)")[1].split(";;")[0]
        self.assertIn("run_helm_uninstall", helm_case)
        self.assertIn("identity_aware_proxy_delete_runtime_secret", helm_case)
        helm_idx = helm_case.index("run_helm_uninstall")
        delete_idx = helm_case.index("identity_aware_proxy_delete_runtime_secret")
        self.assertLess(
            helm_idx, delete_idx,
            msg="helm uninstall must run BEFORE secret deletion in the helm case",
        )

    def test_destroy_removes_all_state_files_by_prefix(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn(
            'remove_state_files_by_prefix "identity_aware_proxy_"', content,
            msg="destroy must remove all identity_aware_proxy_* state files",
        )

    def test_destroy_uses_placeholder_credentials_for_teardown(self) -> None:
        content = _DESTROY_SH.read_text(encoding="utf-8")
        self.assertIn(
            "set_default_env KEYCLOAK_CLIENT_SECRET", content,
            msg="destroy must set placeholder client secret so teardown runs without live OIDC wiring",
        )
        self.assertIn(
            "set_default_env IAP_COOKIE_SECRET", content,
            msg="destroy must set placeholder cookie secret so init_env validation passes",
        )


class IdentityAwareProxySmokeStateContractTests(unittest.TestCase):
    def _run_smoke_with_runtime(self, state_content: str, values_content: str) -> int:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        runtime_env = _STATE_DIR / "identity_aware_proxy_runtime.env"
        backup = None
        if runtime_env.exists():
            backup = runtime_env.read_bytes()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".values.yaml", delete=False, encoding="utf-8"
        ) as vf:
            vf.write(values_content)
            values_path = vf.name

        full_state = state_content + f"\nprovision_path={values_path}\n"
        runtime_env.write_text(full_state, encoding="utf-8")
        try:
            result = run(
                ["bash", str(_SMOKE_SH)],
                {
                    "IDENTITY_AWARE_PROXY_ENABLED": "true",
                    "BLUEPRINT_PROFILE": "local-full",
                    "KEYCLOAK_ISSUER_URL": "https://auth.example.com/realms/myrealm",
                    "KEYCLOAK_CLIENT_ID": "iap-client",
                    "KEYCLOAK_CLIENT_SECRET": "test-secret",
                    "IAP_COOKIE_SECRET": "0123456789abcdef",
                    "IAP_UPSTREAM_URL": "http://catalog.apps.svc.cluster.local:8080",
                },
            )
            return result.returncode
        finally:
            Path(values_path).unlink(missing_ok=True)
            if backup is not None:
                runtime_env.write_bytes(backup)
            else:
                runtime_env.unlink(missing_ok=True)

    def _valid_values(
        self,
        gateway_name: str = "public-endpoints",
        gateway_namespace: str = "network",
        public_host: str = "iap.local",
    ) -> str:
        return (
            "gatewayApi:\n"
            "  enabled: true\n"
            f'  gatewayRef:\n    name: "{gateway_name}"\n    namespace: "{gateway_namespace}"\n'
            f"hostnames:\n  - {public_host}\n"
        )

    def _valid_runtime_state(
        self,
        public_host: str = "iap.local",
        gateway_name: str = "public-endpoints",
        gateway_namespace: str = "network",
    ) -> str:
        return (
            f"keycloak_issuer=https://auth.example.com/realms/myrealm\n"
            f"public_host={public_host}\n"
            f"public_url=https://{public_host}\n"
            f"gateway_name={gateway_name}\n"
            f"gateway_namespace={gateway_namespace}\n"
        )

    def test_smoke_passes_with_valid_runtime_state_and_values(self) -> None:
        rc = self._run_smoke_with_runtime(self._valid_runtime_state(), self._valid_values())
        self.assertEqual(rc, 0, msg="smoke must pass with valid runtime state and valid values artifact")

    def test_smoke_fails_when_runtime_oidc_issuer_is_missing(self) -> None:
        state = (
            "public_host=iap.local\n"
            "public_url=https://iap.local\n"
            "gateway_name=public-endpoints\n"
            "gateway_namespace=network\n"
        )
        rc = self._run_smoke_with_runtime(state, self._valid_values())
        self.assertNotEqual(rc, 0, msg="smoke must fail when keycloak_issuer is absent from runtime state")

    def test_smoke_fails_when_gatewayapi_block_missing_from_values(self) -> None:
        values = "config:\n  provider: oidc\n"
        rc = self._run_smoke_with_runtime(self._valid_runtime_state(), values)
        self.assertNotEqual(rc, 0, msg="smoke must fail when gatewayApi block is absent from values artifact")

    def test_smoke_fails_when_public_host_missing_from_runtime_state(self) -> None:
        state = (
            "keycloak_issuer=https://auth.example.com/realms/myrealm\n"
            "gateway_name=public-endpoints\n"
            "gateway_namespace=network\n"
        )
        rc = self._run_smoke_with_runtime(state, self._valid_values())
        self.assertNotEqual(rc, 0, msg="smoke must fail when public_host is absent from runtime state")

    def test_smoke_script_does_not_write_cookie_secret_to_state(self) -> None:
        content = _SMOKE_SH.read_text(encoding="utf-8")
        state_block = content.split("write_state_file")[1].split(")")[0]
        self.assertNotIn(
            "IAP_COOKIE_SECRET", state_block,
            msg="IAP_COOKIE_SECRET must never be written to the smoke state file (NFR-SEC-001)",
        )

    def test_smoke_script_does_not_write_client_secret_to_state(self) -> None:
        content = _SMOKE_SH.read_text(encoding="utf-8")
        state_block = content.split("write_state_file")[1].split(")")[0]
        self.assertNotIn(
            "KEYCLOAK_CLIENT_SECRET", state_block,
            msg="KEYCLOAK_CLIENT_SECRET must never be written to the smoke state file (NFR-SEC-001)",
        )


class IdentityAwareProxyHelmValuesContractTests(unittest.TestCase):
    def test_seed_values_use_existing_secret_not_inline_credentials(self) -> None:
        import yaml
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        config = parsed.get("config", {})
        self.assertIn(
            "existingSecret", config,
            msg="config.existingSecret must be present; credentials delivered via K8s Secret",
        )

    def test_seed_values_do_not_embed_cookie_secret(self) -> None:
        content = _SEED_VALUES.read_text(encoding="utf-8")
        self.assertNotIn(
            "cookieSecret", content,
            msg="values.yaml must not embed cookie secret; delivered via K8s Secret",
        )
        self.assertNotIn(
            "cookie-secret", content,
            msg="values.yaml must not embed cookie secret; delivered via K8s Secret",
        )

    def test_seed_values_enable_gateway_api(self) -> None:
        import yaml
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        gateway_api = parsed.get("gatewayApi", {})
        self.assertTrue(
            gateway_api.get("enabled", False),
            msg="gatewayApi.enabled must be true; HTTPRoute is rendered by the chart",
        )

    def test_seed_values_attach_to_public_endpoints_gateway(self) -> None:
        import yaml
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        gateway_ref = parsed.get("gatewayApi", {}).get("gatewayRef", {})
        self.assertEqual(
            gateway_ref.get("name"), "public-endpoints",
            msg="gatewayRef.name must be 'public-endpoints'; shared Gateway is owned by public-endpoints module",
        )

    def test_seed_values_disable_ingress(self) -> None:
        import yaml
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        ingress = parsed.get("ingress", {})
        self.assertFalse(
            ingress.get("enabled", True),
            msg="ingress.enabled must be false; HTTPRoute via Gateway API is the exposure path",
        )

    def test_seed_values_pin_image_tag(self) -> None:
        import yaml
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        image = parsed.get("image", {})
        self.assertNotEqual(
            image.get("tag", ""), "",
            msg="image.tag must be pinned; chart defaults must not drift",
        )
        self.assertNotEqual(
            image.get("tag", ""), "latest",
            msg="image.tag must not be 'latest'",
        )


class IdentityAwareProxyVersionPinTests(unittest.TestCase):
    def test_versions_sh_declares_chart_version_pin(self) -> None:
        content = _VERSIONS_SH.read_text(encoding="utf-8")
        self.assertIn(
            "IAP_HELM_CHART_VERSION_PIN", content,
            msg="versions.sh must declare IAP_HELM_CHART_VERSION_PIN",
        )

    def test_versions_sh_declares_local_image_tag(self) -> None:
        content = _VERSIONS_SH.read_text(encoding="utf-8")
        self.assertIn(
            "IAP_LOCAL_IMAGE_TAG", content,
            msg="versions.sh must declare IAP_LOCAL_IMAGE_TAG",
        )

    def test_chart_version_pin_is_10_4_0(self) -> None:
        content = _VERSIONS_SH.read_text(encoding="utf-8")
        match = re.search(r'IAP_HELM_CHART_VERSION_PIN="([^"]+)"', content)
        self.assertIsNotNone(match, msg="IAP_HELM_CHART_VERSION_PIN must be quoted in versions.sh")
        self.assertEqual(
            match.group(1), "10.4.0",
            msg="IAP_HELM_CHART_VERSION_PIN must be pinned to 10.4.0",
        )

    def test_image_tag_matches_seed_values(self) -> None:
        import yaml
        versions_content = _VERSIONS_SH.read_text(encoding="utf-8")
        pin_match = re.search(r'IAP_LOCAL_IMAGE_TAG="([^"]+)"', versions_content)
        self.assertIsNotNone(pin_match, msg="IAP_LOCAL_IMAGE_TAG must be set in versions.sh")
        parsed = yaml.safe_load(_SEED_VALUES.read_text(encoding="utf-8"))
        seed_tag = parsed.get("image", {}).get("tag", "")
        self.assertEqual(
            seed_tag, pin_match.group(1),
            msg="image.tag in values.yaml must match IAP_LOCAL_IMAGE_TAG in versions.sh",
        )
