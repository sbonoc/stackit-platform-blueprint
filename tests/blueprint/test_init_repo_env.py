from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.lib.blueprint.init_repo_contract import load_blueprint_contract_for_init
from scripts.lib.blueprint.init_repo_env import (
    non_sensitive_module_required_env_specs,
    render_defaults_env_file_content,
    render_secrets_example_env_file_content,
    runtime_credentials_env_specs,
    sensitive_env_specs,
    sensitive_module_required_env_specs,
)
from tests._shared.helpers import REPO_ROOT


class InitRepoEnvTests(unittest.TestCase):
    def _module_enablement(self, enabled_modules: set[str]) -> dict[str, bool]:
        contract = load_blueprint_contract_for_init(REPO_ROOT)
        module_enablement = {module.module_id: False for module in contract.optional_modules.modules.values()}
        for module_id in enabled_modules:
            module_enablement[module_id] = True
        return module_enablement

    def test_enabled_module_required_inputs_split_by_sensitivity(self) -> None:
        module_enablement = self._module_enablement(
            {"postgres", "object-storage", "public-endpoints", "identity-aware-proxy"}
        )

        with patch.dict(
            os.environ,
            {
                "POSTGRES_INSTANCE_NAME": "",
                "POSTGRES_DB_NAME": "",
                "POSTGRES_USER": "",
                "POSTGRES_PASSWORD": "",
                "OBJECT_STORAGE_BUCKET_NAME": "",
                "PUBLIC_ENDPOINTS_BASE_DOMAIN": "",
                "IAP_UPSTREAM_URL": "",
                "IAP_COOKIE_SECRET": "",
                "KEYCLOAK_ISSUER_URL": "",
                "KEYCLOAK_CLIENT_ID": "",
                "KEYCLOAK_CLIENT_SECRET": "",
            },
            clear=False,
        ):
            non_sensitive = dict(non_sensitive_module_required_env_specs(REPO_ROOT, module_enablement))
            sensitive = dict(sensitive_module_required_env_specs(REPO_ROOT, module_enablement))

        self.assertEqual(non_sensitive["POSTGRES_INSTANCE_NAME"], "blueprint-postgres")
        self.assertEqual(non_sensitive["POSTGRES_DB_NAME"], "platform")
        self.assertEqual(non_sensitive["POSTGRES_USER"], "platform")
        self.assertEqual(non_sensitive["OBJECT_STORAGE_BUCKET_NAME"], "marketplace-assets")
        self.assertEqual(non_sensitive["PUBLIC_ENDPOINTS_BASE_DOMAIN"], "apps.local")
        self.assertEqual(non_sensitive["IAP_UPSTREAM_URL"], "http://catalog.apps.svc.cluster.local:8080")
        self.assertEqual(non_sensitive["KEYCLOAK_ISSUER_URL"], "https://auth.example.invalid/realms/iap")
        self.assertEqual(non_sensitive["KEYCLOAK_CLIENT_ID"], "iap-client")
        self.assertNotIn("POSTGRES_PASSWORD", non_sensitive)
        self.assertNotIn("IAP_COOKIE_SECRET", non_sensitive)
        self.assertNotIn("KEYCLOAK_CLIENT_SECRET", non_sensitive)

        self.assertEqual(sensitive["POSTGRES_PASSWORD"], "platform-password")
        self.assertEqual(sensitive["IAP_COOKIE_SECRET"], "0123456789abcdef0123456789abcdef")
        self.assertEqual(sensitive["KEYCLOAK_CLIENT_SECRET"], "blueprint-client-secret")
        self.assertNotIn("KEYCLOAK_CLIENT_ID", sensitive)

    def test_defaults_env_render_includes_non_sensitive_required_module_inputs(self) -> None:
        rendered = render_defaults_env_file_content(
            identity_specs=[("BLUEPRINT_REPO_NAME", "acme-platform")],
            module_flag_specs=[("POSTGRES_ENABLED", "true"), ("IDENTITY_AWARE_PROXY_ENABLED", "true")],
            module_required_specs=[
                ("POSTGRES_INSTANCE_NAME", "blueprint-postgres"),
                ("POSTGRES_DB_NAME", "platform"),
                ("POSTGRES_USER", "platform"),
                ("IAP_UPSTREAM_URL", "http://catalog.apps.svc.cluster.local:8080"),
                ("KEYCLOAK_CLIENT_ID", "blueprint-client"),
            ],
            runtime_credentials_specs=[
                ("KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED", "true"),
                ("RUNTIME_CREDENTIALS_SOURCE_NAMESPACE", "security"),
                ("RUNTIME_CREDENTIALS_TARGET_NAMESPACE", "apps"),
                ("RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT", "180"),
                ("RUNTIME_CREDENTIALS_REQUIRED", "false"),
            ],
        )

        self.assertIn("POSTGRES_ENABLED=true", rendered)
        self.assertIn("IDENTITY_AWARE_PROXY_ENABLED=true", rendered)
        self.assertIn("# Required non-sensitive module inputs for currently enabled optional modules", rendered)
        self.assertIn("POSTGRES_INSTANCE_NAME=blueprint-postgres", rendered)
        self.assertIn("POSTGRES_DB_NAME=platform", rendered)
        self.assertIn("POSTGRES_USER=platform", rendered)
        self.assertIn("IAP_UPSTREAM_URL=http://catalog.apps.svc.cluster.local:8080", rendered)
        self.assertIn("KEYCLOAK_CLIENT_ID=blueprint-client", rendered)
        self.assertIn("# Runtime credential contract", rendered)
        self.assertIn("KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED=true", rendered)
        self.assertIn("RUNTIME_CREDENTIALS_SOURCE_NAMESPACE=security", rendered)
        self.assertIn("RUNTIME_CREDENTIALS_TARGET_NAMESPACE=apps", rendered)
        self.assertIn("RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT=180", rendered)
        self.assertIn("RUNTIME_CREDENTIALS_REQUIRED=false", rendered)

    def test_runtime_credentials_env_specs_default_and_override(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            defaults = dict(runtime_credentials_env_specs())
        self.assertEqual(defaults["KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED"], "true")
        self.assertEqual(defaults["RUNTIME_CREDENTIALS_SOURCE_NAMESPACE"], "security")
        self.assertEqual(defaults["RUNTIME_CREDENTIALS_TARGET_NAMESPACE"], "apps")
        self.assertEqual(defaults["RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT"], "180")
        self.assertEqual(defaults["RUNTIME_CREDENTIALS_REQUIRED"], "false")

        with patch.dict(
            os.environ,
            {
                "KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED": "false",
                "RUNTIME_CREDENTIALS_SOURCE_NAMESPACE": "custom-security",
                "RUNTIME_CREDENTIALS_TARGET_NAMESPACE": "custom-apps",
                "RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT": "60",
                "RUNTIME_CREDENTIALS_REQUIRED": "true",
            },
            clear=False,
        ):
            overrides = dict(runtime_credentials_env_specs())

        self.assertEqual(overrides["KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED"], "false")
        self.assertEqual(overrides["RUNTIME_CREDENTIALS_SOURCE_NAMESPACE"], "custom-security")
        self.assertEqual(overrides["RUNTIME_CREDENTIALS_TARGET_NAMESPACE"], "custom-apps")
        self.assertEqual(overrides["RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT"], "60")
        self.assertEqual(overrides["RUNTIME_CREDENTIALS_REQUIRED"], "true")

    def test_runtime_credentials_env_specs_uses_passed_repo_root(self) -> None:
        custom_repo_root = Path("/tmp/custom-blueprint-root")
        with patch(
            "scripts.lib.blueprint.init_repo_env.load_runtime_identity_contract",
            return_value=SimpleNamespace(runtime_env_defaults=[]),
        ) as load_contract:
            resolved = runtime_credentials_env_specs(custom_repo_root)

        self.assertEqual(resolved, [])
        load_contract.assert_called_once_with(custom_repo_root / "blueprint/runtime_identity_contract.yaml")

    def test_secrets_example_render_keeps_module_sensitive_placeholders_non_empty(self) -> None:
        module_enablement = self._module_enablement({"postgres", "identity-aware-proxy"})
        with patch.dict(
            os.environ,
            {
                "POSTGRES_PASSWORD": "env-postgres-password",
                "IAP_COOKIE_SECRET": "env-cookie-secret-0123456789",
                "KEYCLOAK_CLIENT_SECRET": "env-keycloak-secret",
            },
            clear=False,
        ):
            sensitive_specs = sensitive_env_specs(REPO_ROOT, module_enablement)
            rendered = render_secrets_example_env_file_content(sensitive_specs)

        self.assertIn("STACKIT_SERVICE_ACCOUNT_KEY=", rendered)
        self.assertIn("STACKIT_TFSTATE_SECRET_ACCESS_KEY=", rendered)
        self.assertIn("POSTGRES_PASSWORD=platform-password", rendered)
        self.assertIn("IAP_COOKIE_SECRET=0123456789abcdef0123456789abcdef", rendered)
        self.assertIn("KEYCLOAK_CLIENT_SECRET=blueprint-client-secret", rendered)
        self.assertNotIn("env-postgres-password", rendered)
        self.assertNotIn("env-cookie-secret-0123456789", rendered)
        self.assertNotIn("env-keycloak-secret", rendered)


if __name__ == "__main__":
    unittest.main()
