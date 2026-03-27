#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"

start_script_metric_trap "blueprint_template_smoke"

usage() {
  cat <<'EOF'
Usage: template_smoke.sh

Runs a generated-repository conformance smoke in a temporary copy.

Environment variables:
  BLUEPRINT_TEMPLATE_SMOKE_SCENARIO   Scenario label for CI/logging (default: default)
  BLUEPRINT_PROFILE                   Generated-repo profile to validate
  OBSERVABILITY_ENABLED               Canonical observability flag
  WORKFLOWS_ENABLED                   Optional module flag
  LANGFUSE_ENABLED                    Optional module flag
  POSTGRES_ENABLED                    Optional module flag
  NEO4J_ENABLED                       Optional module flag
  OBJECT_STORAGE_ENABLED              Optional module flag
  RABBITMQ_ENABLED                    Optional module flag
  DNS_ENABLED                         Optional module flag
  PUBLIC_ENDPOINTS_ENABLED            Optional module flag
  SECRETS_MANAGER_ENABLED             Optional module flag
  KMS_ENABLED                         Optional module flag
  IDENTITY_AWARE_PROXY_ENABLED        Optional module flag
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command tar
require_command make
require_command python3
require_command git

set_default_env BLUEPRINT_TEMPLATE_SMOKE_SCENARIO "default"
set_default_env BLUEPRINT_PROFILE "local-full"
set_default_env DRY_RUN "true"
set_default_env OBSERVABILITY_ENABLED "false"
set_default_env WORKFLOWS_ENABLED "false"
set_default_env LANGFUSE_ENABLED "false"
set_default_env POSTGRES_ENABLED "false"
set_default_env NEO4J_ENABLED "false"
set_default_env OBJECT_STORAGE_ENABLED "false"
set_default_env RABBITMQ_ENABLED "false"
set_default_env DNS_ENABLED "false"
set_default_env PUBLIC_ENDPOINTS_ENABLED "false"
set_default_env SECRETS_MANAGER_ENABLED "false"
set_default_env KMS_ENABLED "false"
set_default_env IDENTITY_AWARE_PROXY_ENABLED "false"

source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

set_default_env BLUEPRINT_REPO_NAME "acme-platform-blueprint"
set_default_env BLUEPRINT_GITHUB_ORG "acme-platform"
set_default_env BLUEPRINT_GITHUB_REPO "acme-platform-blueprint"
set_default_env BLUEPRINT_DEFAULT_BRANCH "main"
set_default_env BLUEPRINT_DOCS_TITLE "Acme Platform Blueprint"
set_default_env BLUEPRINT_DOCS_TAGLINE "Reusable local+STACKIT platform blueprint"
set_default_env BLUEPRINT_STACKIT_REGION "eu01"
set_default_env BLUEPRINT_STACKIT_TENANT_SLUG "acme"
set_default_env BLUEPRINT_STACKIT_PLATFORM_SLUG "platform"
set_default_env BLUEPRINT_STACKIT_PROJECT_ID "acme-platform"
set_default_env BLUEPRINT_STACKIT_TFSTATE_BUCKET "acme-platform-tf-state"
set_default_env BLUEPRINT_STACKIT_TFSTATE_KEY_PREFIX "terraform/state"

template_smoke_enabled_module_count() {
  local enabled_modules
  enabled_modules="$(enabled_modules_csv)"
  if [[ -z "$enabled_modules" ]]; then
    echo "0"
    return 0
  fi

  local modules=()
  IFS=',' read -r -a modules <<<"$enabled_modules"
  echo "${#modules[@]}"
}

seed_template_smoke_contract_env() {
  set_default_env STACKIT_PROJECT_ID "$BLUEPRINT_STACKIT_PROJECT_ID"
  set_default_env STACKIT_REGION "$BLUEPRINT_STACKIT_REGION"
  set_default_env STACKIT_TFSTATE_BUCKET "$BLUEPRINT_STACKIT_TFSTATE_BUCKET"

  set_default_env POSTGRES_INSTANCE_NAME "bp-postgres"
  set_default_env POSTGRES_DB_NAME "platform"
  set_default_env POSTGRES_USER "platform"
  set_default_env POSTGRES_PASSWORD "platform-password"

  set_default_env NEO4J_AUTH_USERNAME "neo4j"
  set_default_env NEO4J_AUTH_PASSWORD "neo4j-password"

  set_default_env KEYCLOAK_ISSUER_URL "https://keycloak.${BLUEPRINT_GITHUB_REPO}.example.com/realms/platform"
  set_default_env KEYCLOAK_CLIENT_ID "blueprint-client"
  set_default_env KEYCLOAK_CLIENT_SECRET "blueprint-client-secret"
  set_default_env IAP_UPSTREAM_URL "http://catalog.apps.svc.cluster.local:8080"
  set_default_env IAP_PUBLIC_HOST "iap.${BLUEPRINT_GITHUB_REPO}.example.com"

  set_default_env LANGFUSE_PUBLIC_DOMAIN "langfuse.${BLUEPRINT_GITHUB_REPO}.example.com"
  set_default_env LANGFUSE_OIDC_ISSUER_URL "$KEYCLOAK_ISSUER_URL"
  set_default_env LANGFUSE_OIDC_CLIENT_ID "langfuse-client"
  set_default_env LANGFUSE_OIDC_CLIENT_SECRET "langfuse-client-secret"
  set_default_env LANGFUSE_DATABASE_URL "postgresql://langfuse:langfuse-password@postgres.internal:5432/langfuse"
  set_default_env LANGFUSE_SALT "langfuse-salt-0123456789"
  set_default_env LANGFUSE_ENCRYPTION_KEY "langfuse-encryption-key-0123456789"
  set_default_env LANGFUSE_NEXTAUTH_SECRET "langfuse-nextauth-secret"

  set_default_env STACKIT_OBSERVABILITY_INSTANCE_ID "obs-template-smoke"
  set_default_env STACKIT_WORKFLOWS_DAGS_REPO_URL "https://github.com/${BLUEPRINT_GITHUB_ORG}/${BLUEPRINT_GITHUB_REPO}.git"
  set_default_env STACKIT_WORKFLOWS_DAGS_REPO_BRANCH "$BLUEPRINT_DEFAULT_BRANCH"
  set_default_env STACKIT_WORKFLOWS_DAGS_REPO_USERNAME "template-smoke"
  set_default_env STACKIT_WORKFLOWS_DAGS_REPO_TOKEN "template-smoke-token"
  set_default_env STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL "${KEYCLOAK_ISSUER_URL}/.well-known/openid-configuration"
  set_default_env STACKIT_WORKFLOWS_OIDC_CLIENT_ID "workflows-client"
  set_default_env STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET "workflows-client-secret"
}

run_template_smoke_init_repo() {
  env \
    OBSERVABILITY_ENABLED=false \
    WORKFLOWS_ENABLED=false \
    LANGFUSE_ENABLED=false \
    POSTGRES_ENABLED=false \
    NEO4J_ENABLED=false \
    OBJECT_STORAGE_ENABLED=false \
    RABBITMQ_ENABLED=false \
    DNS_ENABLED=false \
    PUBLIC_ENDPOINTS_ENABLED=false \
    SECRETS_MANAGER_ENABLED=false \
    KMS_ENABLED=false \
    IDENTITY_AWARE_PROXY_ENABLED=false \
    make blueprint-init-repo
}

assert_template_smoke_repo_state() {
  local repo_root="$1"
  python3 - "$repo_root" <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys

repo_root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo_root))

