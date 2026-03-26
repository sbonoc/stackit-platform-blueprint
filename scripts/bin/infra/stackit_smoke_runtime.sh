#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "infra_stackit_smoke_runtime"

usage() {
  cat <<'USAGE'
Usage: stackit_smoke_runtime.sh

Smoke-checks STACKIT runtime convergence after runtime deploy.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-smoke-runtime requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

if ! state_file_exists stackit_runtime_deploy; then
  log_fatal "missing stackit runtime deploy state; run make infra-stackit-runtime-deploy first"
fi

run_cmd "$ROOT_DIR/scripts/bin/infra/smoke.sh"

state_file="$(
  write_state_file "stackit_smoke_runtime" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "status=passed" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit runtime smoke state written to $state_file"
