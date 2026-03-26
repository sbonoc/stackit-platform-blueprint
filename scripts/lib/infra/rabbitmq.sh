#!/usr/bin/env bash
set -euo pipefail

rabbitmq_init_env() {
  set_default_env RABBITMQ_INSTANCE_NAME "marketplace-rabbitmq"
  set_default_env RABBITMQ_USERNAME "marketplace"
  set_default_env RABBITMQ_PASSWORD "marketplace-password"
  set_default_env RABBITMQ_PORT "5672"
  set_default_env RABBITMQ_NAMESPACE "messaging"
  set_default_env RABBITMQ_HELM_RELEASE "blueprint-rabbitmq"
  set_default_env RABBITMQ_HELM_CHART "bitnami/rabbitmq"
  set_default_env RABBITMQ_HELM_CHART_VERSION "15.6.2"

  require_env_vars RABBITMQ_INSTANCE_NAME RABBITMQ_USERNAME RABBITMQ_PASSWORD
}

rabbitmq_host() {
  if is_stackit_profile; then
    printf '%s.rabbitmq.%s.onstackit.cloud' "$RABBITMQ_INSTANCE_NAME" "${STACKIT_REGION:-eu01}"
    return 0
  fi
  printf '%s.%s.svc.cluster.local' "$RABBITMQ_HELM_RELEASE" "$RABBITMQ_NAMESPACE"
}

rabbitmq_uri() {
  local host
  host="$(rabbitmq_host)"
  printf 'amqp://%s:%s@%s:%s' "$RABBITMQ_USERNAME" "$RABBITMQ_PASSWORD" "$host" "$RABBITMQ_PORT"
}
