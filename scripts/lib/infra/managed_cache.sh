#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"

managed_cache_seed_env_defaults() {
  set_default_env MANAGED_CACHE_INSTANCE_NAME "marketplace-managed-cache"
  set_default_env MANAGED_CACHE_PASSWORD "managed-cache-password"
  set_default_env MANAGED_CACHE_PORT "6379"
  set_default_env MANAGED_CACHE_NAMESPACE "managed-cache"
  set_default_env MANAGED_CACHE_HELM_RELEASE "blueprint-managed-cache"
  set_default_env MANAGED_CACHE_HELM_CHART "bitnami/redis"
  set_default_env MANAGED_CACHE_HELM_CHART_VERSION "$MANAGED_CACHE_REDIS_HELM_CHART_VERSION_PIN"
}

managed_cache_init_env() {
  managed_cache_seed_env_defaults
  require_env_vars MANAGED_CACHE_INSTANCE_NAME
}

managed_cache_local_service_host() {
  printf '%s.%s.svc.cluster.local' "$MANAGED_CACHE_HELM_RELEASE" "$MANAGED_CACHE_NAMESPACE"
}

managed_cache_host() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "managed_cache_host" "provider-generated"
    return 0
  fi
  managed_cache_local_service_host
}

managed_cache_port() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "managed_cache_port" "$MANAGED_CACHE_PORT"
    return 0
  fi
  printf '%s' "$MANAGED_CACHE_PORT"
}

managed_cache_username() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "managed_cache_username" "provider-generated"
    return 0
  fi
  printf ''
}

managed_cache_password() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "managed_cache_password" "provider-generated"
    return 0
  fi
  printf '%s' "$MANAGED_CACHE_PASSWORD"
}

managed_cache_uri() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "managed_cache_uri" "redis://not-yet-provisioned"
    return 0
  fi
  local host port password
  host="$(managed_cache_local_service_host)"
  port="$MANAGED_CACHE_PORT"
  password="$MANAGED_CACHE_PASSWORD"
  printf 'redis://:%s@%s:%s/0' "$password" "$host" "$port"
}
