#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/versions.sh"

postgres_init_env() {
  set_default_env POSTGRES_VERSION "16"
  set_default_env POSTGRES_PORT "5432"
  set_default_env POSTGRES_CONNECT_TIMEOUT_SECONDS "30"
  set_default_env POSTGRES_EXTRA_ALLOWED_CIDRS ""
  set_default_env POSTGRES_NAMESPACE "data"
  set_default_env POSTGRES_HELM_RELEASE "blueprint-postgres"
  set_default_env POSTGRES_HELM_CHART "bitnami/postgresql"
  set_default_env POSTGRES_HELM_CHART_VERSION "$POSTGRES_HELM_CHART_VERSION_PIN"

  require_env_vars POSTGRES_INSTANCE_NAME POSTGRES_DB_NAME POSTGRES_USER POSTGRES_PASSWORD

  if [[ "$POSTGRES_EXTRA_ALLOWED_CIDRS" == *"0.0.0.0/0"* ]]; then
    log_fatal "POSTGRES_EXTRA_ALLOWED_CIDRS must not include 0.0.0.0/0"
  fi
}

postgres_host() {
  local region
  region="${STACKIT_REGION:-local}"
  if is_stackit_profile; then
    printf '%s.postgresql.%s.onstackit.cloud' "$POSTGRES_INSTANCE_NAME" "$region"
    return 0
  fi
  postgres_local_service_host
}

postgres_dsn() {
  local host
  host="$(postgres_host)"
  printf 'postgresql://%s:%s@%s:%s/%s' \
    "$POSTGRES_USER" \
    "$POSTGRES_PASSWORD" \
    "$host" \
    "$POSTGRES_PORT" \
    "$POSTGRES_DB_NAME"
}

postgres_local_service_host() {
  printf '%s.%s.svc.cluster.local' "$POSTGRES_HELM_RELEASE" "$POSTGRES_NAMESPACE"
}
