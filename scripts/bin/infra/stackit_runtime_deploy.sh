#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_stackit_runtime_deploy"

usage() {
  cat <<'USAGE'
Usage: stackit_runtime_deploy.sh

Deploys STACKIT runtime path using contract-driven deploy wrapper.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-runtime-deploy requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

if ! state_file_exists stackit_runtime_prerequisites; then
  log_warn "stackit runtime prerequisites state not found; running prerequisites"
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_runtime_prerequisites.sh"
fi

run_cmd "$ROOT_DIR/scripts/bin/infra/deploy.sh"

overlay_path="$(argocd_overlay_dir)"
state_file="$(
  write_state_file "stackit_runtime_deploy" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "runtime_driver=argocd_kustomize" \
    "argocd_overlay_path=$overlay_path" \
    "enabled_modules=$(enabled_modules_csv)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit runtime deploy state written to $state_file"
