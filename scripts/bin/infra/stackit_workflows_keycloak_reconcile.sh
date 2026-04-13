#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak_identity_contract.sh"

start_script_metric_trap "infra_stackit_workflows_keycloak_reconcile"

if ! keycloak_optional_module_reconcile_should_run \
  "workflows" \
  "WORKFLOWS_ENABLED" \
  "workflows_keycloak_reconcile" \
  "workflows"; then
  exit 0
fi

keycloak_seed_env_defaults
workflows_init_env

keycloak_identity_contract_resolve_effective_realm_settings \
  "workflows" \
  "$KEYCLOAK_REALM_WORKFLOWS" \
  "Admin,User,Viewer,Op" \
  "Admin" \
  "STACKIT Workflows"

set_default_env STACKIT_WORKFLOWS_ADMIN_USERNAME "workflows-admin"
set_default_env STACKIT_WORKFLOWS_ADMIN_PASSWORD ""

workflows_realm_name="$KEYCLOAK_IDENTITY_EFFECTIVE_REALM_NAME"
workflows_role_names="$KEYCLOAK_IDENTITY_EFFECTIVE_ROLE_NAMES_CSV"
workflows_admin_role="$KEYCLOAK_IDENTITY_EFFECTIVE_ADMIN_ROLE"
workflows_client_display_name="$KEYCLOAK_IDENTITY_EFFECTIVE_CLIENT_DISPLAY_NAME"

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
  web_origin="$(keycloak_url_origin "$resolved_web_url")"
  web_origins="$(keycloak_csv_append_unique "$web_origins" "$web_origin")"
fi
if [[ -n "$resolved_redirect_uri" ]]; then
  redirect_uris="$(keycloak_csv_append_unique "$redirect_uris" "$resolved_redirect_uri")"
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

state_file="$(keycloak_optional_module_write_reconciled_state "workflows_keycloak_reconcile" \
  "realm=$workflows_realm_name" \
  "client_id=$STACKIT_WORKFLOWS_OIDC_CLIENT_ID" \
  "redirect_uris=$redirect_uris" \
  "web_origins=$web_origins" \
  "admin_username=$STACKIT_WORKFLOWS_ADMIN_USERNAME")"

log_info "workflows Keycloak reconciliation complete; state written to $state_file"
