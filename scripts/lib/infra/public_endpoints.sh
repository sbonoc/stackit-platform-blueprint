#!/usr/bin/env bash
set -euo pipefail

public_endpoints_init_env() {
  set_default_env PUBLIC_ENDPOINTS_BASE_DOMAIN "apps.local"
  set_default_env PUBLIC_ENDPOINTS_INGRESS_CLASS "nginx"
  set_default_env PUBLIC_ENDPOINTS_NAMESPACE "network"
  set_default_env PUBLIC_ENDPOINTS_HELM_RELEASE "blueprint-public-endpoints"
  set_default_env PUBLIC_ENDPOINTS_HELM_CHART "ingress-nginx/ingress-nginx"
  set_default_env PUBLIC_ENDPOINTS_HELM_CHART_VERSION "4.13.3"

  require_env_vars PUBLIC_ENDPOINTS_BASE_DOMAIN
}
