#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"

postgres_init_env() {
  set_default_env POSTGRES_VERSION "16"
  set_default_env POSTGRES_PORT "5432"
  set_default_env POSTGRES_CONNECT_TIMEOUT_SECONDS "30"
  set_default_env POSTGRES_EXTRA_ALLOWED_CIDRS ""
  set_default_env POSTGRES_NAMESPACE "data"
  set_default_env POSTGRES_HELM_RELEASE "blueprint-postgres"
  set_default_env POSTGRES_HELM_CHART "bitnami/postgresql"
  set_default_env POSTGRES_HELM_CHART_VERSION "$POSTGRES_HELM_CHART_VERSION_PIN"
  set_default_env POSTGRES_IMAGE_REGISTRY "$POSTGRES_LOCAL_IMAGE_REGISTRY"
  set_default_env POSTGRES_IMAGE_REPOSITORY "$POSTGRES_LOCAL_IMAGE_REPOSITORY"
  set_default_env POSTGRES_IMAGE_TAG "$POSTGRES_LOCAL_IMAGE_TAG"

  require_env_vars POSTGRES_INSTANCE_NAME POSTGRES_DB_NAME POSTGRES_USER POSTGRES_PASSWORD

  if [[ "$POSTGRES_EXTRA_ALLOWED_CIDRS" == *"0.0.0.0/0"* ]]; then
    log_fatal "POSTGRES_EXTRA_ALLOWED_CIDRS must not include 0.0.0.0/0"
  fi
}

postgres_stackit_placeholder_host() {
  local region
  region="${STACKIT_REGION:-local}"
  printf '%s.postgresql.%s.onstackit.cloud' "$POSTGRES_INSTANCE_NAME" "$region"
}

postgres_username() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "postgres_username" "$POSTGRES_USER"
    return 0
  fi
  printf '%s' "$POSTGRES_USER"
}

postgres_password() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "postgres_password" "provider-generated"
    return 0
  fi
  printf '%s' "$POSTGRES_PASSWORD"
}

postgres_port() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "postgres_port" "$POSTGRES_PORT"
    return 0
  fi
  printf '%s' "$POSTGRES_PORT"
}

postgres_database() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "postgres_database" "$POSTGRES_DB_NAME"
    return 0
  fi
  printf '%s' "$POSTGRES_DB_NAME"
}

postgres_host() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "postgres_host" "$(postgres_stackit_placeholder_host)"
    return 0
  fi
  postgres_local_service_host
}

postgres_dsn() {
  local host
  local username
  local password
  local port
  local database
  host="$(postgres_host)"
  username="$(postgres_username)"
  password="$(postgres_password)"
  port="$(postgres_port)"
  database="$(postgres_database)"
  printf 'postgresql://%s:%s@%s:%s/%s' \
    "$username" \
    "$password" \
    "$host" \
    "$port" \
    "$database"
}

postgres_local_service_host() {
  printf '%s.%s.svc.cluster.local' "$POSTGRES_HELM_RELEASE" "$POSTGRES_NAMESPACE"
}

postgres_credential_secret_name() {
  printf '%s-auth' "$POSTGRES_HELM_RELEASE"
}

postgres_reconcile_runtime_secret() {
  apply_optional_module_secret_from_literals \
    "$POSTGRES_NAMESPACE" \
    "$(postgres_credential_secret_name)" \
    "password=$POSTGRES_PASSWORD"
}

postgres_delete_runtime_secret() {
  delete_optional_module_secret "$POSTGRES_NAMESPACE" "$(postgres_credential_secret_name)"
}

postgres_render_values_file() {
  render_optional_module_values_file \
    "postgres" \
    "infra/local/helm/postgres/values.yaml" \
    "POSTGRES_HELM_RELEASE=$POSTGRES_HELM_RELEASE" \
    "POSTGRES_CREDENTIAL_SECRET_NAME=$(postgres_credential_secret_name)" \
    "POSTGRES_DB_NAME=$POSTGRES_DB_NAME" \
    "POSTGRES_IMAGE_REGISTRY=$POSTGRES_IMAGE_REGISTRY" \
    "POSTGRES_IMAGE_REPOSITORY=$POSTGRES_IMAGE_REPOSITORY" \
    "POSTGRES_IMAGE_TAG=$POSTGRES_IMAGE_TAG"
}