from scripts.lib.blueprint.contract_schema import load_blueprint_contract


def normalize_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def profile_environment(profile: str) -> tuple[str, str]:
    if profile.startswith("local-"):
        return "local", "local"
    if profile.startswith("stackit-"):
        return "stackit", profile.split("-", 1)[1]
    raise AssertionError(f"unsupported BLUEPRINT_PROFILE={profile}")


def assert_path_exists(repo_root: Path, relative_path: str, scenario: str) -> None:
    path = repo_root / relative_path
    if not path.exists():
        raise AssertionError(f"{scenario}: expected path to exist: {relative_path}")


def assert_path_missing(repo_root: Path, relative_path: str, scenario: str) -> None:
    path = repo_root / relative_path
    if path.exists():
        raise AssertionError(f"{scenario}: expected path to be pruned: {relative_path}")


def assert_make_target_presence(makefile_text: str, target: str, expected: bool, scenario: str) -> None:
    pattern = re.compile(rf"^{re.escape(target)}:", re.MULTILINE)
    present = bool(pattern.search(makefile_text))
    if present != expected:
        state = "present" if expected else "absent"
        raise AssertionError(f"{scenario}: expected target to be {state}: {target}")


scenario = os.environ.get("BLUEPRINT_TEMPLATE_SMOKE_SCENARIO", "default")
profile = os.environ["BLUEPRINT_PROFILE"]
expected_stack, expected_environment = profile_environment(profile)
observability_enabled = normalize_bool(os.environ.get("OBSERVABILITY_ENABLED", "false"))

