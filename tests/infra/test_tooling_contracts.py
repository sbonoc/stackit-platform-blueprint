from __future__ import annotations

import json
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

    def test_stackit_layer_var_args_normalize_provider_backed_module_inputs(self) -> None:
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/stack_paths.sh"
source "{REPO_ROOT}/scripts/lib/infra/stackit_layers.sh"
stackit_layer_var_args foundation
"""
        result = run(
            ["bash", "-lc", script],
            {
                "BLUEPRINT_PROFILE": "stackit-dev",
                "POSTGRES_ENABLED": "true",
                "OBJECT_STORAGE_ENABLED": "true",
                "DNS_ENABLED": "true",
                "SECRETS_MANAGER_ENABLED": "true",
                "POSTGRES_INSTANCE_NAME": "bp-postgres-stackit",
                "POSTGRES_DB_NAME": "platform",
                "POSTGRES_USER": "platform",
                "POSTGRES_EXTRA_ALLOWED_CIDRS": "10.0.0.0/24, 10.0.1.0/24",
                "OBJECT_STORAGE_BUCKET_NAME": "bp-assets-stackit",
                "DNS_ZONE_NAME": "marketplace-stackit",
                "DNS_ZONE_FQDN": "marketplace-stackit.example.",
                "SECRETS_MANAGER_INSTANCE_NAME": "bp-secrets-stackit",
            },
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("-var=postgres_instance_name=bp-postgres-stackit", result.stdout)
        self.assertIn("-var=postgres_db_name=platform", result.stdout)
        self.assertIn("-var=postgres_username=platform", result.stdout)
        self.assertIn('-var=postgres_acl=["10.0.0.0/24", "10.0.1.0/24"]', result.stdout)
        self.assertIn("-var=object_storage_bucket_name=bp-assets-stackit", result.stdout)
        self.assertIn('-var=dns_zone_fqdns=["marketplace-stackit.example."]', result.stdout)
        self.assertIn("-var=secrets_manager_instance_name=bp-secrets-stackit", result.stdout)

    def test_stackit_provider_backed_helpers_prefer_foundation_outputs(self) -> None:
        payload = json.dumps(
            {
                "postgres_host": {"value": "managed-postgres.eu01.onstackit.cloud"},
                "postgres_port": {"value": 15432},
                "postgres_username": {"value": "managed-user"},
                "postgres_password": {"value": "managed-password"},
                "postgres_database": {"value": "managed-db"},
                "object_storage_bucket_name": {"value": "managed-assets"},
                "object_storage_access_key": {"value": "managed-access"},
                "object_storage_secret_access_key": {"value": "managed-secret"},
                "dns_zone_ids": {"value": {"marketplace-stackit.example.": "zone-12345"}},
            }
        )
        script = f"""
export ROOT_DIR="{REPO_ROOT}"
source "{REPO_ROOT}/scripts/lib/shell/bootstrap.sh"
source "{REPO_ROOT}/scripts/lib/infra/profile.sh"
source "{REPO_ROOT}/scripts/lib/infra/postgres.sh"
source "{REPO_ROOT}/scripts/lib/infra/object_storage.sh"
source "{REPO_ROOT}/scripts/lib/infra/dns.sh"
printf 'postgres_host=%s\\n' "$(postgres_host)"
printf 'postgres_port=%s\\n' "$(postgres_port)"
printf 'postgres_user=%s\\n' "$(postgres_username)"
printf 'postgres_password=%s\\n' "$(postgres_password)"
printf 'postgres_db=%s\\n' "$(postgres_database)"
printf 'object_storage_bucket=%s\\n' "$(object_storage_bucket_name)"
printf 'object_storage_access=%s\\n' "$(object_storage_access_key)"
printf 'object_storage_secret=%s\\n' "$(object_storage_secret_key)"
printf 'dns_zone_id=%s\\n' "$(dns_zone_id)"
printf 'dsn=%s\\n' "$(postgres_dsn)"
"""
        result = run(
            ["bash", "-lc", script],
            {
                "BLUEPRINT_PROFILE": "stackit-dev",
                "STACKIT_REGION": "eu01",
                "POSTGRES_INSTANCE_NAME": "placeholder-postgres",
                "POSTGRES_DB_NAME": "placeholder-db",
                "POSTGRES_USER": "placeholder-user",
                "POSTGRES_PASSWORD": "placeholder-password",
                "POSTGRES_PORT": "5432",
                "OBJECT_STORAGE_BUCKET_NAME": "placeholder-assets",
                "OBJECT_STORAGE_ACCESS_KEY": "placeholder-access",
                "OBJECT_STORAGE_SECRET_KEY": "placeholder-secret",
                "DNS_ZONE_NAME": "placeholder-zone",
                "DNS_ZONE_FQDN": "marketplace-stackit.example.",
                "STACKIT_FOUNDATION_OUTPUTS_LOADED": "true",
                "STACKIT_FOUNDATION_OUTPUTS_JSON": payload,
            },
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("postgres_host=managed-postgres.eu01.onstackit.cloud", result.stdout)
        self.assertIn("postgres_port=15432", result.stdout)
        self.assertIn("postgres_user=managed-user", result.stdout)
        self.assertIn("postgres_password=managed-password", result.stdout)
        self.assertIn("postgres_db=managed-db", result.stdout)
        self.assertIn("object_storage_bucket=managed-assets", result.stdout)
        self.assertIn("object_storage_access=managed-access", result.stdout)
        self.assertIn("object_storage_secret=managed-secret", result.stdout)
        self.assertIn("dns_zone_id=zone-12345", result.stdout)
        self.assertIn(
            "dsn=postgresql://managed-user:managed-password@managed-postgres.eu01.onstackit.cloud:15432/managed-db",
            result.stdout,
        )

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
