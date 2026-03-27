#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"

rabbitmq_seed_env_defaults() {
  set_default_env RABBITMQ_INSTANCE_NAME "marketplace-rabbitmq"
  set_default_env RABBITMQ_USERNAME "marketplace"
  set_default_env RABBITMQ_PASSWORD "marketplace-password"
  set_default_env RABBITMQ_PORT "5672"
  set_default_env RABBITMQ_VERSION "3.13"
  set_default_env RABBITMQ_PLAN_NAME "stackit-rabbitmq-1.2.10-replica"
  set_default_env RABBITMQ_NAMESPACE "messaging"
  set_default_env RABBITMQ_HELM_RELEASE "blueprint-rabbitmq"
  set_default_env RABBITMQ_HELM_CHART "bitnami/rabbitmq"
  set_default_env RABBITMQ_HELM_CHART_VERSION "$RABBITMQ_HELM_CHART_VERSION_PIN"
  set_default_env RABBITMQ_IMAGE_REGISTRY "$RABBITMQ_LOCAL_IMAGE_REGISTRY"
  set_default_env RABBITMQ_IMAGE_REPOSITORY "$RABBITMQ_LOCAL_IMAGE_REPOSITORY"
  set_default_env RABBITMQ_IMAGE_TAG "$RABBITMQ_LOCAL_IMAGE_TAG"
}

rabbitmq_init_env() {
  rabbitmq_seed_env_defaults
  require_env_vars RABBITMQ_INSTANCE_NAME
}

rabbitmq_password_secret_name() {
  printf '%s-auth' "$RABBITMQ_HELM_RELEASE"
}

rabbitmq_local_service_host() {
  printf '%s.%s.svc.cluster.local' "$RABBITMQ_HELM_RELEASE" "$RABBITMQ_NAMESPACE"
}

rabbitmq_stackit_placeholder_host() {
  local region
  region="${STACKIT_REGION:-${BLUEPRINT_STACKIT_REGION:-eu01}}"
  printf '%s.rabbitmq.%s.stackit.invalid' "$RABBITMQ_INSTANCE_NAME" "$region"
}

rabbitmq_username() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "rabbitmq_username" "provider-generated"
    return 0
  fi
  printf '%s' "$RABBITMQ_USERNAME"
}

rabbitmq_password() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "rabbitmq_password" "provider-generated"
    return 0
  fi
  printf '%s' "$RABBITMQ_PASSWORD"
}

rabbitmq_port() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "rabbitmq_port" "$RABBITMQ_PORT"
    return 0
  fi
  printf '%s' "$RABBITMQ_PORT"
}

rabbitmq_host() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "rabbitmq_host" "$(rabbitmq_stackit_placeholder_host)"
    return 0
  fi
  rabbitmq_local_service_host
}

rabbitmq_uri() {
  if is_stackit_profile; then
    # STACKIT RabbitMQ credentials are provider-generated, so dry-run mode uses
    # a stable placeholder until terraform outputs are available after apply.
    stackit_foundation_output_value_or_default \
      "rabbitmq_uri" \
      "amqp://provider-generated:provider-generated@$(rabbitmq_stackit_placeholder_host):$RABBITMQ_PORT"
    return 0
  fi

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
    "RABBITMQ_PASSWORD_SECRET_NAME=$(rabbitmq_password_secret_name)" \
    "RABBITMQ_IMAGE_REGISTRY=$RABBITMQ_IMAGE_REGISTRY" \
    "RABBITMQ_IMAGE_REPOSITORY=$RABBITMQ_IMAGE_REPOSITORY" \
    "RABBITMQ_IMAGE_TAG=$RABBITMQ_IMAGE_TAG"
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
