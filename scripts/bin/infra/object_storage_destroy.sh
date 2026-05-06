#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/object_storage.sh"

start_script_metric_trap "infra_object_storage_destroy"

object_storage_init_env
resolve_optional_module_execution "object-storage" "destroy"
destroy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
destroy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$destroy_driver" in
foundation_reconcile_apply)
  optional_module_destroy_foundation_contract "object-storage"
  ;;
helm)
  destroy_path="$OBJECT_STORAGE_HELM_RELEASE@$OBJECT_STORAGE_NAMESPACE"
  run_helm_uninstall "$OBJECT_STORAGE_HELM_RELEASE" "$OBJECT_STORAGE_NAMESPACE"
  object_storage_delete_runtime_secret
  ;;
*)
  optional_module_unexpected_driver "object-storage" "destroy"
  ;;
esac

remove_state_files_by_prefix "object_storage_"
state_file="$(write_state_file "object_storage_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "object-storage artifacts destroyed"
log_info "object-storage destroy state written to $state_file"