contract = load_blueprint_contract(repo_root / "blueprint/contract.yaml")
makefile_path = repo_root / contract.make_contract.ownership.blueprint_generated_file
makefile_text = makefile_path.read_text(encoding="utf-8")

expected_modules: list[str] = []
for module_name, module in sorted(contract.optional_modules.modules.items()):
    enabled = normalize_bool(os.environ.get(module.enable_flag, "false"))
    if enabled:
        expected_modules.append(module_name)

    for target in module.make_targets:
        assert_make_target_presence(makefile_text, target, enabled, scenario)

    for path_key in module.paths_required_when_enabled:
        raw_path = module.paths[path_key].replace("${ENV}", expected_environment)
        relative_path = raw_path.rstrip("/")
        if enabled:
            assert_path_exists(repo_root, relative_path, scenario)
        else:
            assert_path_missing(repo_root, relative_path, scenario)

required_artifacts = [
    "artifacts/infra/provision.env",
    "artifacts/infra/deploy.env",
    "artifacts/infra/smoke.env",
    "artifacts/infra/smoke_result.json",
    "artifacts/infra/smoke_diagnostics.json",
    "artifacts/infra/infra_status_snapshot.json",
    "artifacts/apps/apps_bootstrap.env",
    "artifacts/apps/apps_smoke.env",
]
for artifact in required_artifacts:
    assert_path_exists(repo_root, artifact, scenario)

if expected_stack == "local":
    assert_path_exists(repo_root, "artifacts/infra/local_crossplane_bootstrap.env", scenario)
else:
    for artifact in (
        "artifacts/infra/stackit_bootstrap_apply.env",
        "artifacts/infra/stackit_foundation_apply.env",
        "artifacts/infra/stackit_foundation_kubeconfig.env",
        "artifacts/infra/stackit_runtime_prerequisites.env",
        "artifacts/infra/stackit_foundation_runtime_secret.env",
    ):
        assert_path_exists(repo_root, artifact, scenario)

manifest_text = (repo_root / "apps/catalog/manifest.yaml").read_text(encoding="utf-8")
expected_manifest_line = "enabled: true" if observability_enabled else "enabled: false"
if expected_manifest_line not in manifest_text:
    raise AssertionError(
        f"{scenario}: apps/catalog/manifest.yaml drifted from OBSERVABILITY_ENABLED={observability_enabled}"
    )
if observability_enabled and "endpoint: http" not in manifest_text:
    raise AssertionError(f"{scenario}: observability-enabled app manifest is missing OTEL endpoint wiring")

smoke_result = json.loads((repo_root / "artifacts/infra/smoke_result.json").read_text(encoding="utf-8"))
if smoke_result.get("status") != "success":
    raise AssertionError(f"{scenario}: smoke result status is not success")
if smoke_result.get("profile") != profile:
    raise AssertionError(f"{scenario}: smoke result profile drifted from BLUEPRINT_PROFILE")
if smoke_result.get("stack") != expected_stack:
    raise AssertionError(f"{scenario}: smoke result stack drifted from BLUEPRINT_PROFILE")
if smoke_result.get("environment") != expected_environment:
    raise AssertionError(f"{scenario}: smoke result environment drifted from BLUEPRINT_PROFILE")
if bool(smoke_result.get("observabilityEnabled")) != observability_enabled:
    raise AssertionError(f"{scenario}: smoke result observability flag drifted from input")
if sorted(smoke_result.get("enabledModules", [])) != expected_modules:
    raise AssertionError(f"{scenario}: smoke result enabledModules drifted from input flags")

