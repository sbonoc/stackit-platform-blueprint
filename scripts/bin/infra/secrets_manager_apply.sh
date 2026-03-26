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

start_script_metric_trap "infra_secrets_manager_apply"

if ! is_module_enabled secrets-manager; then
  log_info "SECRETS_MANAGER_ENABLED=false; skipping secrets-manager apply"
  exit 0
fi

secrets_manager_init_env
if ! state_file_exists secrets_manager_plan; then
  log_fatal "missing secrets-manager plan artifact; run infra-secrets-manager-plan first"
fi

provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="foundation_contract"
  provision_path="$(stackit_terraform_layer_dir foundation)"
  if ! state_file_exists stackit_foundation_apply; then
    log_info "stackit foundation apply state missing; reconciling foundation for secrets-manager contract"
    run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_preflight.sh"
    run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
  fi
elif is_local_profile; then
  provision_driver="noop"
  log_warn "secrets-manager module has no managed local counterpart; apply is a contract no-op"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "secrets_manager_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "instance_name=$SECRETS_MANAGER_INSTANCE_NAME" \
  "endpoint=$(secrets_manager_endpoint)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "secrets-manager runtime state written to $state_file"
