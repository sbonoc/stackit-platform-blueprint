#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak_identity_contract.sh"

start_script_metric_trap "infra_stackit_workflows_keycloak_reconcile"

if ! is_module_enabled workflows; then
  log_info "WORKFLOWS_ENABLED=false; skipping workflows Keycloak reconciliation"
  exit 0
fi

if ! keycloak_reconciliation_enabled; then
  state_file="$(write_state_file "workflows_keycloak_reconcile" \
    "status=disabled" \
    "reason=keycloak_optional_module_reconciliation_toggle_off" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"
  log_info "workflows Keycloak reconciliation disabled; state written to $state_file"
  exit 0
fi

keycloak_seed_env_defaults
workflows_init_env

keycloak_identity_contract_load_realm "workflows"

set_default_env STACKIT_WORKFLOWS_ADMIN_USERNAME "workflows-admin"
set_default_env STACKIT_WORKFLOWS_ADMIN_PASSWORD "$STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET"

workflows_realm_name="${KEYCLOAK_IDENTITY_CONTRACT_REALM_NAME:-$KEYCLOAK_REALM_WORKFLOWS}"
workflows_role_names="${KEYCLOAK_IDENTITY_CONTRACT_ROLE_NAMES_CSV:-Admin,User,Viewer,Op}"
workflows_admin_role="${KEYCLOAK_IDENTITY_CONTRACT_ADMIN_ROLE:-Admin}"
workflows_client_display_name="${KEYCLOAK_IDENTITY_CONTRACT_CLIENT_DISPLAY_NAME:-STACKIT Workflows}"

csv_append_unique() {
  local csv_value="$1"
  local item="$2"
  local token=""
  [[ -n "$item" ]] || {
    printf '%s' "$csv_value"
    return 0
  }

  IFS=',' read -r -a tokens <<<"$csv_value"
  for token in "${tokens[@]}"; do
    if [[ "$token" == "$item" ]]; then
      printf '%s' "$csv_value"
      return 0
    fi
  done

  if [[ -z "$csv_value" ]]; then
    printf '%s' "$item"
    return 0
  fi
  printf '%s,%s' "$csv_value" "$item"
}

redirect_uris="https://*.workflows.${STACKIT_REGION}.stackit.cloud/*"
web_origins="https://*.workflows.${STACKIT_REGION}.stackit.cloud"
resolved_web_url=""
resolved_redirect_uri=""

if state_file_exists workflows_instance; then
  workflows_state_file="$(state_file_path workflows_instance)"
  resolved_web_url="$(grep -E '^web_url=' "$workflows_state_file" | head -n1 | cut -d= -f2- || true)"
  resolved_redirect_uri="$(grep -E '^redirect_uri=' "$workflows_state_file" | head -n1 | cut -d= -f2- || true)"
fi

if [[ -n "$resolved_web_url" ]]; then
  web_origin="$(printf '%s' "$resolved_web_url" | sed -E 's#^(https?://[^/]+).*$#\1#')"
  web_origins="$(csv_append_unique "$web_origins" "$web_origin")"
fi
if [[ -n "$resolved_redirect_uri" ]]; then
  redirect_uris="$(csv_append_unique "$redirect_uris" "$resolved_redirect_uri")"
fi

keycloak_reconcile_oidc_identity_contract \
  "$KEYCLOAK_NAMESPACE" \
  "$KEYCLOAK_HELM_RELEASE" \
  "keycloak-runtime-credentials" \
  "$workflows_realm_name" \
  "$STACKIT_WORKFLOWS_OIDC_CLIENT_ID" \
  "$STACKIT_WORKFLOWS_OIDC_CLIENT_SECRET" \
  "$redirect_uris" \
  "$web_origins" \
  "$workflows_role_names" \
  "$STACKIT_WORKFLOWS_ADMIN_USERNAME" \
  "$STACKIT_WORKFLOWS_ADMIN_PASSWORD" \
  "$workflows_admin_role" \
  "$workflows_client_display_name"

state_file="$(write_state_file "workflows_keycloak_reconcile" \
  "status=reconciled" \
  "realm=$workflows_realm_name" \
  "client_id=$STACKIT_WORKFLOWS_OIDC_CLIENT_ID" \
  "redirect_uris=$redirect_uris" \
  "web_origins=$web_origins" \
  "admin_username=$STACKIT_WORKFLOWS_ADMIN_USERNAME" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "workflows Keycloak reconciliation complete; state written to $state_file"
