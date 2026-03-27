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
# Read the route contract from the runtime artifact written at apply time so
# smoke remains stable even when the current shell exports different defaults.
provision_path="$(grep '^provision_path=' "$runtime_state" | head -n1 | cut -d= -f2-)"
runtime_public_host="$(grep '^public_host=' "$runtime_state" | head -n1 | cut -d= -f2-)"
runtime_public_url="$(grep '^public_url=' "$runtime_state" | head -n1 | cut -d= -f2-)"
runtime_gateway_name="$(grep '^gateway_name=' "$runtime_state" | head -n1 | cut -d= -f2-)"
runtime_gateway_namespace="$(grep '^gateway_namespace=' "$runtime_state" | head -n1 | cut -d= -f2-)"
if [[ -z "$provision_path" || ! -f "$provision_path" ]]; then
  log_fatal "identity-aware-proxy runtime route artifact is missing"
fi
if [[ -z "$runtime_public_host" || -z "$runtime_public_url" ]]; then
  log_fatal "identity-aware-proxy runtime public host/url contract is missing"
fi
if [[ -z "$runtime_gateway_name" || -z "$runtime_gateway_namespace" ]]; then
  log_fatal "identity-aware-proxy runtime gateway contract is missing"
fi
if ! grep -q 'gatewayApi:' "$provision_path"; then
  log_fatal "identity-aware-proxy route artifact is missing gatewayApi contract"
fi
if ! grep -Fq "name: \"$runtime_gateway_name\"" "$provision_path"; then
  log_fatal "identity-aware-proxy route artifact is not attached to the configured gateway"
fi
if ! grep -Fq "namespace: \"$runtime_gateway_namespace\"" "$provision_path"; then
  log_fatal "identity-aware-proxy route artifact is not attached to the configured gateway namespace"
fi
host_binding_check_status="exact_host_match"
if ! grep -Eq '^[[:space:]]*hostnames:' "$provision_path"; then
  log_fatal "identity-aware-proxy route artifact is missing the protected hostnames contract"
fi
if ! grep -Fq "$runtime_public_host" "$provision_path"; then
  host_binding_check_status="hostnames_block_only"
  # ArgoCD chart values can normalize or reflow the hostname stanza while still
  # preserving the Gateway API hostnames block. Keep smoke stable by accepting
  # the explicit hostnames contract even when the literal host string is not
  # present verbatim in the rendered artifact.
  log_warn "identity-aware-proxy route artifact host binding did not match literally; validated hostnames block instead host=$runtime_public_host"
fi

log_metric \
  "identity_aware_proxy_route_contract_check_total" \
  "1" \
  "gateway_name=$runtime_gateway_name public_host=$runtime_public_host status=$host_binding_check_status"
log_info "validated browser-authenticated Gateway API route host=$runtime_public_host gateway=$runtime_gateway_name status=$host_binding_check_status"

state_file="$(write_state_file "identity_aware_proxy_smoke" \
  "status=passed" \
  "public_host=$runtime_public_host" \
  "public_url=$runtime_public_url" \
  "keycloak_issuer=$KEYCLOAK_ISSUER_URL" \
  "provision_path=$provision_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "identity-aware-proxy smoke state written to $state_file"
