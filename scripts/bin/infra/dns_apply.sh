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

start_script_metric_trap "infra_dns_apply"

if ! is_module_enabled dns; then
  log_info "DNS_ENABLED=false; skipping dns apply"
  exit 0
fi

dns_init_env
if ! state_file_exists dns_plan; then
  log_fatal "missing dns plan artifact; run infra-dns-plan first"
fi

provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="terraform"
  provision_path="$(stackit_terraform_module_dir "dns")"
  run_terraform_action apply "$provision_path"
elif is_local_profile; then
  provision_driver="noop"
  log_warn "dns module has no managed local counterpart; apply is a contract no-op"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "dns_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "zone_id=$(dns_zone_id)" \
  "zone_name=$DNS_ZONE_NAME" \
  "zone_fqdn=$DNS_ZONE_FQDN" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "dns runtime state written to $state_file"
