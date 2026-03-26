#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/secrets_manager.sh"

start_script_metric_trap "infra_secrets_manager_destroy"

secrets_manager_init_env
destroy_driver="none"
destroy_path="none"
if is_stackit_profile; then
  destroy_driver="foundation_reconcile_apply"
  destroy_path="$(stackit_terraform_layer_dir foundation)"
  run_cmd env SECRETS_MANAGER_ENABLED=false "$ROOT_DIR/scripts/bin/infra/stackit_foundation_preflight.sh"
  run_cmd env SECRETS_MANAGER_ENABLED=false "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
elif is_local_profile; then
  destroy_driver="noop"
  log_warn "secrets-manager module has no managed local counterpart; destroy is a contract no-op"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

remove_state_files_by_prefix "secrets_manager_"
state_file="$(write_state_file "secrets_manager_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "secrets-manager artifacts destroyed"
log_info "secrets-manager destroy state written to $state_file"
