#!/usr/bin/env bash
set -euo pipefail

identity_aware_proxy_init_env() {
  set_default_env IAP_UPSTREAM_URL "http://catalog.apps.svc.cluster.local:8080"
  set_default_env IAP_PUBLIC_HOST "iap.local"
  set_default_env IAP_NAMESPACE "security"
  set_default_env IAP_HELM_RELEASE "blueprint-iap"
  set_default_env IAP_HELM_CHART "oauth2-proxy/oauth2-proxy"
  set_default_env IAP_HELM_CHART_VERSION "7.12.17"

  require_env_vars IAP_UPSTREAM_URL KEYCLOAK_ISSUER_URL KEYCLOAK_CLIENT_ID KEYCLOAK_CLIENT_SECRET
}

identity_aware_proxy_public_url() {
  if [[ "$IAP_PUBLIC_HOST" =~ ^https?:// ]]; then
    printf '%s' "$IAP_PUBLIC_HOST"
    return 0
  fi
  printf 'https://%s' "$IAP_PUBLIC_HOST"
}
