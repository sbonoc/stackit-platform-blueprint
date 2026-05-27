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
source "$ROOT_DIR/scripts/lib/infra/managed_cache.sh"

start_script_metric_trap "infra_managed_cache_apply"

if ! is_module_enabled managed-cache; then
  log_info "MANAGED_CACHE_ENABLED=false; skipping managed-cache apply"
  exit 0
fi

managed_cache_init_env

resolve_optional_module_execution "managed-cache" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_apply_foundation_contract "managed-cache"
  ;;
helm)
  provision_path="$(managed_cache_render_values_file)"
  managed_cache_reconcile_runtime_secret
  run_helm_upgrade_install \
    "$MANAGED_CACHE_HELM_RELEASE" \
    "$MANAGED_CACHE_NAMESPACE" \
    "$MANAGED_CACHE_HELM_CHART" \
    "$MANAGED_CACHE_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "managed-cache" "apply"
  ;;
esac

state_file="$(write_state_file "managed_cache_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "host=$(managed_cache_host)" \
  "port=$(managed_cache_port)" \
  "uri=$(managed_cache_uri)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "managed-cache runtime state written to $state_file"
