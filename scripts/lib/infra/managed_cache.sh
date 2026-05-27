#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"

managed_cache_seed_env_defaults() {
  set_default_env MANAGED_CACHE_NAMESPACE "managed-cache"
  set_default_env MANAGED_CACHE_HELM_RELEASE "blueprint-managed-cache"
  set_default_env MANAGED_CACHE_HELM_CHART "bitnami/redis"
  set_default_env MANAGED_CACHE_PORT "6379"
  set_default_env MANAGED_CACHE_PASSWORD "managed-cache-password"
}

managed_cache_init_env() {
  managed_cache_seed_env_defaults
}

managed_cache_local_service_host() {
  printf '%s-master.%s.svc.cluster.local' "$MANAGED_CACHE_HELM_RELEASE" "$MANAGED_CACHE_NAMESPACE"
}

managed_cache_host() {
  echo "not implemented"
}

managed_cache_port() {
  echo "not implemented"
}

managed_cache_username() {
  echo "not implemented"
}

managed_cache_password() {
  echo "not implemented"
}

managed_cache_uri() {
  echo "not implemented"
}
