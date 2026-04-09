#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/dns.sh"

start_script_metric_trap "infra_dns_plan"

if ! is_module_enabled dns; then
  log_info "DNS_ENABLED=false; skipping dns plan"
  exit 0
fi

dns_init_env
resolve_optional_module_execution "dns" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_warn_missing_foundation_diff "dns"
  ;;
noop)
  optional_module_log_execution_note
  ;;
*)
  optional_module_unexpected_driver "dns" "plan"
  ;;
esac

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
