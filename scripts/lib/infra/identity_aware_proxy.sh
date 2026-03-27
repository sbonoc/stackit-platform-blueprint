#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/versions.sh"

identity_aware_proxy_seed_env_defaults() {
  set_default_env IAP_UPSTREAM_URL "http://catalog.apps.svc.cluster.local:8080"
  set_default_env IAP_PUBLIC_HOST "iap.local"
  set_default_env IAP_NAMESPACE "security"
  set_default_env IAP_HELM_RELEASE "blueprint-iap"
  set_default_env IAP_HELM_CHART "oauth2-proxy/oauth2-proxy"
  set_default_env IAP_HELM_CHART_VERSION "$IAP_HELM_CHART_VERSION_PIN"
  set_default_env IAP_IMAGE_REGISTRY "$IAP_LOCAL_IMAGE_REGISTRY"
  set_default_env IAP_IMAGE_REPOSITORY "$IAP_LOCAL_IMAGE_REPOSITORY"
  set_default_env IAP_IMAGE_TAG "$IAP_LOCAL_IMAGE_TAG"
  set_default_env PUBLIC_ENDPOINTS_NAMESPACE "network"
  set_default_env PUBLIC_ENDPOINTS_GATEWAY_NAME "public-endpoints"
}

identity_aware_proxy_validate_cookie_secret() {
  local secret_length
  secret_length="${#IAP_COOKIE_SECRET}"
  case "$secret_length" in
  16 | 24 | 32)
    log_metric "identity_aware_proxy_cookie_secret_validation_total" "1" "status=valid length=$secret_length"
    ;;
  *)
    log_metric "identity_aware_proxy_cookie_secret_validation_total" "1" "status=invalid length=$secret_length"
    log_fatal "IAP_COOKIE_SECRET must be a raw 16, 24, or 32 byte string; got length=$secret_length"
    ;;
  esac
}

identity_aware_proxy_init_env() {
  identity_aware_proxy_seed_env_defaults
  require_env_vars IAP_UPSTREAM_URL KEYCLOAK_ISSUER_URL KEYCLOAK_CLIENT_ID KEYCLOAK_CLIENT_SECRET IAP_COOKIE_SECRET
  identity_aware_proxy_validate_cookie_secret
}

identity_aware_proxy_public_url() {
  if [[ "$IAP_PUBLIC_HOST" =~ ^https?:// ]]; then
    printf '%s' "$IAP_PUBLIC_HOST"
    return 0
  fi
  printf 'https://%s' "$IAP_PUBLIC_HOST"
}

identity_aware_proxy_public_host() {
  local host="$IAP_PUBLIC_HOST"
  host="${host#http://}"
  host="${host#https://}"
  printf '%s' "${host%%/*}"
}

identity_aware_proxy_redirect_url() {
  local public_url
  public_url="$(identity_aware_proxy_public_url)"
  printf '%s/oauth2/callback' "${public_url%/}"
}

identity_aware_proxy_config_secret_name() {
  printf '%s-config' "$IAP_HELM_RELEASE"
}

identity_aware_proxy_render_values_file() {
  render_optional_module_values_file \
    "identity-aware-proxy" \
    "infra/local/helm/identity-aware-proxy/values.yaml" \
    "IAP_CONFIG_SECRET_NAME=$(identity_aware_proxy_config_secret_name)" \
    "KEYCLOAK_ISSUER_URL=$KEYCLOAK_ISSUER_URL" \
    "IAP_UPSTREAM_URL=$IAP_UPSTREAM_URL" \
    "PUBLIC_ENDPOINTS_NAMESPACE=$PUBLIC_ENDPOINTS_NAMESPACE" \
    "PUBLIC_ENDPOINTS_GATEWAY_NAME=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
    "IAP_PUBLIC_HOST=$(identity_aware_proxy_public_host)" \
    "IAP_REDIRECT_URL=$(identity_aware_proxy_redirect_url)" \
    "IAP_IMAGE_REGISTRY=$IAP_IMAGE_REGISTRY" \
    "IAP_IMAGE_REPOSITORY=$IAP_IMAGE_REPOSITORY" \
    "IAP_IMAGE_TAG=$IAP_IMAGE_TAG"
}

identity_aware_proxy_reconcile_runtime_secret() {
  apply_optional_module_secret_from_literals \
    "$IAP_NAMESPACE" \
    "$(identity_aware_proxy_config_secret_name)" \
    "client-id=$KEYCLOAK_CLIENT_ID" \
    "client-secret=$KEYCLOAK_CLIENT_SECRET" \
    "cookie-secret=$IAP_COOKIE_SECRET"
}

identity_aware_proxy_delete_runtime_secret() {
  delete_optional_module_secret "$IAP_NAMESPACE" "$(identity_aware_proxy_config_secret_name)"
}
