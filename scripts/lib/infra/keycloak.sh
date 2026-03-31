#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"

keycloak_seed_env_defaults() {
  local default_public_host=""
  local local_postgres_instance="${POSTGRES_INSTANCE_NAME:-blueprint-postgres}"

  set_default_env KEYCLOAK_NAMESPACE "security"
  set_default_env KEYCLOAK_HELM_RELEASE "keycloak"
  set_default_env KEYCLOAK_HELM_CHART "codecentric/keycloakx"
  set_default_env KEYCLOAK_HELM_CHART_VERSION "$KEYCLOAK_HELM_CHART_VERSION_PIN"
  set_default_env KEYCLOAK_IMAGE_TAG "$KEYCLOAK_IMAGE_TAG_PIN"
  set_default_env KEYCLOAK_ADMIN_USERNAME "admin"
  default_public_host="${KEYCLOAK_PUBLIC_HOST:-}"
  if [[ -z "$default_public_host" && -n "${PUBLIC_ENDPOINTS_BASE_DOMAIN:-}" ]]; then
    default_public_host="auth.${PUBLIC_ENDPOINTS_BASE_DOMAIN}"
  fi
  if [[ -z "$default_public_host" ]]; then
    default_public_host="auth.example.invalid"
  fi
  set_default_env KEYCLOAK_PUBLIC_HOST "$default_public_host"
  set_default_env KEYCLOAK_ACME_EMAIL "noreply@${KEYCLOAK_PUBLIC_HOST}"
  set_default_env KEYCLOAK_ACME_SERVER "https://acme-v02.api.letsencrypt.org/directory"
  set_default_env KEYCLOAK_GATEWAY_NAME "keycloak"
  set_default_env KEYCLOAK_GATEWAY_CLASS_NAME "public-endpoints"
  set_default_env KEYCLOAK_TLS_SECRET_NAME "keycloak-tls"
  set_default_env KEYCLOAK_REALM_IAP "iap"
  set_default_env KEYCLOAK_REALM_WORKFLOWS "workflows"
  set_default_env KEYCLOAK_REALM_LANGFUSE "langfuse"
  set_default_env KEYCLOAK_ISSUER_URL "https://${KEYCLOAK_PUBLIC_HOST}/realms/${KEYCLOAK_REALM_IAP}"
  set_default_env STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL "https://${KEYCLOAK_PUBLIC_HOST}/realms/${KEYCLOAK_REALM_WORKFLOWS}/.well-known/openid-configuration"
  set_default_env LANGFUSE_OIDC_ISSUER_URL "https://${KEYCLOAK_PUBLIC_HOST}/realms/${KEYCLOAK_REALM_LANGFUSE}"
  set_default_env KEYCLOAK_DATABASE_PORT "5432"
  set_default_env KEYCLOAK_DATABASE_NAME "keycloak"
  set_default_env KEYCLOAK_DATABASE_USERNAME "keycloak"

  if is_stackit_profile; then
    set_default_env KEYCLOAK_DATABASE_MODE "stackit-dedicated"
    set_default_env KEYCLOAK_DATABASE_HOST "keycloak-postgres.stackit.internal"
  else
    set_default_env KEYCLOAK_DATABASE_MODE "local-shared"
    set_default_env KEYCLOAK_DATABASE_HOST "${local_postgres_instance}.data.svc.cluster.local"
  fi
}
