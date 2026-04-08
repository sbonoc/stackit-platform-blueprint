#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak.sh"

start_script_metric_trap "infra_local_runtime_inventory"

usage() {
  cat <<'USAGE'
Usage: local_runtime_inventory.sh

Prints local runtime inventory derived from contract + state artifacts.
Outputs export-ready environment hints with sensitive values redacted by default.

Environment variables:
  LOCAL_RUNTIME_INVENTORY_INCLUDE_SENSITIVE  true|false (default: false)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if is_stackit_profile; then
  log_fatal "infra-local-runtime-inventory requires local-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

set_default_env LOCAL_RUNTIME_INVENTORY_INCLUDE_SENSITIVE "false"
keycloak_seed_env_defaults

inventory_include_sensitive="$LOCAL_RUNTIME_INVENTORY_INCLUDE_SENSITIVE"
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

provision_status="missing"
if state_file_exists provision; then
  provision_status="present"
fi

deploy_status="missing"
if state_file_exists deploy; then
  deploy_status="present"
fi

smoke_status="missing"
if state_file_exists smoke; then
  smoke_status="passed"
fi

runtime_credentials_status="$(state_read_value runtime_credentials_eso_reconcile status)"
if [[ -z "$runtime_credentials_status" ]]; then
  runtime_credentials_status="missing"
fi

workflows_keycloak_status="$(state_read_value workflows_keycloak_reconcile status)"
if [[ -z "$workflows_keycloak_status" ]]; then
  workflows_keycloak_status="not-enabled-or-missing"
fi

langfuse_keycloak_status="$(state_read_value langfuse_keycloak_reconcile status)"
if [[ -z "$langfuse_keycloak_status" ]]; then
  langfuse_keycloak_status="not-enabled-or-missing"
fi

kubeconfig_path="$(active_kubeconfig_path)"
kube_context="$(active_kube_context_name)"
kube_access_source="$(active_kube_access_source)"
overlay_path="$(local_argocd_overlay_dir)"

print_section_header "Local Runtime Inventory Exports"
print_export_or_missing "BLUEPRINT_PROFILE" "$BLUEPRINT_PROFILE"
print_export_or_missing "LOCAL_KUBECONFIG_PATH" "$kubeconfig_path"
print_export_or_missing "LOCAL_KUBECONTEXT" "$kube_context"
print_export_or_missing "LOCAL_KUBE_ACCESS_SOURCE" "$kube_access_source"
print_export_or_missing "LOCAL_ARGOCD_OVERLAY_PATH" "$overlay_path"
print_export_or_missing "LOCAL_PROVISION_STATUS" "$provision_status"
print_export_or_missing "LOCAL_DEPLOY_STATUS" "$deploy_status"
print_export_or_missing "LOCAL_SMOKE_STATUS" "$smoke_status"
print_export_or_missing "LOCAL_RUNTIME_CREDENTIALS_STATUS" "$runtime_credentials_status"
print_export_or_missing "LOCAL_ENABLED_MODULES" "$(enabled_modules_csv)"
print_export_or_missing "KEYCLOAK_PUBLIC_HOST" "$KEYCLOAK_PUBLIC_HOST"
print_export_or_missing "KEYCLOAK_ISSUER_URL" "$KEYCLOAK_ISSUER_URL"
print_export_or_missing "KEYCLOAK_REALM_WORKFLOWS" "$KEYCLOAK_REALM_WORKFLOWS"
print_export_or_missing "KEYCLOAK_REALM_LANGFUSE" "$KEYCLOAK_REALM_LANGFUSE"
print_export_or_missing "WORKFLOWS_KEYCLOAK_RECONCILE_STATUS" "$workflows_keycloak_status"
print_export_or_missing "LANGFUSE_KEYCLOAK_RECONCILE_STATUS" "$langfuse_keycloak_status"
print_export_or_missing "KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED" "${KEYCLOAK_OPTIONAL_MODULE_RECONCILIATION_ENABLED:-true}"

if [[ "$inventory_include_sensitive" != "true" ]]; then
  log_info "sensitive exports are redacted by default; set LOCAL_RUNTIME_INVENTORY_INCLUDE_SENSITIVE=true to print them"
fi

state_file="$(
  write_state_file "local_runtime_inventory" \
    "profile=$BLUEPRINT_PROFILE" \
    "environment=$(profile_environment)" \
    "kubeconfig_path=$kubeconfig_path" \
    "kube_context=$kube_context" \
    "kube_access_source=$kube_access_source" \
    "argocd_overlay_path=$overlay_path" \
    "provision_status=$provision_status" \
    "deploy_status=$deploy_status" \
    "smoke_status=$smoke_status" \
    "runtime_credentials_status=$runtime_credentials_status" \
    "workflows_keycloak_reconcile_status=$workflows_keycloak_status" \
    "langfuse_keycloak_reconcile_status=$langfuse_keycloak_status" \
    "enabled_modules=$(enabled_modules_csv)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "local runtime inventory profile=$BLUEPRINT_PROFILE env=$(profile_environment) context=$kube_context"
log_info "local runtime inventory kubeconfig=$kubeconfig_path overlay=$overlay_path"
log_info "local runtime inventory state written to $state_file"
