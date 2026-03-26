#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_stackit_runtime_inventory"

usage() {
  cat <<'USAGE'
Usage: stackit_runtime_inventory.sh

Prints STACKIT runtime inventory derived from contract + state artifacts.
Outputs export-ready environment hints with sensitive values redacted by default.

Environment variables:
  STACKIT_RUNTIME_INVENTORY_INCLUDE_SENSITIVE  true|false (default: false)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-runtime-inventory requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

if tooling_is_execution_enabled; then
  require_env_vars STACKIT_PROJECT_ID STACKIT_REGION
else
  set_default_env STACKIT_PROJECT_ID "project-placeholder"
  set_default_env STACKIT_REGION "eu01"
fi
set_default_env STACKIT_FOUNDATION_KUBECONFIG_OUTPUT "${HOME}/.kube/stackit-${BLUEPRINT_PROFILE}.yaml"
set_default_env STACKIT_RUNTIME_INVENTORY_INCLUDE_SENSITIVE "false"
set_default_env STACKIT_WORKFLOWS_API_BASE_URL "https://workflows.api.stackit.cloud/v1alpha"
set_default_env STACKIT_WORKFLOWS_API_TOKEN "${STACKIT_WORKFLOWS_ACCESS_TOKEN:-}"

kubeconfig_output="$STACKIT_FOUNDATION_KUBECONFIG_OUTPUT"
if [[ "$kubeconfig_output" != /* ]]; then
  kubeconfig_output="$ROOT_DIR/$kubeconfig_output"
fi

inventory_include_sensitive="$STACKIT_RUNTIME_INVENTORY_INCLUDE_SENSITIVE"
case "$inventory_include_sensitive" in
1 | true | TRUE | True | yes | YES | on | ON)
  inventory_include_sensitive="true"
  ;;
*)
  inventory_include_sensitive="false"
  ;;
esac

print_section_header() {
  local title="$1"
  printf '\n=== %s ===\n' "$title"
}

print_export_or_missing() {
  local key="$1"
  local value="$2"
  local sensitive="${3:-false}"
  if [[ -z "$value" ]]; then
    printf '# %s=<missing>\n' "$key"
    return 0
  fi
  if [[ "$sensitive" == "true" && "$inventory_include_sensitive" != "true" ]]; then
    printf '# %s=<redacted>\n' "$key"
    return 0
  fi
  printf 'export %s=%q\n' "$key" "$value"
}

state_read_value() {
  local state_prefix="$1"
  local key="$2"
  if ! state_file_exists "$state_prefix"; then
    return 0
  fi
  grep -E "^${key}=" "$(state_file_path "$state_prefix")" | head -n1 | cut -d= -f2- || true
}

foundation_smoke_status="missing"
if state_file_exists stackit_smoke_foundation; then
  foundation_smoke_status="passed"
fi

runtime_deploy_status="missing"
if state_file_exists stackit_runtime_deploy; then
  runtime_deploy_status="deployed"
fi

runtime_smoke_status="missing"
if state_file_exists stackit_smoke_runtime; then
  runtime_smoke_status="passed"
fi

overlay_path="$(argocd_overlay_dir)"
terraform_env_dir="$(stackit_terraform_env_dir)"
workflows_instance_id="$(state_read_value workflows_instance instance_id)"
workflows_web_url="$(state_read_value workflows_instance web_url)"
workflows_health_status="$(state_read_value workflows_instance health_status)"

print_section_header "STACKIT Runtime Inventory Exports"
print_export_or_missing "BLUEPRINT_PROFILE" "$BLUEPRINT_PROFILE"
print_export_or_missing "STACKIT_PROJECT_ID" "$STACKIT_PROJECT_ID"
print_export_or_missing "STACKIT_REGION" "$STACKIT_REGION"
print_export_or_missing "STACKIT_FOUNDATION_KUBECONFIG_OUTPUT" "$kubeconfig_output"
print_export_or_missing "STACKIT_TERRAFORM_ENV_DIR" "$terraform_env_dir"
print_export_or_missing "STACKIT_ARGOCD_OVERLAY_PATH" "$overlay_path"
print_export_or_missing "STACKIT_FOUNDATION_SMOKE_STATUS" "$foundation_smoke_status"
print_export_or_missing "STACKIT_RUNTIME_DEPLOY_STATUS" "$runtime_deploy_status"
print_export_or_missing "STACKIT_RUNTIME_SMOKE_STATUS" "$runtime_smoke_status"
print_export_or_missing "STACKIT_ENABLED_MODULES" "$(enabled_modules_csv)"
print_export_or_missing "STACKIT_WORKFLOWS_API_BASE_URL" "$STACKIT_WORKFLOWS_API_BASE_URL"
print_export_or_missing "STACKIT_WORKFLOWS_API_TOKEN" "${STACKIT_WORKFLOWS_API_TOKEN:-}" "true"
print_export_or_missing "STACKIT_WORKFLOWS_INSTANCE_ID" "$workflows_instance_id"
print_export_or_missing "STACKIT_WORKFLOWS_WEB_URL" "$workflows_web_url"
print_export_or_missing "STACKIT_WORKFLOWS_HEALTH_STATUS" "$workflows_health_status"

if [[ "$inventory_include_sensitive" != "true" ]]; then
  log_info "sensitive exports are redacted by default; set STACKIT_RUNTIME_INVENTORY_INCLUDE_SENSITIVE=true to print them"
fi

state_file="$(
  write_state_file "stackit_runtime_inventory" \
    "profile=$BLUEPRINT_PROFILE" \
    "environment=$(profile_environment)" \
    "project_id=$STACKIT_PROJECT_ID" \
    "region=$STACKIT_REGION" \
    "terraform_env_dir=$terraform_env_dir" \
    "argocd_overlay_path=$overlay_path" \
    "kubeconfig_output=$kubeconfig_output" \
    "foundation_smoke_status=$foundation_smoke_status" \
    "runtime_deploy_status=$runtime_deploy_status" \
    "runtime_smoke_status=$runtime_smoke_status" \
    "enabled_modules=$(enabled_modules_csv)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "STACKIT runtime inventory profile=$BLUEPRINT_PROFILE env=$(profile_environment) project=$STACKIT_PROJECT_ID region=$STACKIT_REGION"
log_info "STACKIT runtime inventory kubeconfig=$kubeconfig_output overlay=$overlay_path"
log_info "stackit runtime inventory state written to $state_file"
