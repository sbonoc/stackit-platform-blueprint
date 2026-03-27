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
source "$ROOT_DIR/scripts/lib/infra/public_endpoints.sh"

start_script_metric_trap "infra_public_endpoints_deploy"

if ! is_module_enabled public-endpoints; then
  log_info "PUBLIC_ENDPOINTS_ENABLED=false; skipping public-endpoints deploy"
  exit 0
fi

public_endpoints_init_env
if ! state_file_exists public_endpoints_runtime; then
  log_fatal "missing public-endpoints runtime artifact; run infra-public-endpoints-apply first"
fi

resolve_optional_module_execution "public-endpoints" "deploy"
deploy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
deploy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
namespace_manifest_path="$(public_endpoints_render_namespace_manifest)"
gateway_manifest_path="$(public_endpoints_render_gateway_manifest)"
deploy_status="already_applied"
gateway_api_wait_status="not_required"
case "$deploy_driver" in
argocd_application_chart)
  run_manifest_apply "$deploy_path"
  run_manifest_apply "$namespace_manifest_path"
  public_endpoints_wait_for_gateway_api_crds
  gateway_api_wait_status="ready"
  run_manifest_apply "$gateway_manifest_path"
  deploy_status="applied_via_argocd_manifest"
  ;;
helm)
  # Local Helm-backed public-endpoints already reconciles the controller and
  # shared Gateway baseline during apply. Deploy records the phase boundary so
  # `infra-deploy` stays symmetrical across module families.
  gateway_api_wait_status="already_applied"
  :
  ;;
*)
  optional_module_unexpected_driver "public-endpoints" "deploy"
  ;;
esac

state_file="$(write_state_file "public_endpoints_deploy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "deploy_driver=$deploy_driver" \
  "deploy_path=$deploy_path" \
  "namespace_manifest_path=$namespace_manifest_path" \
  "gateway_manifest_path=$gateway_manifest_path" \
  "deploy_status=$deploy_status" \
  "gateway_api_wait_status=$gateway_api_wait_status" \
  "gateway_name=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
  "gateway_class_name=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" \
  "gateway_namespace=$PUBLIC_ENDPOINTS_NAMESPACE" \
  "controller_namespace=$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints deploy state written to $state_file"
