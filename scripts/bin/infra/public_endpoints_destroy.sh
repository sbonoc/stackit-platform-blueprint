#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/public_endpoints.sh"

start_script_metric_trap "infra_public_endpoints_destroy"

public_endpoints_init_env
resolve_optional_module_execution "public-endpoints" "destroy"
destroy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
destroy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
gateway_manifest_path="$(public_endpoints_render_gateway_manifest)"
destroy_path_components=()
case "$destroy_driver" in
argocd_application_chart)
  if tooling_is_execution_enabled; then
    if public_endpoints_gateway_api_crds_available; then
      run_manifest_delete "$gateway_manifest_path"
      destroy_path_components+=("$gateway_manifest_path")
    else
      log_metric "public_endpoints_gateway_manifest_delete_total" "1" "status=skipped_missing_crds"
      log_warn "skipping public-endpoints gateway manifest delete because Gateway API CRDs are absent"
    fi
  else
    run_manifest_delete "$gateway_manifest_path"
    destroy_path_components+=("$gateway_manifest_path")
  fi
  run_manifest_delete "$destroy_path"
  destroy_path_components+=("$destroy_path")
  ;;
helm)
  public_endpoints_delete_helm_gateway_baseline
  destroy_path_components+=("$PUBLIC_ENDPOINTS_HELM_RELEASE@$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE")
  destroy_path_components+=("$(public_endpoints_gateway_manifest_file)")
  run_helm_uninstall "$PUBLIC_ENDPOINTS_HELM_RELEASE" "$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE"
  ;;
*)
  optional_module_unexpected_driver "public-endpoints" "destroy"
  ;;
esac

destroy_path="$(IFS=,; printf '%s' "${destroy_path_components[*]}")"

remove_state_files_by_prefix "public_endpoints_"
state_file="$(write_state_file "public_endpoints_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints artifacts destroyed"
log_info "public-endpoints destroy state written to $state_file"
