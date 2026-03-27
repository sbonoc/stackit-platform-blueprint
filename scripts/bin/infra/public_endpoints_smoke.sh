#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/public_endpoints.sh"

start_script_metric_trap "infra_public_endpoints_smoke"

if ! is_module_enabled public-endpoints; then
  log_info "PUBLIC_ENDPOINTS_ENABLED=false; skipping public-endpoints smoke"
  exit 0
fi

public_endpoints_init_env
if ! state_file_exists public_endpoints_runtime; then
  log_fatal "missing public-endpoints runtime artifact"
fi

runtime_state="$(state_file_path public_endpoints_runtime)"
if ! grep -q '^base_domain=' "$runtime_state"; then
  log_fatal "public-endpoints runtime base_domain contract is missing"
fi
if ! grep -q '^gateway_name=' "$runtime_state"; then
  log_fatal "public-endpoints runtime gateway_name contract is missing"
fi
if ! grep -q '^gateway_class_name=' "$runtime_state"; then
  log_fatal "public-endpoints runtime gateway_class_name contract is missing"
fi
gateway_manifest_path="$(grep '^gateway_manifest_path=' "$runtime_state" | head -n1 | cut -d= -f2-)"
if [[ -z "$gateway_manifest_path" || ! -f "$gateway_manifest_path" ]]; then
  log_fatal "public-endpoints runtime gateway manifest artifact is missing"
fi
if ! grep -q '^kind: GatewayClass$' "$gateway_manifest_path"; then
  log_fatal "public-endpoints gateway manifest is missing GatewayClass"
fi
if ! grep -q '^kind: Gateway$' "$gateway_manifest_path"; then
  log_fatal "public-endpoints gateway manifest is missing Gateway"
fi
if ! grep -q 'from: All' "$gateway_manifest_path"; then
  log_fatal "public-endpoints gateway listener does not allow cross-namespace route attachment"
fi

log_metric \
  "public_endpoints_gateway_contract_check_total" \
  "1" \
  "gateway_name=$PUBLIC_ENDPOINTS_GATEWAY_NAME gateway_class_name=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME"
log_info "validated shared Gateway API contract gateway=$PUBLIC_ENDPOINTS_GATEWAY_NAME class=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME"

state_file="$(write_state_file "public_endpoints_smoke" \
  "status=passed" \
  "base_domain=$PUBLIC_ENDPOINTS_BASE_DOMAIN" \
  "gateway_name=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
  "gateway_class_name=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" \
  "gateway_manifest_path=$gateway_manifest_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints smoke state written to $state_file"
