#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
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

stackit_layer_preflight "bootstrap"
bootstrap_dir="$(stackit_layer_dir "bootstrap")"
backend_file="$(stackit_layer_backend_file "bootstrap")"
var_file="$(stackit_layer_var_file "bootstrap")"
tf_var_args=()
while IFS= read -r arg; do
  [[ -n "$arg" ]] || continue
  tf_var_args+=("$arg")
done < <(stackit_layer_var_args "bootstrap")
run_terraform_action_with_backend destroy "$bootstrap_dir" "$backend_file" "$var_file" "${tf_var_args[@]}"

state_file="$(
  write_state_file "stackit_bootstrap_destroy" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "terraform_dir=$bootstrap_dir" \
    "backend_file=$backend_file" \
    "var_file=$var_file" \
    "tfstate_credential_source=${STACKIT_TFSTATE_CREDENTIAL_SOURCE:-unknown}" \
    "action=destroy" \
    "tooling_mode=$(tooling_execution_mode)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit bootstrap destroy state written to $state_file"
