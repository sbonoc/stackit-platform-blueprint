from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT, module_flags_env, run_make


class RuntimeCredentialsEsoTests(unittest.TestCase):
    def tearDown(self) -> None:
        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        if state_path.exists():
            state_path.unlink()

    def test_dry_run_reconcile_writes_success_state_and_renders_source_secret(self) -> None:
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS": "username=dev-user,password=dev-password",
            }
        )

        result = run_make("auth-reconcile-eso-runtime-secrets", env)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        self.assertTrue(state_path.exists(), msg="runtime credentials state artifact was not created")

        state = state_path.read_text(encoding="utf-8")
        self.assertIn("enabled=true", state)
        self.assertIn("status=success", state)
        self.assertIn("source_secret_seed_mode=manifest-rendered", state)
        self.assertIn("target_namespace=apps", state)
        self.assertIn("target_secret_name=runtime-credentials", state)

        rendered_secret_path = (
            REPO_ROOT
            / "artifacts"
            / "infra"
            / "rendered"
            / "secrets"
            / "secret-security-runtime-credentials-source.yaml"
        )
        self.assertTrue(rendered_secret_path.exists(), msg="dry-run source secret manifest was not rendered")
        rendered_secret = rendered_secret_path.read_text(encoding="utf-8")
        self.assertIn("name: runtime-credentials-source", rendered_secret)
        self.assertIn("namespace: security", rendered_secret)

    def test_required_mode_fails_on_invalid_literal_contract(self) -> None:
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "RUNTIME_CREDENTIALS_REQUIRED": "true",
                "RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS": "missing-separator",
            }
        )

        result = run_make("auth-reconcile-eso-runtime-secrets", env)
        self.assertNotEqual(result.returncode, 0, msg="required mode should fail on invalid source literal format")

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        self.assertTrue(state_path.exists(), msg="runtime credentials state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("required=true", state)
        self.assertIn("status=failed-required", state)


if __name__ == "__main__":
    unittest.main()
