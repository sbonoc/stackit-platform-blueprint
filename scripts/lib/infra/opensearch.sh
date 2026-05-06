#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"

# Bitnami OpenSearch chart hard-codes OPENSEARCH_USERNAME=admin in the
# StatefulSet env; any override via extraEnvVars produces a duplicate env
# entry with undefined precedence. We surface the locked value via a
# constant and forbid override on the local lane.
OPENSEARCH_LOCAL_ADMIN_USERNAME="admin"

opensearch_seed_env_defaults() {
  set_default_env OPENSEARCH_INSTANCE_NAME "marketplace-opensearch"
  set_default_env OPENSEARCH_VERSION "2.17"
  set_default_env OPENSEARCH_PLAN_NAME "stackit-opensearch-single"
  set_default_env OPENSEARCH_NAMESPACE "search"
  set_default_env OPENSEARCH_HELM_RELEASE "blueprint-opensearch"
  set_default_env OPENSEARCH_HELM_CHART "bitnami/opensearch"
  set_default_env OPENSEARCH_HELM_CHART_VERSION "$OPENSEARCH_HELM_CHART_VERSION_PIN"
  set_default_env OPENSEARCH_IMAGE_REGISTRY "$OPENSEARCH_LOCAL_IMAGE_REGISTRY"
  set_default_env OPENSEARCH_IMAGE_REPOSITORY "$OPENSEARCH_LOCAL_IMAGE_REPOSITORY"
  set_default_env OPENSEARCH_IMAGE_TAG "$OPENSEARCH_LOCAL_IMAGE_TAG"
  set_default_env OPENSEARCH_PASSWORD "admin"
}

opensearch_init_env() {
  opensearch_seed_env_defaults
  require_env_vars OPENSEARCH_INSTANCE_NAME OPENSEARCH_VERSION OPENSEARCH_PLAN_NAME
}

opensearch_password_secret_name() {
  printf '%s-auth' "$OPENSEARCH_HELM_RELEASE"
}

opensearch_stackit_placeholder_host() {
  local region
  region="${STACKIT_REGION:-${BLUEPRINT_STACKIT_REGION:-eu01}}"
  printf '%s.opensearch.%s.stackit.invalid' "$OPENSEARCH_INSTANCE_NAME" "$region"
}

opensearch_local_service_host() {
  printf '%s.%s.svc.cluster.local' "$OPENSEARCH_HELM_RELEASE" "$OPENSEARCH_NAMESPACE"
}

opensearch_local_port() {
  printf '9200'
}

opensearch_local_scheme() {
  printf 'http'
}

opensearch_host() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_host" "$(opensearch_stackit_placeholder_host)"
    return 0
  fi
  opensearch_local_service_host
}

opensearch_hosts() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_hosts" "$(opensearch_host)"
    return 0
  fi
  opensearch_local_service_host
}

opensearch_port() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_port" "443"
    return 0
  fi
  opensearch_local_port
}

opensearch_scheme() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_scheme" "https"
    return 0
  fi
  opensearch_local_scheme
}

opensearch_uri() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default \
      "opensearch_uri" \
      "https://$(opensearch_stackit_placeholder_host):443"
    return 0
  fi
  printf '%s://%s:%s' "$(opensearch_local_scheme)" "$(opensearch_local_service_host)" "$(opensearch_local_port)"
}

opensearch_dashboard_url() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_dashboard_url" "https://$(opensearch_stackit_placeholder_host)"
    return 0
  fi
  # Local lane runs the bitnami/opensearch chart with dashboards.enabled=false
  # to keep the dev footprint at ~1 GB RAM. No dashboards Pod is deployed,
  # so the contract output is intentionally empty for local.
  printf ''
}

opensearch_username() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_username" "provider-generated"
    return 0
  fi
  printf '%s' "$OPENSEARCH_LOCAL_ADMIN_USERNAME"
}

opensearch_password() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_password" "provider-generated"
    return 0
  fi
  printf '%s' "$OPENSEARCH_PASSWORD"
}

opensearch_render_values_file() {
  render_optional_module_values_file \
    "opensearch" \
    "infra/local/helm/opensearch/values.yaml" \
    "OPENSEARCH_HELM_RELEASE=$OPENSEARCH_HELM_RELEASE" \
    "OPENSEARCH_PASSWORD_SECRET_NAME=$(opensearch_password_secret_name)" \
    "OPENSEARCH_IMAGE_REGISTRY=$OPENSEARCH_IMAGE_REGISTRY" \
    "OPENSEARCH_IMAGE_REPOSITORY=$OPENSEARCH_IMAGE_REPOSITORY" \
    "OPENSEARCH_IMAGE_TAG=$OPENSEARCH_IMAGE_TAG"
}

opensearch_reconcile_runtime_secret() {
  apply_optional_module_secret_from_literals \
    "$OPENSEARCH_NAMESPACE" \
    "$(opensearch_password_secret_name)" \
    "opensearch-password=$OPENSEARCH_PASSWORD"
}

opensearch_delete_runtime_secret() {
  delete_optional_module_secret "$OPENSEARCH_NAMESPACE" "$(opensearch_password_secret_name)"
}
