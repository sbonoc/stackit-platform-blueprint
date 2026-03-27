#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/versions.sh"

public_endpoints_seed_env_defaults() {
  set_default_env PUBLIC_ENDPOINTS_BASE_DOMAIN "apps.local"
  set_default_env PUBLIC_ENDPOINTS_INGRESS_CLASS "nginx"
  set_default_env PUBLIC_ENDPOINTS_NAMESPACE "network"
  set_default_env PUBLIC_ENDPOINTS_HELM_RELEASE "blueprint-public-endpoints"
  set_default_env PUBLIC_ENDPOINTS_HELM_CHART "ingress-nginx/ingress-nginx"
  set_default_env PUBLIC_ENDPOINTS_HELM_CHART_VERSION "$PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN"
}

public_endpoints_init_env() {
  public_endpoints_seed_env_defaults
  require_env_vars PUBLIC_ENDPOINTS_BASE_DOMAIN
}

public_endpoints_render_values_file() {
  render_optional_module_values_file \
    "public-endpoints" \
    "infra/local/helm/public-endpoints/values.yaml" \
    "PUBLIC_ENDPOINTS_INGRESS_CLASS=$PUBLIC_ENDPOINTS_INGRESS_CLASS"
}
