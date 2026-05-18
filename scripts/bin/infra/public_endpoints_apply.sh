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

# NFR-SEC-008: Warn when KMS module is not enabled for stackit-stage/prod profiles.
# TLS Secret and ACME account key will not be encrypted at rest without KMS.
if [[ "$BLUEPRINT_PROFILE" == "stackit-stage" || "$BLUEPRINT_PROFILE" == "stackit-prod" ]]; then
  if ! is_module_enabled kms; then
    log_warn "KMS module is not enabled for $BLUEPRINT_PROFILE — TLS Secret and ACME account key will NOT be encrypted at rest; enable the KMS module to protect these secrets (NFR-SEC-008)"
  fi
fi

resolve_optional_module_execution "public-endpoints" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
namespace_manifest_path="$(public_endpoints_render_namespace_manifest)"
gateway_manifest_path="$(public_endpoints_render_gateway_manifest)"
issuer_manifest_path=""
certificate_manifest_path=""
network_policy_manifest_path=""
provision_status="applied"
case "$provision_driver" in
argocd_application_chart)
  # ArgoCD-backed fallback modules are applied during deploy after the core
  # runtime bootstraps the ArgoCD CRDs and controller into the cluster.
  provision_status="deferred_to_deploy"
  issuer_manifest_path="$(public_endpoints_render_issuer_manifest)"
  certificate_manifest_path="$(public_endpoints_render_certificate_manifest)"
  network_policy_manifest_path="$(public_endpoints_render_network_policy_manifests)"
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
  issuer_manifest_path="$(public_endpoints_render_issuer_manifest)"
  certificate_manifest_path="$(public_endpoints_render_certificate_manifest)"
  network_policy_manifest_path="$(public_endpoints_render_network_policy_manifests)"
  run_manifest_apply "$issuer_manifest_path"
  run_manifest_apply "$certificate_manifest_path"
  run_manifest_apply "$network_policy_manifest_path"
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
  "cluster_issuer_name=$PUBLIC_ENDPOINTS_CLUSTER_ISSUER_NAME" \
  "cluster_issuer_type=$(public_endpoints_issuer_type)" \
  "tls_secret_name=$PUBLIC_ENDPOINTS_GATEWAY_TLS_SECRET_NAME" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints runtime state written to $state_file"
