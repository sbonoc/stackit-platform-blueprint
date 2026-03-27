#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_context"

usage() {
  cat <<'USAGE'
Usage: context.sh

Prints current kubectl context together with blueprint profile metadata.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$(tooling_execution_mode)" == "execute" ]] && command -v kubectl >/dev/null 2>&1; then
  prepare_cluster_access
fi

current_context="kubectl-unavailable"
if command -v kubectl >/dev/null 2>&1; then
  current_context="$(active_kube_context_name)"
  if [[ -z "$current_context" ]]; then
    current_context="unset"
  fi
fi
context_source="$(active_kube_access_source)"

state_file="$(
  write_state_file "infra_context" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "kubectl_context=$current_context" \
    "kube_access_source=$context_source" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "infra context profile=$BLUEPRINT_PROFILE stack=$(active_stack) environment=$(profile_environment) kubectl_context=$current_context source=$context_source"
log_info "infra context state written to $state_file"
