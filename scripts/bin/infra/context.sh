#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

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

current_context="kubectl-unavailable"
if command -v kubectl >/dev/null 2>&1; then
  current_context="$(kubectl config current-context 2>/dev/null || true)"
  if [[ -z "$current_context" ]]; then
    current_context="unset"
  fi
fi

state_file="$(
  write_state_file "infra_context" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "kubectl_context=$current_context" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "infra context profile=$BLUEPRINT_PROFILE stack=$(active_stack) environment=$(profile_environment) kubectl_context=$current_context"
log_info "infra context state written to $state_file"
