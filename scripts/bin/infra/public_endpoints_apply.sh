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
source "$ROOT_DIR/scripts/lib/infra/public_endpoints.sh"

start_script_metric_trap "infra_public_endpoints_apply"

if ! is_module_enabled public-endpoints; then
  log_info "PUBLIC_ENDPOINTS_ENABLED=false; skipping public-endpoints apply"
  exit 0
fi

public_endpoints_init_env
if ! state_file_exists public_endpoints_plan; then
  log_fatal "missing public-endpoints plan artifact; run infra-public-endpoints-plan first"
fi

resolve_optional_module_execution "public-endpoints" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
namespace_manifest_path="$(public_endpoints_render_namespace_manifest)"
gateway_manifest_path="$(public_endpoints_render_gateway_manifest)"
provision_status="applied"
case "$provision_driver" in
argocd_application_chart)
  # ArgoCD-backed fallback modules are applied during deploy after the core
  # runtime bootstraps the ArgoCD CRDs and controller into the cluster.
  provision_status="deferred_to_deploy"
  log_info "deferring public-endpoints ArgoCD manifest apply to deploy phase path=$provision_path"
  ;;
helm)
  provision_path="$(public_endpoints_render_values_file)"
  run_helm_upgrade_install \
    "$PUBLIC_ENDPOINTS_HELM_RELEASE" \
    "$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE" \
    "$PUBLIC_ENDPOINTS_HELM_CHART" \
    "$PUBLIC_ENDPOINTS_HELM_CHART_VERSION" \
    "$provision_path"
  # The shared Gateway contract lives in a dedicated namespace that may not
  # exist yet during module-level provision time, so the module materializes it
  # explicitly before applying the GatewayClass/Gateway manifest.
  run_manifest_apply "$namespace_manifest_path"
  run_manifest_apply "$gateway_manifest_path"
  provision_status="applied"
  ;;
*)
  optional_module_unexpected_driver "public-endpoints" "apply"
  ;;
esac

state_file="$(write_state_file "public_endpoints_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "edge_mode=gateway_api_envoy" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "provision_status=$provision_status" \
  "namespace_manifest_path=$namespace_manifest_path" \
  "gateway_manifest_path=$gateway_manifest_path" \
  "base_domain=$PUBLIC_ENDPOINTS_BASE_DOMAIN" \
  "gateway_name=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
  "gateway_class_name=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" \
  "gateway_namespace=$PUBLIC_ENDPOINTS_NAMESPACE" \
  "controller_namespace=$PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE" \
  "listener_policy=allow_cross_namespace_routes" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints runtime state written to $state_file"
