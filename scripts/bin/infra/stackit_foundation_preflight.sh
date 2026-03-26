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

start_script_metric_trap "infra_stackit_foundation_preflight"

usage() {
  cat <<'USAGE'
Usage: stackit_foundation_preflight.sh

Validates STACKIT foundation terraform layer routing and configuration.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

foundation_dir="$(stackit_layer_preflight "foundation")"

state_file="$(
  write_state_file "stackit_foundation_preflight" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "terraform_dir=$foundation_dir" \
    "tooling_mode=$(tooling_execution_mode)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit foundation preflight passed terraform_dir=$foundation_dir"
log_info "stackit foundation preflight state written to $state_file"
