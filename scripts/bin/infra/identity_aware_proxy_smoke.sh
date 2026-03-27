#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/identity_aware_proxy.sh"

start_script_metric_trap "infra_identity_aware_proxy_smoke"

if ! is_module_enabled identity-aware-proxy; then
  log_info "IDENTITY_AWARE_PROXY_ENABLED=false; skipping identity-aware-proxy smoke"
  exit 0
fi

identity_aware_proxy_init_env
if ! state_file_exists identity_aware_proxy_runtime; then
  log_fatal "missing identity-aware-proxy runtime artifact"
fi
if [[ ! "$KEYCLOAK_ISSUER_URL" =~ ^https?:// ]]; then
  log_fatal "KEYCLOAK_ISSUER_URL must be a valid HTTP(S) URL"
fi

runtime_state="$(state_file_path identity_aware_proxy_runtime)"
if ! grep -q '^keycloak_issuer=https\?://' "$runtime_state"; then
  log_fatal "identity-aware-proxy runtime OIDC issuer contract is invalid"
fi
provision_path="$(grep '^provision_path=' "$runtime_state" | head -n1 | cut -d= -f2-)"
if [[ -z "$provision_path" || ! -f "$provision_path" ]]; then
  log_fatal "identity-aware-proxy runtime route artifact is missing"
fi
if ! grep -q 'gatewayApi:' "$provision_path"; then
  log_fatal "identity-aware-proxy route artifact is missing gatewayApi contract"
fi
if ! grep -Fq "name: \"$PUBLIC_ENDPOINTS_GATEWAY_NAME\"" "$provision_path"; then
  log_fatal "identity-aware-proxy route artifact is not attached to the configured gateway"
fi
if ! grep -Fq "namespace: \"$PUBLIC_ENDPOINTS_NAMESPACE\"" "$provision_path"; then
  log_fatal "identity-aware-proxy route artifact is not attached to the configured gateway namespace"
fi
if ! grep -Fq "$(identity_aware_proxy_public_host)" "$provision_path"; then
  log_fatal "identity-aware-proxy route artifact is missing the protected host binding"
fi

log_metric \
  "identity_aware_proxy_route_contract_check_total" \
  "1" \
  "gateway_name=$PUBLIC_ENDPOINTS_GATEWAY_NAME public_host=$(identity_aware_proxy_public_host)"
log_info "validated browser-authenticated Gateway API route host=$(identity_aware_proxy_public_host) gateway=$PUBLIC_ENDPOINTS_GATEWAY_NAME"

state_file="$(write_state_file "identity_aware_proxy_smoke" \
  "status=passed" \
  "public_host=$(identity_aware_proxy_public_host)" \
  "public_url=$(identity_aware_proxy_public_url)" \
  "keycloak_issuer=$KEYCLOAK_ISSUER_URL" \
  "provision_path=$provision_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "identity-aware-proxy smoke state written to $state_file"
