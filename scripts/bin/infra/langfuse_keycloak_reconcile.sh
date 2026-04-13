#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak.sh"
source "$ROOT_DIR/scripts/lib/infra/langfuse.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak_identity_contract.sh"

start_script_metric_trap "infra_langfuse_keycloak_reconcile"

if ! keycloak_optional_module_reconcile_should_run \
  "langfuse" \
  "LANGFUSE_ENABLED" \
  "langfuse_keycloak_reconcile" \
  "langfuse"; then
  exit 0
fi

keycloak_seed_env_defaults
langfuse_init_env

keycloak_identity_contract_resolve_effective_realm_settings \
  "langfuse" \
  "$KEYCLOAK_REALM_LANGFUSE" \
  "admin,user" \
  "" \
  "Langfuse"

langfuse_realm_name="$KEYCLOAK_IDENTITY_EFFECTIVE_REALM_NAME"
langfuse_role_names="$KEYCLOAK_IDENTITY_EFFECTIVE_ROLE_NAMES_CSV"
langfuse_client_display_name="$KEYCLOAK_IDENTITY_EFFECTIVE_CLIENT_DISPLAY_NAME"

langfuse_url="$(langfuse_public_url)"
langfuse_origin="$(keycloak_url_origin "$langfuse_url")"
langfuse_callback_uri="${langfuse_origin}/api/auth/callback/keycloak"

keycloak_reconcile_oidc_identity_contract \
  "$KEYCLOAK_NAMESPACE" \
  "$KEYCLOAK_HELM_RELEASE" \
  "keycloak-runtime-credentials" \
  "$langfuse_realm_name" \
  "$LANGFUSE_OIDC_CLIENT_ID" \
  "$LANGFUSE_OIDC_CLIENT_SECRET" \
  "$langfuse_callback_uri" \
  "$langfuse_origin" \
  "$langfuse_role_names" \
  "" \
  "" \
  "" \
  "$langfuse_client_display_name"

state_file="$(keycloak_optional_module_write_reconciled_state "langfuse_keycloak_reconcile" \
  "realm=$langfuse_realm_name" \
  "client_id=$LANGFUSE_OIDC_CLIENT_ID" \
  "callback_uri=$langfuse_callback_uri" \
  "web_origin=$langfuse_origin")"

log_info "Langfuse Keycloak reconciliation complete; state written to $state_file"
