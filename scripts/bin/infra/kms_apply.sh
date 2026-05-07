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

resolve_optional_module_execution "kms" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_apply_foundation_contract "kms"
  ;;
helm)
  provision_path="$(kms_render_values_file)"
  run_helm_upgrade_install \
    "$KMS_VAULT_HELM_RELEASE" \
    "$KMS_NAMESPACE" \
    "$KMS_VAULT_HELM_CHART" \
    "$KMS_VAULT_HELM_CHART_VERSION" \
    "$provision_path"
  kms_enable_vault_transit
  kms_reconcile_runtime_secret
  ;;
*)
  optional_module_unexpected_driver "kms" "apply"
  ;;
esac

state_file="$(write_state_file "kms_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "key_ring_name=$KMS_KEY_RING_NAME" \
  "key_ring_id=$(kms_key_ring_id)" \
  "key_name=$KMS_KEY_NAME" \
  "key_id=$(kms_key_id)" \
  "endpoint=$(kms_endpoint)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "kms runtime state written to $state_file"
