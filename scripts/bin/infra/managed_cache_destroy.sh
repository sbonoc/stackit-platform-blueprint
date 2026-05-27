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

start_script_metric_trap "infra_managed_cache_destroy"

if ! is_module_enabled managed-cache; then
  log_info "MANAGED_CACHE_ENABLED=false; skipping managed-cache destroy"
  exit 0
fi

managed_cache_init_env
resolve_optional_module_execution "managed-cache" "destroy"
destroy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
destroy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$destroy_driver" in
foundation_reconcile_apply)
  optional_module_destroy_foundation_contract "managed-cache"
  ;;
helm)
  destroy_path="$MANAGED_CACHE_HELM_RELEASE@$MANAGED_CACHE_NAMESPACE"
  run_helm_uninstall "$MANAGED_CACHE_HELM_RELEASE" "$MANAGED_CACHE_NAMESPACE"
  managed_cache_delete_runtime_secret
  ;;
*)
  optional_module_unexpected_driver "managed-cache" "destroy"
  ;;
esac

remove_state_files_by_prefix "managed_cache_"
state_file="$(write_state_file "managed_cache_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "managed-cache artifacts destroyed"
log_info "managed-cache destroy state written to $state_file"
