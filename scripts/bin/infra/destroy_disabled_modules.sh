#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh"

start_script_metric_trap "infra_destroy_disabled_modules"

usage() {
  cat <<'USAGE'
Usage: destroy_disabled_modules.sh

Contract-driven cleanup wrapper:
- validates repository contract,
- executes destroy actions for optional modules currently disabled by flags,
- persists cleanup state under artifacts/infra.

This target is designed to be run before infra-bootstrap pruning when
optional modules are toggled from enabled to disabled.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

all_modules=(
  observability
  workflows
  langfuse
  postgres
  neo4j
  object-storage
  rabbitmq
  dns
  public-endpoints
  secrets-manager
  kms
  identity-aware-proxy
)

disabled_modules_csv() {
  local out=""
  local module
  for module in "${all_modules[@]}"; do
    if is_module_enabled "$module"; then
      continue
    fi
    if [[ -n "$out" ]]; then
      out+=","
    fi
    out+="$module"
  done
  if [[ -z "$out" ]]; then
    echo "none"
    return 0
  fi
  echo "$out"
}

log_info "destroy-disabled-modules start profile=$BLUEPRINT_PROFILE stack=$(active_stack) tooling_mode=$(tooling_execution_mode)"
run_cmd "$ROOT_DIR/scripts/bin/infra/validate.sh"

disabled_modules="$(disabled_modules_csv)"
if [[ "$disabled_modules" == "none" ]]; then
  log_info "no disabled optional modules detected; nothing to destroy"
else
  log_info "destroying currently disabled optional modules: $disabled_modules"
fi

run_disabled_modules_action destroy "${all_modules[@]}"

state_file="$(
  write_state_file "destroy_disabled_modules" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "enabled_modules=$(enabled_modules_csv)" \
    "disabled_modules=$disabled_modules" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "disabled-module destroy state written to $state_file"
log_info "infra destroy-disabled-modules complete"
