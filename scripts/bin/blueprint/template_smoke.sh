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
  APP_CATALOG_SCAFFOLD_ENABLED        Opt-in app catalog scaffold contract
  APP_RUNTIME_GITOPS_ENABLED          App runtime GitOps scaffold contract (enabled by default)
  APP_RUNTIME_MIN_WORKLOADS           Execute-mode minimum expected app runtime workloads (default: 1)
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
set_default_env APP_CATALOG_SCAFFOLD_ENABLED "false"
set_default_env APP_RUNTIME_GITOPS_ENABLED "true"
set_default_env APP_RUNTIME_MIN_WORKLOADS "1"

source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
# Ignore untouched template placeholder identity values from source-repo
# defaults so smoke scenarios operate on deterministic non-placeholder inputs.
blueprint_sanitize_init_placeholder_defaults

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
  set_default_env RABBITMQ_INSTANCE_NAME "bp-rabbitmq"
  set_default_env KMS_KEY_RING_NAME "bp-ring"
  set_default_env KMS_KEY_NAME "bp-key"

  set_default_env NEO4J_AUTH_USERNAME "neo4j"
  set_default_env NEO4J_AUTH_PASSWORD "neo4j-password"

  set_default_env KEYCLOAK_ISSUER_URL "https://keycloak.${BLUEPRINT_GITHUB_REPO}.example.com/realms/platform"
  set_default_env KEYCLOAK_CLIENT_ID "blueprint-client"
  set_default_env KEYCLOAK_CLIENT_SECRET "blueprint-client-secret"
  set_default_env IAP_COOKIE_SECRET "0123456789abcdef0123456789abcdef"
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

run_template_smoke_reset_generated_make_surface() {
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
    make blueprint-render-makefile
}

assert_template_smoke_repo_state() {
  local repo_root="$1"
  python3 "$ROOT_DIR/scripts/lib/blueprint/template_smoke_assertions.py" "$repo_root"
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
  # Generated repos must start from the baseline no-optional-modules Make
  # surface, even if the source workspace currently has an enabled-module
  # generated file from a previous local validation run.
  run_cmd run_template_smoke_reset_generated_make_surface
  run_cmd run_template_smoke_init_repo
  run_cmd make blueprint-bootstrap
  run_cmd make infra-bootstrap
  run_cmd make infra-validate
  run_cmd env BLUEPRINT_CODEX_SKILLS_DIR="$tmp_root/codex-skills" make blueprint-install-codex-skill
  run_cmd test -f "$tmp_root/codex-skills/blueprint-consumer-upgrade/SKILL.md"
  run_cmd test -x "$tmp_root/codex-skills/blueprint-consumer-upgrade/scripts/resolve_latest_stable_ref.sh"
  run_cmd make blueprint-check-placeholders

  # Validate the full generated-repo operator chain so scenario coverage checks
  # the same provision/deploy/smoke/status artifacts consumers rely on.
  run_cmd make infra-provision-deploy
  run_cmd make infra-status-json

  assert_template_smoke_repo_state "$tmp_repo"
)

log_info "template smoke completed successfully scenario=$BLUEPRINT_TEMPLATE_SMOKE_SCENARIO profile=$BLUEPRINT_PROFILE"
