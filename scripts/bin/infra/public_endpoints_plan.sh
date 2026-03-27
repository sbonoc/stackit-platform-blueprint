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

start_script_metric_trap "infra_public_endpoints_plan"

if ! is_module_enabled public-endpoints; then
  log_info "PUBLIC_ENDPOINTS_ENABLED=false; skipping public-endpoints plan"
  exit 0
fi

public_endpoints_init_env
resolve_optional_module_execution "public-endpoints" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
gateway_manifest_path="$provision_path"
case "$provision_driver" in
argocd_application_chart)
  optional_module_require_manifest_present "public-endpoints" "$provision_path"
  ;;
helm)
  provision_path="$(public_endpoints_render_values_file)"
  gateway_manifest_path="$(public_endpoints_render_gateway_manifest)"
  run_helm_template \
    "$PUBLIC_ENDPOINTS_HELM_RELEASE" \
    "$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE" \
    "$PUBLIC_ENDPOINTS_HELM_CHART" \
    "$PUBLIC_ENDPOINTS_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "public-endpoints" "plan"
  ;;
esac

state_file="$(write_state_file "public_endpoints_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "edge_mode=gateway_api_envoy" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "gateway_manifest_path=$gateway_manifest_path" \
  "base_domain=$PUBLIC_ENDPOINTS_BASE_DOMAIN" \
  "gateway_name=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
  "gateway_class_name=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" \
  "gateway_namespace=$PUBLIC_ENDPOINTS_NAMESPACE" \
  "controller_namespace=$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE" \
  "listener_policy=allow_cross_namespace_routes" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints plan state written to $state_file"
