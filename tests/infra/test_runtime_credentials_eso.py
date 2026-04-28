from __future__ import annotations

import base64
import os
from pathlib import Path
import shutil
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
            REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_target_secret_checks.json",
            REPO_ROOT / "artifacts" / "infra" / "argocd_repo_credentials_reconcile.env",
            REPO_ROOT / "artifacts" / "infra" / "argocd_repo_credentials_reconcile.json",
            REPO_ROOT / "artifacts" / "infra" / "runtime_identity_reconcile.env",
            REPO_ROOT / "artifacts" / "infra" / "runtime_identity_reconcile.json",
            REPO_ROOT / "artifacts" / "infra" / "runtime_identity_doctor.env",
            REPO_ROOT / "artifacts" / "infra" / "runtime_identity_doctor.json",
            REPO_ROOT / "artifacts" / "infra" / "runtime_identity_doctor_report.json",
            REPO_ROOT / "artifacts" / "infra" / "postgres_runtime.env",
            REPO_ROOT / "artifacts" / "infra" / "postgres_runtime.json",
        )
        for state_path in state_paths:
            if state_path.exists():
                state_path.unlink()
        target_secret_checks_dir = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_target_secret_checks"
        if target_secret_checks_dir.exists():
            shutil.rmtree(target_secret_checks_dir)

    def test_dry_run_reconcile_writes_success_state_and_renders_source_secret(self) -> None:
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS": "username=dev-user\npassword=dev-password",
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
        self.assertIn(
            base64.b64encode(b"dev-password").decode(),
            rendered_secret,
            msg="both newline-separated literals must appear in the rendered secret",
        )

    def test_comma_in_value_literal_reconciles_and_preserves_full_value(self) -> None:
        """AC-001/AC-003: newline-separated literal with comma-in-value (data URI) must succeed and preserve the full value."""
        data_uri_value = "data:;base64,bG9jYWwtZGV2LW9pZGMtdG9rLWtleS0zMi1ieXRlcyE="
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS": f"NUXT_OIDC_TOKEN_KEY={data_uri_value}",
            }
        )

        result = run_make("auth-reconcile-eso-runtime-secrets", env)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        self.assertTrue(state_path.exists())
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=success", state)
        self.assertIn("source_secret_seed_mode=manifest-rendered", state)

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
        self.assertIn("NUXT_OIDC_TOKEN_KEY", rendered_secret)
        expected_b64 = base64.b64encode(data_uri_value.encode()).decode()
        self.assertIn(
            expected_b64,
            rendered_secret,
            msg="full comma-containing value must be preserved verbatim and appear base64-encoded in the rendered secret",
        )

    def test_comma_separated_input_is_rejected_with_log_warn(self) -> None:
        """AC-002: comma-separated input must be rejected with non-zero exit and a log_warn diagnostic."""
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "RUNTIME_CREDENTIALS_REQUIRED": "true",
                "RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS": "username=dev-user,password=dev-password",
            }
        )

        result = run_make("auth-reconcile-eso-runtime-secrets", env)
        self.assertNotEqual(result.returncode, 0, msg="comma-separated input must be rejected (non-zero exit)")

        combined_output = result.stdout + result.stderr
        self.assertIn(
            "WARN",
            combined_output,
            msg="a log_warn diagnostic must be visible when comma-separated input is rejected",
        )

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        self.assertTrue(state_path.exists())
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=failed-required", state)

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

    def test_local_lite_postgres_runtime_contract_is_skipped_when_runtime_state_exists(self) -> None:
        env = module_flags_env(profile="local-lite", postgres="true")
        postgres_runtime_state = REPO_ROOT / "artifacts" / "infra" / "postgres_runtime.env"
        postgres_runtime_state.parent.mkdir(parents=True, exist_ok=True)
        postgres_runtime_state.write_text(
            "\n".join(
                [
                    "profile=local-lite",
                    "stack=local",
                    "tooling_mode=execute",
                    "dsn=postgresql://platform:platform-password@blueprint-postgres.data.svc.cluster.local:5432/platform",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = run_make("auth-reconcile-eso-runtime-secrets", env)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        combined_output = result.stdout + result.stderr
        self.assertIn(
            "runtime credentials contract check skipped contract_id=postgres-runtime-credentials",
            combined_output,
        )

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        self.assertTrue(state_path.exists(), msg="runtime credentials state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=success", state)
        self.assertIn("skipped_contract_count=1", state)
        self.assertIn(
            "skipped_contracts=data/postgres-runtime-credentials:local-lite-postgres-runtime",
            state,
        )

    def test_local_lite_postgres_runtime_contract_skip_requires_owned_local_state(self) -> None:
        env = module_flags_env(profile="local-lite", postgres="true")
        postgres_runtime_state = REPO_ROOT / "artifacts" / "infra" / "postgres_runtime.env"
        postgres_runtime_state.parent.mkdir(parents=True, exist_ok=True)
        postgres_runtime_state.write_text(
            "\n".join(
                [
                    "profile=stackit-dev",
                    "stack=stackit",
                    "tooling_mode=execute",
                    "dsn=postgresql://platform:platform-password@blueprint-postgres.data.svc.cluster.local:5432/platform",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = run_make("auth-reconcile-eso-runtime-secrets", env)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        combined_output = result.stdout + result.stderr
        self.assertNotIn(
            "runtime credentials contract check skipped contract_id=postgres-runtime-credentials",
            combined_output,
        )

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        self.assertTrue(state_path.exists(), msg="runtime credentials state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("skipped_contract_count=0", state)
        self.assertIn("skipped_contracts=none", state)

    def test_required_mode_does_not_false_flag_hyphenated_target_keys_as_missing(self) -> None:
        env = module_flags_env(profile="local-full")
        env.update(
            {
                "DRY_RUN": "false",
                "RUNTIME_CREDENTIALS_REQUIRED": "true",
                "RUNTIME_CREDENTIALS_SOURCE_SECRET_LITERALS": "username=dev-user\npassword=dev-password",
            }
        )

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
                        "RUNTIME_CREDENTIALS_ESO_WAIT_TIMEOUT\t15",
                        "RUNTIME_CREDENTIALS_REQUIRED\tfalse",
                        "EOF",
                        "      exit 0",
                        "      ;;",
                        "    eso-contracts)",
                        "      cat <<'EOF'",
                        "iap-runtime-credentials\t\tsecurity\tiap-runtime-credentials\tiap-runtime-credentials\tclient-id,client-secret",
                        "EOF",
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

            kubectl_shim = shim_dir / "kubectl"
            kubectl_shim.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'if [[ "${1:-}" == "--context=docker-desktop" && "${2:-}" == "config" && "${3:-}" == "view" && "${4:-}" == "--raw" && "${5:-}" == "--minify" && "${6:-}" == "--flatten" ]]; then',
                        "  cat <<'EOF'",
                        "apiVersion: v1",
                        "kind: Config",
                        "clusters:",
                        "- cluster:",
                        "    server: https://docker-desktop.example:6443",
                        "  name: docker-desktop",
                        "contexts:",
                        "- context:",
                        "    cluster: docker-desktop",
                        "    user: docker-desktop",
                        "  name: docker-desktop",
                        "current-context: docker-desktop",
                        "users:",
                        "- name: docker-desktop",
                        "  user:",
                        "    token: placeholder",
                        "EOF",
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "config" && "${2:-}" == "get-contexts" && "${3:-}" == "-o" && "${4:-}" == "name" ]]; then',
                        "  printf 'docker-desktop\\n'",
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "config" && "${2:-}" == "current-context" ]]; then',
                        "  printf 'docker-desktop\\n'",
                        "  exit 0",
                        "fi",
                        'while [[ "$#" -gt 0 ]]; do',
                        '  case "$1" in',
                        "    --kubeconfig|--context)",
                        "      shift 2",
                        "      continue",
                        "      ;;",
                        "    --kubeconfig=*|--context=*)",
                        "      shift",
                        "      continue",
                        "      ;;",
                        "  esac",
                        "  break",
                        "done",
                        'if [[ "${1:-}" == "apply" && "${2:-}" == "-k" ]]; then',
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "apply" && "${2:-}" == "-f" ]]; then',
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "get" && "${2:-}" == "crd/clustersecretstores.external-secrets.io" ]]; then',
                        "  printf 'Established=True\\n'",
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "get" && "${2:-}" == "crd/externalsecrets.external-secrets.io" ]]; then',
                        "  printf 'Established=True\\n'",
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "-n" && "${2:-}" == "security" && "${3:-}" == "get" && "${4:-}" == "externalsecret" && "${5:-}" == "iap-runtime-credentials" && "${6:-}" == "-o" ]]; then',
                        "  printf 'Ready=True\\n'",
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "-n" && "${2:-}" == "security" && "${3:-}" == "get" && "${4:-}" == "externalsecret" && "${5:-}" == "iap-runtime-credentials" ]]; then',
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "-n" && "${2:-}" == "security" && "${3:-}" == "get" && "${4:-}" == "secret" && "${5:-}" == "iap-runtime-credentials" && "${6:-}" == "-o" && "${7:-}" == "json" ]]; then',
                        "  cat <<'EOF'",
                        '{"apiVersion":"v1","kind":"Secret","metadata":{"name":"iap-runtime-credentials","namespace":"security"},"data":{"client-id":"Y2xpZW50LWlk","client-secret":"Y2xpZW50LXNlY3JldA=="}}',
                        "EOF",
                        "  exit 0",
                        "fi",
                        'if [[ "${1:-}" == "-n" && "${2:-}" == "security" && "${3:-}" == "get" && "${4:-}" == "secret" && "${5:-}" == "iap-runtime-credentials" && "${6:-}" == "-o" ]]; then',
                        "  printf 'simulated jsonpath parser mismatch\\n' >&2",
                        "  exit 1",
                        "fi",
                        'if [[ "${1:-}" == "-n" && "${2:-}" == "security" && "${3:-}" == "get" && "${4:-}" == "secret" && "${5:-}" == "iap-runtime-credentials" ]]; then',
                        "  exit 0",
                        "fi",
                        'printf "unexpected kubectl call: %s\\n" "$*" >&2',
                        "exit 1",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            kubectl_shim.chmod(0o755)

            env["PATH"] = f"{shim_dir}:{os.environ.get('PATH', '')}"
            result = run_make("auth-reconcile-eso-runtime-secrets", env)

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        combined_output = result.stdout + result.stderr
        self.assertNotIn("missing key(s)", combined_output)
        self.assertNotIn("verification error", combined_output)

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_reconcile.env"
        self.assertTrue(state_path.exists(), msg="runtime credentials state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=success", state)
        self.assertIn("target_secret_status=ready", state)
        self.assertIn("target_secret_missing_keys=none", state)
        self.assertIn("target_secret_checked=security/iap-runtime-credentials", state)
        self.assertIn("target_secret_diagnostics_count=1", state)
        self.assertIn(
            f"target_secret_diagnostics_report={REPO_ROOT}/artifacts/infra/runtime_credentials_eso_target_secret_checks.json",
            state,
        )

        diagnostics_path = REPO_ROOT / "artifacts" / "infra" / "runtime_credentials_eso_target_secret_checks.json"
        self.assertTrue(diagnostics_path.exists(), msg="target secret diagnostics report was not created")
        diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
        self.assertEqual(diagnostics.get("kind"), "runtime-target-secret-contract-check-report")
        self.assertEqual(diagnostics.get("schemaVersion"), "v1")
        counts = diagnostics.get("counts", {})
        self.assertEqual(counts.get("total"), 1)
        self.assertEqual(counts.get("ready"), 1)
        checks = diagnostics.get("checks", [])
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].get("status"), "ready")
        self.assertEqual(checks[0].get("namespace"), "security")
        self.assertEqual(checks[0].get("secretName"), "iap-runtime-credentials")
        self.assertEqual(checks[0].get("requiredKeys"), ["client-id", "client-secret"])

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

    def test_runtime_identity_doctor_writes_consolidated_diagnostics_state(self) -> None:
        env = module_flags_env(profile="local-full")
        env.update({"ARGOCD_REPO_TOKEN": "ghp_exampletoken"})

        result = run_make("auth-runtime-identity-doctor", env)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

        state_path = REPO_ROOT / "artifacts" / "infra" / "runtime_identity_doctor.env"
        self.assertTrue(state_path.exists(), msg="runtime identity doctor state artifact was not created")
        state = state_path.read_text(encoding="utf-8")
        self.assertIn("status=success", state)
        self.assertIn("refresh_status=success", state)
        self.assertIn("runtime_identity_state=", state)
        self.assertIn("runtime_credentials_state=", state)
        self.assertIn("argocd_repo_state=", state)
        self.assertIn("contract_eso_expected_count=", state)
        self.assertIn("contract_keycloak_enabled_count=", state)

        state_json_path = REPO_ROOT / "artifacts" / "infra" / "runtime_identity_doctor.json"
        self.assertTrue(state_json_path.exists(), msg="runtime identity doctor JSON state artifact was not created")
        state_json = json.loads(state_json_path.read_text(encoding="utf-8"))
        self.assertEqual(state_json.get("artifact", {}).get("name"), "runtime_identity_doctor")
        self.assertEqual(state_json.get("entries", {}).get("status"), "success")

        report_path = REPO_ROOT / "artifacts" / "infra" / "runtime_identity_doctor_report.json"
        self.assertTrue(report_path.exists(), msg="runtime identity doctor report was not created")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report.get("kind"), "runtime-identity-doctor-report")
        self.assertEqual(report.get("schemaVersion"), "v1")
        self.assertEqual(report.get("summary", {}).get("status"), "success")
        self.assertEqual(report.get("summary", {}).get("issueCount"), 0)
        self.assertEqual(report.get("execution", {}).get("refreshStatus"), "success")
        self.assertEqual(report.get("artifacts", {}).get("runtimeIdentityReconcile", {}).get("present"), True)
        self.assertEqual(report.get("contract", {}).get("keycloak", {}).get("enabledRealmCount"), 0)
        self.assertEqual(report.get("contract", {}).get("keycloak", {}).get("enabledRealms"), [])


if __name__ == "__main__":
    unittest.main()
