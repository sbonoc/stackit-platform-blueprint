#!/usr/bin/env bash
set -euo pipefail

secrets_manager_init_env() {
  set_default_env SECRETS_MANAGER_INSTANCE_NAME "marketplace-secrets"

  require_env_vars SECRETS_MANAGER_INSTANCE_NAME
}

secrets_manager_endpoint() {
  printf 'https://secrets.%s.onstackit.cloud/%s' "${STACKIT_REGION:-eu01}" "$SECRETS_MANAGER_INSTANCE_NAME"
}
