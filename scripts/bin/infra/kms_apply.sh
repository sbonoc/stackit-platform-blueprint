#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/kms.sh"

start_script_metric_trap "infra_kms_apply"

if ! is_module_enabled kms; then
  log_info "KMS_ENABLED=false; skipping kms apply"
  exit 0
fi

kms_init_env
if ! state_file_exists kms_plan; then
  log_fatal "missing kms plan artifact; run infra-kms-plan first"
fi

provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="external_automation_contract"
  provision_path="stackit-kms-external"
  log_warn "kms module has no Terraform provider coverage in STACKIT MVP; apply is an external-automation contract"
elif is_local_profile; then
  provision_driver="noop"
  log_warn "kms module has no managed local counterpart; apply is a contract no-op"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "kms_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "key_ring=$KMS_KEY_RING_NAME" \
  "key_name=$KMS_KEY_NAME" \
  "key_id=$(kms_key_id)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "kms runtime state written to $state_file"
