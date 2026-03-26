#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/kms.sh"

start_script_metric_trap "infra_kms_plan"

if ! is_module_enabled kms; then
  log_info "KMS_ENABLED=false; skipping kms plan"
  exit 0
fi

kms_init_env
resolve_optional_module_execution "kms" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
external_automation_contract | noop)
  optional_module_log_execution_note
  ;;
*)
  optional_module_unexpected_driver "kms" "plan"
  ;;
esac

state_file="$(write_state_file "kms_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "key_ring=$KMS_KEY_RING_NAME" \
  "key_name=$KMS_KEY_NAME" \
  "key_id=$(kms_key_id)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "kms plan state written to $state_file"
