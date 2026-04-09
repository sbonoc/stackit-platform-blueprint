from __future__ import annotations

import os
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
import json

from tests._shared.helpers import REPO_ROOT, module_flags_env, run_make


class RuntimeCredentialsEsoTests(unittest.TestCase):
    def tearDown(self) -> None:
        state_paths = (
            REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env",
            REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.json",
            REPO_ROOT / "artifacts" / "infra" / "argocd_repo_credentials_reconcile.env",
            REPO_ROOT / "artifacts" / "infra" / "argocd_repo_credentials_reconcile.json",
            REPO_ROOT / "artifacts" / "infra" / "runtime_identity_reconcile.env",
            REPO_ROOT / "artifacts" / "infra" / "runtime_identity_reconcile.json",
        )
        for state_path in state_paths:
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
        state_json_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.json"
        self.assertTrue(state_json_path.exists(), msg="runtime credentials JSON state artifact was not created")
        state_json = json.loads(state_json_path.read_text(encoding="utf-8"))
        self.assertEqual(state_json.get("artifact", {}).get("name"), "runtime_credentials_eso_reconcile")
        self.assertEqual(state_json.get("artifact", {}).get("namespace"), "infra")
        self.assertEqual(state_json.get("entryCount"), len(state_json.get("entryOrder", [])))
        self.assertEqual(state_json.get("entries", {}).get("status"), "success")

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

    def test_empty_contract_set_is_noop_without_source_secret_warning(self) -> None:
        env = module_flags_env(profile="local-full")
        with tempfile.TemporaryDirectory() as tmpdir:
            shim_dir = Path(tmpdir)
            python_shim = shim_dir / "python3"
            python_shim.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        f'target_contract_cli="{REPO_ROOT}/scripts/lib/infra/runtime_identity_contract.py"',
                        'if [[ "${1:-}" == "$target_contract_cli" ]]; then',
                        '  case "${2:-}" in',
                        "    runtime-env-defaults)",
                        "      cat <<'EOF'",
                        "KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED\ttrue",
                        "RUNTIME_CREDENTIALS_SOURCE_NAMESPACE\tsecurity",
                        "RUNTIME_CREDENTIALS_TARGET_NAMESPACE\tapps",
                        "RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT\t180",
                        "RUNTIME_CREDENTIALS_REQUIRED\tfalse",
                        "EOF",
                        "      exit 0",
                        "      ;;",
                        "    eso-contracts)",
                        "      exit 0",
                        "      ;;",
                        "  esac",
                        "fi",
                        f"exec {shlex.quote(sys.executable)} \"$@\"",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            python_shim.chmod(0o755)
            env["PATH"] = f"{shim_dir}:{os.environ.get('PATH', '')}"

            result = run_make("auth-reconcile-eso-runtime-secrets", env)

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        combined_output = result.stdout + result.stderr
        self.assertIn("runtime credential contract set empty; skipping source secret checks", combined_output)
        self.assertNotIn("missing and no literals provided", combined_output)

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        self.assertTrue(state_path.exists(), msg="runtime credentials state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=noop-empty-contract-set", state)
        self.assertIn("source_secret_seed_mode=skipped-empty-contract-set", state)
        self.assertIn("issue_count=0", state)

    def test_argocd_reconcile_resolves_repo_contract_without_argparse_errors(self) -> None:
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "ARGOCD_REPO_CREDENTIALS_REQUIRED": "true",
                "ARGOCD_REPO_TOKEN": "ghp_exampletoken",
            }
        )

        result = run_make("auth-reconcile-argocd-repo-credentials", env)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        combined_output = result.stdout + result.stderr
        self.assertNotIn("argocd_repo_contract.py: error: unrecognized arguments", combined_output)
        self.assertNotIn("ghp_exampletoken", combined_output)

        state_path = REPO_ROOT / "artifacts" / "infra" / "argocd_repo_credentials_reconcile.env"
        self.assertTrue(state_path.exists(), msg="argocd repo credentials state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=success", state)
        self.assertIn("runtime_reconcile_status=success", state)
        self.assertNotIn("ghp_exampletoken", state)
        state_json_path = REPO_ROOT / "artifacts" / "infra" / "argocd_repo_credentials_reconcile.json"
        self.assertTrue(state_json_path.exists(), msg="argocd repo credentials JSON state artifact was not created")
        state_json = state_json_path.read_text(encoding="utf-8")
        self.assertNotIn("ghp_exampletoken", state_json)

    def test_argocd_reconcile_ignores_unrelated_env_vars_and_fails_required_without_argocd_token(self) -> None:
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "ARGOCD_REPO_CREDENTIALS_REQUIRED": "true",
                "ARGOCD_REPO_USERNAME": "",
                "ARGOCD_REPO_TOKEN": "",
                "UNRELATED_GITOPS_REPO_USERNAME": "x-access-token",
                "UNRELATED_GITOPS_REPO_TOKEN": "ghp_unrelatedtoken",
            }
        )

        result = run_make("auth-reconcile-argocd-repo-credentials", env)
        self.assertNotEqual(result.returncode, 0, msg="required mode must fail when ARGOCD_REPO_TOKEN is unset")

        combined_output = result.stdout + result.stderr
        self.assertNotIn("ghp_unrelatedtoken", combined_output)
        self.assertIn("ARGOCD_REPO_TOKEN is empty", combined_output)

        state_path = REPO_ROOT / "artifacts" / "infra" / "argocd_repo_credentials_reconcile.env"
        self.assertTrue(state_path.exists(), msg="argocd repo credentials state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=failed-required", state)
        self.assertNotIn("ghp_unrelatedtoken", state)

        state_json_path = REPO_ROOT / "artifacts" / "infra" / "argocd_repo_credentials_reconcile.json"
        self.assertTrue(state_json_path.exists(), msg="argocd repo credentials JSON state artifact was not created")
        state_json = state_json_path.read_text(encoding="utf-8")
        self.assertNotIn("ghp_unrelatedtoken", state_json)

    def test_runtime_identity_orchestrator_writes_plugin_state(self) -> None:
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "ARGOCD_REPO_TOKEN": "ghp_exampletoken",
            }
        )

        result = run_make("auth-reconcile-runtime-identity", env)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_identity_reconcile.env"
        self.assertTrue(state_path.exists(), msg="runtime identity reconcile state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=success", state)
        self.assertIn("plugin_eso_status=success", state)
        self.assertIn("plugin_argocd_repo_status=success", state)
        self.assertRegex(state, r"plugin_keycloak_contract_status=(success|skipped-no-enabled-realm-contracts)")
        self.assertIn("runtime_credentials_state=", state)
        self.assertIn("argocd_repo_state=", state)

        state_json_path = REPO_ROOT / "artifacts" / "infra" / "runtime_identity_reconcile.json"
        self.assertTrue(state_json_path.exists(), msg="runtime identity reconcile JSON state artifact was not created")


if __name__ == "__main__":
    unittest.main()
