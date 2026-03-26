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

start_script_metric_trap "infra_object_storage_plan"

if ! is_module_enabled object-storage; then
  log_info "OBJECT_STORAGE_ENABLED=false; skipping object-storage plan"
  exit 0
fi

object_storage_init_env
resolve_optional_module_execution "object-storage" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_warn_missing_foundation_diff "object-storage"
  ;;
helm)
  run_helm_template \
    "$OBJECT_STORAGE_HELM_RELEASE" \
    "$OBJECT_STORAGE_NAMESPACE" \
    "$OBJECT_STORAGE_HELM_CHART" \
    "$OBJECT_STORAGE_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "object-storage" "plan"
  ;;
esac

state_file="$(write_state_file "object_storage_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "endpoint=$(object_storage_endpoint)" \
  "bucket=$OBJECT_STORAGE_BUCKET_NAME" \
  "region=$OBJECT_STORAGE_REGION" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "object-storage plan state written to $state_file"
