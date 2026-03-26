#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "infra_status"

usage() {
  cat <<'USAGE'
Usage: status.sh

Prints compact infrastructure status derived from canonical state artifacts.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

state_flag() {
  local artifact_name="$1"
  if state_file_exists "$artifact_name"; then
    echo "present"
    return 0
  fi
  echo "missing"
}

provision_status="$(state_flag provision)"
deploy_status="$(state_flag deploy)"
smoke_status="$(state_flag smoke)"
stackit_bootstrap_status="$(state_flag stackit_bootstrap_apply)"
stackit_foundation_status="$(state_flag stackit_foundation_apply)"
stackit_runtime_status="$(state_flag stackit_runtime_deploy)"
stackit_runtime_smoke_status="$(state_flag stackit_smoke_runtime)"

log_info "infra status profile=$BLUEPRINT_PROFILE stack=$(active_stack) enabled_modules=$(enabled_modules_csv)"
log_info "infra status provision=$provision_status deploy=$deploy_status smoke=$smoke_status"
log_info "infra status stackit_bootstrap_apply=$stackit_bootstrap_status stackit_foundation_apply=$stackit_foundation_status"
log_info "infra status stackit_runtime_deploy=$stackit_runtime_status stackit_smoke_runtime=$stackit_runtime_smoke_status"

state_file="$(
  write_state_file "infra_status" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "enabled_modules=$(enabled_modules_csv)" \
    "provision_status=$provision_status" \
    "deploy_status=$deploy_status" \
    "smoke_status=$smoke_status" \
    "stackit_bootstrap_apply_status=$stackit_bootstrap_status" \
    "stackit_foundation_apply_status=$stackit_foundation_status" \
    "stackit_runtime_deploy_status=$stackit_runtime_status" \
    "stackit_smoke_runtime_status=$stackit_runtime_smoke_status" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "infra status state written to $state_file"
