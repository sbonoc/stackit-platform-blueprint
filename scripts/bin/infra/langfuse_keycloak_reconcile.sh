#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak.sh"
source "$ROOT_DIR/scripts/lib/infra/langfuse.sh"
source "$ROOT_DIR/scripts/lib/infra/keycloak_identity_contract.sh"

start_script_metric_trap "infra_langfuse_keycloak_reconcile"

if ! is_module_enabled langfuse; then
  log_info "LANGFUSE_ENABLED=false; skipping Langfuse Keycloak reconciliation"
  exit 0
fi

if ! keycloak_reconciliation_enabled; then
  state_file="$(write_state_file "langfuse_keycloak_reconcile" \
    "status=disabled" \
    "reason=keycloak_optional_module_reconciliation_toggle_off" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"
  log_info "Langfuse Keycloak reconciliation disabled; state written to $state_file"
  exit 0
fi

keycloak_seed_env_defaults
langfuse_init_env

keycloak_identity_contract_load_realm "langfuse"

langfuse_realm_name="${KEYCLOAK_IDENTITY_CONTRACT_REALM_NAME:-$KEYCLOAK_REALM_LANGFUSE}"
langfuse_role_names="${KEYCLOAK_IDENTITY_CONTRACT_ROLE_NAMES_CSV:-admin,user}"
langfuse_client_display_name="${KEYCLOAK_IDENTITY_CONTRACT_CLIENT_DISPLAY_NAME:-Langfuse}"

langfuse_url="$(langfuse_public_url)"
langfuse_origin="$(printf '%s' "$langfuse_url" | sed -E 's#^(https?://[^/]+).*$#\1#')"
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

state_file="$(write_state_file "langfuse_keycloak_reconcile" \
  "status=reconciled" \
  "realm=$langfuse_realm_name" \
  "client_id=$LANGFUSE_OIDC_CLIENT_ID" \
  "callback_uri=$langfuse_callback_uri" \
  "web_origin=$langfuse_origin" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "Langfuse Keycloak reconciliation complete; state written to $state_file"
