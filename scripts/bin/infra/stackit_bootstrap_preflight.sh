#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stackit_layers.sh"

start_script_metric_trap "infra_stackit_bootstrap_preflight"

usage() {
  cat <<'USAGE'
Usage: stackit_bootstrap_preflight.sh

Validates STACKIT bootstrap terraform layer routing and configuration.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

stackit_layer_preflight "bootstrap"
bootstrap_dir="$(stackit_layer_dir "bootstrap")"
backend_file="$(stackit_layer_backend_file "bootstrap")"
var_file="$(stackit_layer_var_file "bootstrap")"

state_file="$(
  write_state_file "stackit_bootstrap_preflight" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "terraform_dir=$bootstrap_dir" \
    "backend_file=$backend_file" \
    "var_file=$var_file" \
    "tfstate_credential_source=${STACKIT_TFSTATE_CREDENTIAL_SOURCE:-unknown}" \
    "tooling_mode=$(tooling_execution_mode)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit bootstrap preflight passed terraform_dir=$bootstrap_dir backend_file=$backend_file var_file=$var_file"
log_info "stackit bootstrap preflight state written to $state_file"
