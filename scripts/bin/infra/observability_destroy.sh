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
source "$ROOT_DIR/scripts/lib/infra/observability.sh"

start_script_metric_trap "infra_observability_destroy"

observability_init_env
resolve_optional_module_execution "observability" "destroy"
destroy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
destroy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$destroy_driver" in
foundation_reconcile_apply)
  optional_module_destroy_foundation_contract "observability"
  ;;
argocd_manifest_plus_helm)
  run_manifest_delete "$destroy_path"
  run_helm_uninstall "blueprint-otel-collector" "$OBSERVABILITY_NAMESPACE"
  run_helm_uninstall "blueprint-observability" "$OBSERVABILITY_NAMESPACE"
  ;;
*)
  optional_module_unexpected_driver "observability" "destroy"
  ;;
esac

remove_state_files_by_prefix "observability_"
state_file="$(
  write_state_file "observability_destroy" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "destroy_driver=$destroy_driver" \
    "destroy_path=$destroy_path" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "observability artifacts destroyed"
log_info "observability destroy state written to $state_file"
