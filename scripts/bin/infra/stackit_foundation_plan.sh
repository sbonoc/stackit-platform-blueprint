#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stackit_layers.sh"

start_script_metric_trap "infra_stackit_foundation_plan"

usage() {
  cat <<'USAGE'
Usage: stackit_foundation_plan.sh

Runs terraform plan for the STACKIT foundation layer.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

stackit_layer_preflight "foundation"
foundation_dir="$(stackit_layer_dir "foundation")"
backend_file="$(stackit_layer_backend_file "foundation")"
var_file="$(stackit_layer_var_file "foundation")"
tf_var_args=()
while IFS= read -r arg; do
  [[ -n "$arg" ]] || continue
  tf_var_args+=("$arg")
done < <(stackit_layer_var_args "foundation")
run_terraform_action_with_backend plan "$foundation_dir" "$backend_file" "$var_file" "${tf_var_args[@]}"

state_file="$(
  write_state_file "stackit_foundation_plan" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "terraform_dir=$foundation_dir" \
    "backend_file=$backend_file" \
    "var_file=$var_file" \
    "tfstate_credential_source=${STACKIT_TFSTATE_CREDENTIAL_SOURCE:-unknown}" \
    "action=plan" \
    "tooling_mode=$(tooling_execution_mode)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit foundation plan state written to $state_file"
