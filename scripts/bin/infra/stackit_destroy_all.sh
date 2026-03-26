#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "infra_stackit_destroy_all"

usage() {
  cat <<'USAGE'
Usage: stackit_destroy_all.sh

Destroys STACKIT foundation and bootstrap terraform layers in canonical order.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-destroy-all requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_destroy.sh"
run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_bootstrap_destroy.sh"

state_file="$(
  write_state_file "stackit_destroy_all" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "destroy_order=foundation_then_bootstrap" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit destroy-all state written to $state_file"
