#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stackit_layers.sh"

start_script_metric_trap "infra_stackit_bootstrap_destroy"

usage() {
  cat <<'USAGE'
Usage: stackit_bootstrap_destroy.sh

Runs terraform destroy for the STACKIT bootstrap layer.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

bootstrap_dir="$(stackit_layer_preflight "bootstrap")"
run_terraform_action destroy "$bootstrap_dir"

state_file="$(
  write_state_file "stackit_bootstrap_destroy" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "terraform_dir=$bootstrap_dir" \
    "action=destroy" \
    "tooling_mode=$(tooling_execution_mode)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit bootstrap destroy state written to $state_file"
