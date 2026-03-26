#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/secrets_manager.sh"

start_script_metric_trap "infra_secrets_manager_plan"

if ! is_module_enabled secrets-manager; then
  log_info "SECRETS_MANAGER_ENABLED=false; skipping secrets-manager plan"
  exit 0
fi

secrets_manager_init_env
provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="terraform"
  provision_path="$(stackit_terraform_module_dir "secrets-manager")"
  run_terraform_action plan "$provision_path"
elif is_local_profile; then
  provision_driver="noop"
  log_warn "secrets-manager module has no managed local counterpart; plan is a contract no-op"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "secrets_manager_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "instance_name=$SECRETS_MANAGER_INSTANCE_NAME" \
  "endpoint=$(secrets_manager_endpoint)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "secrets-manager plan state written to $state_file"
