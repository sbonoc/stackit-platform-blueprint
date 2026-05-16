#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"

secrets_manager_init_env() {
  set_default_env SECRETS_MANAGER_INSTANCE_NAME "marketplace-secrets"
  set_default_env SECRETS_MANAGER_K8S_NAMESPACE "secrets-manager"

  require_env_vars SECRETS_MANAGER_INSTANCE_NAME
}

secrets_manager_endpoint() {
  printf 'https://secrets.%s.onstackit.cloud/%s' "${STACKIT_REGION:-eu01}" "$SECRETS_MANAGER_INSTANCE_NAME"
}

secrets_manager_namespace() {
  printf '%s' "$SECRETS_MANAGER_INSTANCE_NAME"
}

secrets_manager_auth_method_details() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "secrets_manager_username" "provider-generated"
    return 0
  fi
  printf 'provider-generated'
}

secrets_manager_secret_name() {
  printf 'blueprint-secrets-manager-auth'
}

secrets_manager_reconcile_runtime_secret() {
  apply_optional_module_secret_from_literals \
    "${SECRETS_MANAGER_K8S_NAMESPACE:-secrets-manager}" \
    "$(secrets_manager_secret_name)" \
    "username=$(secrets_manager_auth_method_details)" \
    "password=$(stackit_foundation_output_value_or_default "secrets_manager_password" "provider-generated")"
}

secrets_manager_delete_runtime_secret() {
  delete_optional_module_secret "${SECRETS_MANAGER_K8S_NAMESPACE:-secrets-manager}" "$(secrets_manager_secret_name)"
}
