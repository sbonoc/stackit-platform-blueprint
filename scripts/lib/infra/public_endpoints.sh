#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"

public_endpoints_seed_env_defaults() {
  set_default_env PUBLIC_ENDPOINTS_BASE_DOMAIN "apps.local"
  set_default_env PUBLIC_ENDPOINTS_NAMESPACE "network"
  set_default_env PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE "envoy-gateway-system"
  set_default_env PUBLIC_ENDPOINTS_GATEWAY_NAME "public-endpoints"
  set_default_env PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME "public-endpoints"
  set_default_env PUBLIC_ENDPOINTS_HELM_RELEASE "blueprint-public-endpoints"
  set_default_env PUBLIC_ENDPOINTS_HELM_CHART "oci://docker.io/envoyproxy/gateway-helm"
  set_default_env PUBLIC_ENDPOINTS_HELM_CHART_VERSION "$PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN"
}

public_endpoints_init_env() {
  public_endpoints_seed_env_defaults
  require_env_vars PUBLIC_ENDPOINTS_BASE_DOMAIN
}

public_endpoints_gateway_manifest_content() {
  render_bootstrap_template_content \
    "infra" \
    "infra/gateway/public-endpoints.yaml.tmpl" \
    "PUBLIC_ENDPOINTS_NAMESPACE=$PUBLIC_ENDPOINTS_NAMESPACE" \
    "PUBLIC_ENDPOINTS_GATEWAY_NAME=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
    "PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME"
}

public_endpoints_render_gateway_manifest() {
  local target_path
  target_path="$(public_endpoints_gateway_manifest_file)"
  ensure_dir "$(dirname "$target_path")"
  printf '%s' "$(public_endpoints_gateway_manifest_content)" >"$target_path"
  # This helper is used in command substitutions, so stdout must stay reserved
  # for the rendered artifact path and diagnostics go to stderr.
  log_metric \
    "public_endpoints_gateway_manifest_render_total" \
    "1" \
    "target=$target_path namespace=$PUBLIC_ENDPOINTS_NAMESPACE gateway=$PUBLIC_ENDPOINTS_GATEWAY_NAME" >&2
  log_info "rendered public-endpoints gateway manifest: $target_path" >&2
  printf '%s\n' "$target_path"
}

public_endpoints_render_values_file() {
  render_optional_module_values_file \
    "public-endpoints" \
    "infra/local/helm/public-endpoints/values.yaml"
}
