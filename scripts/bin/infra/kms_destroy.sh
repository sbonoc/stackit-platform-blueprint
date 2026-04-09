#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/kms.sh"

start_script_metric_trap "infra_kms_destroy"

kms_init_env
resolve_optional_module_execution "kms" "destroy"
destroy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
destroy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$destroy_driver" in
foundation_reconcile_apply)
  optional_module_log_execution_note
  optional_module_destroy_foundation_contract "kms"
  ;;
external_automation_contract | noop)
  optional_module_log_execution_note
  ;;
*)
  optional_module_unexpected_driver "kms" "destroy"
  ;;
esac

remove_state_files_by_prefix "kms_"
state_file="$(write_state_file "kms_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "kms artifacts destroyed"
log_info "kms destroy state written to $state_file"
