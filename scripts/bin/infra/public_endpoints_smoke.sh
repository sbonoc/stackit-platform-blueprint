#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
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

state_file="$(write_state_file "public_endpoints_smoke" \
  "status=passed" \
  "base_domain=$PUBLIC_ENDPOINTS_BASE_DOMAIN" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints smoke state written to $state_file"
