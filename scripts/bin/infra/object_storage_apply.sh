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
source "$ROOT_DIR/scripts/lib/infra/object_storage.sh"

start_script_metric_trap "infra_object_storage_apply"

if ! is_module_enabled object-storage; then
  log_info "OBJECT_STORAGE_ENABLED=false; skipping object-storage apply"
  exit 0
fi

object_storage_init_env
if ! state_file_exists object_storage_plan; then
  log_fatal "missing object-storage plan artifact; run infra-object-storage-plan first"
fi

resolve_optional_module_execution "object-storage" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_apply_foundation_contract "object-storage"
  ;;
helm)
  run_helm_upgrade_install \
    "$OBJECT_STORAGE_HELM_RELEASE" \
    "$OBJECT_STORAGE_NAMESPACE" \
    "$OBJECT_STORAGE_HELM_CHART" \
    "$OBJECT_STORAGE_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "object-storage" "apply"
  ;;
esac

state_file="$(write_state_file "object_storage_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "endpoint=$(object_storage_endpoint)" \
  "bucket=$(object_storage_bucket_name)" \
  "access_key=$(object_storage_access_key)" \
  "secret_key=$(object_storage_secret_key)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "object-storage runtime state written to $state_file"
