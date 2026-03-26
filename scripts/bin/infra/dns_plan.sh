#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/dns.sh"

start_script_metric_trap "infra_dns_plan"

if ! is_module_enabled dns; then
  log_info "DNS_ENABLED=false; skipping dns plan"
  exit 0
fi

dns_init_env
provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="foundation_contract"
  provision_path="$(stackit_terraform_layer_dir foundation)"
  if ! state_file_exists stackit_foundation_plan && ! state_file_exists stackit_foundation_apply; then
    log_warn "STACKIT foundation plan/apply state not found; run infra-stackit-foundation-plan for full terraform diff"
  fi
elif is_local_profile; then
  provision_driver="noop"
  log_warn "dns module has no managed local counterpart; plan is a contract no-op"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "dns_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "zone_id=$(dns_zone_id)" \
  "zone_name=$DNS_ZONE_NAME" \
  "zone_fqdn=$DNS_ZONE_FQDN" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "dns plan state written to $state_file"