smoke_diagnostics = json.loads((repo_root / "artifacts/infra/smoke_diagnostics.json").read_text(encoding="utf-8"))
for artifact_name in ("provision", "deploy", "coreRuntimeSmoke", "appsSmoke"):
    if not smoke_diagnostics.get("artifacts", {}).get(artifact_name):
        raise AssertionError(f"{scenario}: smoke diagnostics missing artifact flag {artifact_name}=true")

status_snapshot = json.loads((repo_root / "artifacts/infra/infra_status_snapshot.json").read_text(encoding="utf-8"))
if status_snapshot.get("profile") != profile:
    raise AssertionError(f"{scenario}: infra status snapshot profile drifted from BLUEPRINT_PROFILE")
if status_snapshot.get("environment") != expected_environment:
    raise AssertionError(f"{scenario}: infra status snapshot environment drifted from BLUEPRINT_PROFILE")
if bool(status_snapshot.get("observabilityEnabled")) != observability_enabled:
    raise AssertionError(f"{scenario}: infra status snapshot observability flag drifted from input")
if sorted(status_snapshot.get("enabledModules", [])) != expected_modules:
    raise AssertionError(f"{scenario}: infra status snapshot enabledModules drifted from input flags")
if status_snapshot.get("latestSmoke", {}).get("status") != "success":
    raise AssertionError(f"{scenario}: infra status snapshot latestSmoke.status is not success")

status_artifacts = status_snapshot.get("artifacts", {})
for artifact_name in ("provision", "deploy", "smoke"):
    if not status_artifacts.get(artifact_name):
        raise AssertionError(f"{scenario}: infra status snapshot missing artifact flag {artifact_name}=true")
if expected_stack == "stackit":
    for artifact_name in ("stackitBootstrapApply", "stackitFoundationApply"):
        if not status_artifacts.get(artifact_name):
            raise AssertionError(f"{scenario}: expected STACKIT artifact flag {artifact_name}=true")
else:
    for artifact_name in ("stackitBootstrapApply", "stackitFoundationApply"):
        if status_artifacts.get(artifact_name):
            raise AssertionError(f"{scenario}: local profile should not report {artifact_name}=true")
PY
}

tmp_root="$(mktemp -d)"
tmp_repo="$tmp_root/repo"
cleanup() {
  rm -rf "$tmp_root"
}
trap cleanup EXIT

set_default_env STACKIT_FOUNDATION_KUBECONFIG_OUTPUT "$tmp_root/kubeconfig/stackit-${BLUEPRINT_PROFILE}.yaml"
seed_template_smoke_contract_env

enabled_modules="$(enabled_modules_csv)"
enabled_module_count="$(template_smoke_enabled_module_count)"
log_metric \
  "template_smoke_enabled_module_count" \
  "$enabled_module_count" \
  "scenario=$BLUEPRINT_TEMPLATE_SMOKE_SCENARIO profile=$BLUEPRINT_PROFILE stack=$(active_stack)"
log_info \
  "template smoke scenario=$BLUEPRINT_TEMPLATE_SMOKE_SCENARIO profile=$BLUEPRINT_PROFILE environment=$(profile_environment) tooling=$(tooling_execution_mode) enabled_modules=${enabled_modules:-none}"

mkdir -p "$tmp_repo"
(
  cd "$ROOT_DIR"
  tar \
    --exclude=".git" \
    --exclude=".pytest_cache" \
    --exclude="artifacts" \
    --exclude="docs/build" \
    --exclude="docs/.docusaurus" \
    --exclude="docs/node_modules" \
    --exclude="__pycache__" \
    -cf - .
) | (cd "$tmp_repo" && tar -xf -)

log_info "template smoke workspace: $tmp_repo"

(
  cd "$tmp_repo"
  git init -q
  run_cmd run_template_smoke_init_repo
  run_cmd make blueprint-bootstrap
  run_cmd make infra-bootstrap
  run_cmd make infra-validate
  run_cmd make blueprint-check-placeholders

  # Validate the full generated-repo operator chain so scenario coverage checks
  # the same provision/deploy/smoke/status artifacts consumers rely on.
  run_cmd make infra-provision-deploy
  run_cmd make infra-status-json

  assert_template_smoke_repo_state "$tmp_repo"
)

log_info "template smoke completed successfully scenario=$BLUEPRINT_TEMPLATE_SMOKE_SCENARIO profile=$BLUEPRINT_PROFILE"
