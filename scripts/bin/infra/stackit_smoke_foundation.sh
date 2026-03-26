#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_stackit_smoke_foundation"

usage() {
  cat <<'USAGE'
Usage: stackit_smoke_foundation.sh

Smoke-checks STACKIT foundation readiness in a pre-apply-safe way.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-smoke-foundation requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

run_cmd "$ROOT_DIR/scripts/bin/infra/validate.sh"

terraform_env_dir="$(stackit_terraform_env_dir)"
if ! terraform_dir_has_config "$terraform_env_dir"; then
  log_fatal "missing STACKIT terraform foundation config under $terraform_env_dir"
fi

state_file="$(
  write_state_file "stackit_smoke_foundation" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "terraform_env_dir=$terraform_env_dir" \
    "status=passed" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit foundation smoke state written to $state_file"
