#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
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

state_file="$(write_state_file "identity_aware_proxy_smoke" \
  "status=passed" \
  "public_url=$(identity_aware_proxy_public_url)" \
  "keycloak_issuer=$KEYCLOAK_ISSUER_URL" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "identity-aware-proxy smoke state written to $state_file"
