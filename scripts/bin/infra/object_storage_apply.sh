#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
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

provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="foundation_contract"
  provision_path="$(stackit_terraform_layer_dir foundation)"
  if ! state_file_exists stackit_foundation_apply; then
    log_info "stackit foundation apply state missing; reconciling foundation for object-storage contract"
    run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_preflight.sh"
    run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
  fi
elif is_local_profile; then
  provision_driver="helm"
  provision_path="$(local_module_helm_values_file "object-storage")"
  run_helm_upgrade_install \
    "$OBJECT_STORAGE_HELM_RELEASE" \
    "$OBJECT_STORAGE_NAMESPACE" \
    "$OBJECT_STORAGE_HELM_CHART" \
    "$OBJECT_STORAGE_HELM_CHART_VERSION" \
    "$provision_path"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "object_storage_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "endpoint=$(object_storage_endpoint)" \
  "bucket=$OBJECT_STORAGE_BUCKET_NAME" \
  "access_key=$OBJECT_STORAGE_ACCESS_KEY" \
  "secret_key=$OBJECT_STORAGE_SECRET_KEY" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "object-storage runtime state written to $state_file"
