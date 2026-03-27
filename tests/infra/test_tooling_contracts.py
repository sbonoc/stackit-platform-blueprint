from __future__ import annotations

import unittest

from tests._shared.helpers import REPO_ROOT, run


def resolve_optional_module_execution(module: str, action: str, *, profile: str) -> str:
    script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/stack_paths.sh"
source "{REPO_ROOT}/scripts/lib/infra/module_execution.sh"
resolve_optional_module_execution "{module}" "{action}"
printf 'class=%s\\ndriver=%s\\npath=%s\\nnote=%s\\n' \
  "$OPTIONAL_MODULE_EXECUTION_CLASS" \
  "$OPTIONAL_MODULE_EXECUTION_DRIVER" \
  "$OPTIONAL_MODULE_EXECUTION_PATH" \
  "$OPTIONAL_MODULE_EXECUTION_NOTE"
"""
    result = run(["bash", "-lc", script], {"BLUEPRINT_PROFILE": profile})
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return result.stdout + result.stderr


class ToolingContractsTests(unittest.TestCase):
    def test_fallback_runtime_values_helper_keeps_stdout_machine_readable(self) -> None:
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/fallback_runtime.sh"
export RABBITMQ_HELM_RELEASE=blueprint-rabbitmq
export RABBITMQ_PASSWORD_SECRET_NAME=blueprint-rabbitmq-auth
render_optional_module_values_file \
  "rabbitmq" \
  "infra/local/helm/rabbitmq/values.yaml" \
  "RABBITMQ_HELM_RELEASE=$RABBITMQ_HELM_RELEASE" \
  "RABBITMQ_PASSWORD_SECRET_NAME=$RABBITMQ_PASSWORD_SECRET_NAME"
"""
        result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            f"{REPO_ROOT}/artifacts/infra/rendered/rabbitmq.values.yaml",
        )
        self.assertIn("optional_module_values_render_total", result.stderr)
        self.assertIn("rendered optional-module values artifact", result.stderr)

    def test_fallback_runtime_secret_helper_keeps_stdout_machine_readable(self) -> None:
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/fallback_runtime.sh"
render_optional_module_secret_manifests "messaging" "blueprint-rabbitmq-auth" "rabbitmq-password=secret"
"""
        result = run(["bash", "-lc", script], {"ROOT_DIR": str(REPO_ROOT)})
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            f"{REPO_ROOT}/artifacts/infra/rendered/secrets/secret-messaging-blueprint-rabbitmq-auth.yaml",
        )
        self.assertIn("optional_module_secret_render_total", result.stderr)

    def test_help_reference_includes_primary_workflows(self) -> None:
        result = run(["make", "infra-help-reference"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Primary Workflows", result.stdout)
        self.assertIn("make quality-hooks-run", result.stdout)
        self.assertIn("make blueprint-bootstrap", result.stdout)
        self.assertIn("make infra-bootstrap", result.stdout)
        self.assertIn("quality-docs-sync-core-targets", result.stdout)

    def test_prereqs_help_mentions_extended_optional_tooling(self) -> None:
        result = run(["scripts/bin/infra/prereqs.sh", "--help"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("terraform kubectl helm docker kind uv gh jq pnpm kustomize nc", result.stdout)

    def test_quality_test_pyramid_target_passes(self) -> None:
        result = run(["make", "quality-test-pyramid"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("[test-pyramid] OK", result.stdout)

    def test_optional_module_execution_resolves_provider_backed_stackit_modes(self) -> None:
        resolved = resolve_optional_module_execution("postgres", "plan", profile="stackit-dev")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=foundation_contract", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/cloud/stackit/terraform/foundation", resolved)

    def test_optional_module_execution_resolves_local_fallback_modes(self) -> None:
        resolved = resolve_optional_module_execution("rabbitmq", "plan", profile="local-full")
        self.assertIn("class=fallback_runtime", resolved)
        self.assertIn("driver=helm", resolved)
        self.assertIn(f"path={REPO_ROOT}/artifacts/infra/rendered/rabbitmq.values.yaml", resolved)

    def test_optional_module_execution_resolves_stackit_provider_backed_rabbitmq_modes(self) -> None:
        resolved = resolve_optional_module_execution("rabbitmq", "apply", profile="stackit-dev")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=foundation_contract", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/cloud/stackit/terraform/foundation", resolved)

    def test_optional_module_execution_resolves_stackit_chart_applications(self) -> None:
        resolved = resolve_optional_module_execution("public-endpoints", "apply", profile="stackit-dev")
        self.assertIn("class=fallback_runtime", resolved)
        self.assertIn("driver=argocd_application_chart", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/gitops/argocd/optional/dev/public-endpoints.yaml", resolved)

    def test_optional_module_execution_resolves_stackit_provider_backed_kms_modes(self) -> None:
        resolved = resolve_optional_module_execution("kms", "apply", profile="stackit-dev")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=foundation_contract", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/cloud/stackit/terraform/foundation", resolved)

    def test_optional_module_execution_resolves_local_noop_modes(self) -> None:
        resolved = resolve_optional_module_execution("dns", "destroy", profile="local-full")
        self.assertIn("class=provider_backed", resolved)
        self.assertIn("driver=noop", resolved)
        self.assertIn("destroy is a contract no-op", resolved)

    def test_optional_module_execution_resolves_manifest_fallback_across_profiles(self) -> None:
        resolved = resolve_optional_module_execution("langfuse", "destroy", profile="local-full")
        self.assertIn("class=fallback_runtime", resolved)
        self.assertIn("driver=argocd_optional_manifest", resolved)
        self.assertIn(f"path={REPO_ROOT}/infra/gitops/argocd/optional/local/langfuse.yaml", resolved)


if __name__ == "__main__":
    unittest.main()
