#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stackit_layers.sh"

start_script_metric_trap "infra_stackit_foundation_refresh_kubeconfig"

usage() {
  cat <<'USAGE'
Usage: stackit_foundation_refresh_kubeconfig.sh

Refreshes STACKIT foundation credentials contract and then fetches local kubeconfig.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-foundation-refresh-kubeconfig requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

stackit_layer_preflight "foundation"
foundation_dir="$(stackit_layer_dir "foundation")"
backend_file="$(stackit_layer_backend_file "foundation")"
var_file="$(stackit_layer_var_file "foundation")"

run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh"

state_file="$(
  write_state_file "stackit_foundation_kubeconfig_refresh" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "terraform_dir=$foundation_dir" \
    "backend_file=$backend_file" \
    "var_file=$var_file" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit foundation kubeconfig refresh state written to $state_file"
