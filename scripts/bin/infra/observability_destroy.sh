#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/observability.sh"

start_script_metric_trap "infra_observability_destroy"

observability_init_env
destroy_driver="none"
destroy_path="none"
if is_stackit_profile; then
  destroy_driver="foundation_reconcile_apply"
  destroy_path="$(stackit_terraform_layer_dir foundation)"
  run_cmd env OBSERVABILITY_ENABLED=false "$ROOT_DIR/scripts/bin/infra/stackit_foundation_preflight.sh"
  run_cmd env OBSERVABILITY_ENABLED=false "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
elif is_local_profile; then
  destroy_driver="argocd_manifest_plus_helm"
  destroy_path="$(argocd_optional_manifest "observability")"
  run_manifest_delete "$destroy_path"
  run_helm_uninstall "blueprint-otel-collector" "$OBSERVABILITY_NAMESPACE"
  run_helm_uninstall "blueprint-observability" "$OBSERVABILITY_NAMESPACE"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

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
