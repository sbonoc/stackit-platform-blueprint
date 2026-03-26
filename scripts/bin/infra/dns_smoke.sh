#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/dns.sh"

start_script_metric_trap "infra_dns_smoke"

if ! is_module_enabled dns; then
  log_info "DNS_ENABLED=false; skipping dns smoke"
  exit 0
fi

dns_init_env
if ! state_file_exists dns_runtime; then
  log_fatal "missing dns runtime artifact"
fi

runtime_state="$(state_file_path dns_runtime)"
if ! grep -q '^zone_name=' "$runtime_state"; then
  log_fatal "dns runtime zone_name contract is missing"
fi

state_file="$(write_state_file "dns_smoke" \
  "status=passed" \
  "zone_id=$(dns_zone_id)" \
  "zone_name=$DNS_ZONE_NAME" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "dns smoke state written to $state_file"
