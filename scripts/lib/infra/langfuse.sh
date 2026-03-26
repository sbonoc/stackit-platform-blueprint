#!/usr/bin/env bash
set -euo pipefail

langfuse_init_env() {
  set_default_env LANGFUSE_RETENTION_DAYS "30"
  set_default_env LANGFUSE_BASE_PATH "/"

  require_env_vars \
    LANGFUSE_PUBLIC_DOMAIN \
    LANGFUSE_OIDC_ISSUER_URL \
    LANGFUSE_OIDC_CLIENT_ID \
    LANGFUSE_OIDC_CLIENT_SECRET \
    LANGFUSE_DATABASE_URL \
    LANGFUSE_SALT \
    LANGFUSE_ENCRYPTION_KEY \
    LANGFUSE_NEXTAUTH_SECRET
}

langfuse_public_url() {
  if [[ "$LANGFUSE_PUBLIC_DOMAIN" =~ ^https?:// ]]; then
    printf '%s' "$LANGFUSE_PUBLIC_DOMAIN"
    return 0
  fi
  printf 'https://%s' "$LANGFUSE_PUBLIC_DOMAIN"
}
