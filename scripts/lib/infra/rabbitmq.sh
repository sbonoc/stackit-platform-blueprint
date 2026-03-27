#!/usr/bin/env bash
set -euo pipefail

rabbitmq_seed_env_defaults() {
  set_default_env RABBITMQ_INSTANCE_NAME "marketplace-rabbitmq"
  set_default_env RABBITMQ_USERNAME "marketplace"
  set_default_env RABBITMQ_PASSWORD "marketplace-password"
  set_default_env RABBITMQ_PORT "5672"
  set_default_env RABBITMQ_NAMESPACE "messaging"
  set_default_env RABBITMQ_HELM_RELEASE "blueprint-rabbitmq"
  set_default_env RABBITMQ_HELM_CHART "bitnami/rabbitmq"
  set_default_env RABBITMQ_HELM_CHART_VERSION "16.0.14"
}

rabbitmq_init_env() {
  rabbitmq_seed_env_defaults
  require_env_vars RABBITMQ_INSTANCE_NAME RABBITMQ_USERNAME RABBITMQ_PASSWORD
}

rabbitmq_password_secret_name() {
  printf '%s-auth' "$RABBITMQ_HELM_RELEASE"
}

rabbitmq_host() {
  printf '%s.%s.svc.cluster.local' "$RABBITMQ_HELM_RELEASE" "$RABBITMQ_NAMESPACE"
}

rabbitmq_uri() {
  local host
  host="$(rabbitmq_host)"
  printf 'amqp://%s:%s@%s:%s' "$RABBITMQ_USERNAME" "$RABBITMQ_PASSWORD" "$host" "$RABBITMQ_PORT"
}

rabbitmq_render_values_file() {
  render_optional_module_values_file \
    "rabbitmq" \
    "infra/local/helm/rabbitmq/values.yaml" \
    "RABBITMQ_HELM_RELEASE=$RABBITMQ_HELM_RELEASE" \
    "RABBITMQ_USERNAME=$RABBITMQ_USERNAME" \
    "RABBITMQ_PASSWORD_SECRET_NAME=$(rabbitmq_password_secret_name)"
}

rabbitmq_reconcile_runtime_secret() {
  apply_optional_module_secret_from_literals \
    "$RABBITMQ_NAMESPACE" \
    "$(rabbitmq_password_secret_name)" \
    "rabbitmq-password=$RABBITMQ_PASSWORD"
}

rabbitmq_delete_runtime_secret() {
  delete_optional_module_secret "$RABBITMQ_NAMESPACE" "$(rabbitmq_password_secret_name)"
}
