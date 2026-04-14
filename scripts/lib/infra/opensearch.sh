#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"

opensearch_init_env() {
  set_default_env OPENSEARCH_INSTANCE_NAME "marketplace-opensearch"
  set_default_env OPENSEARCH_VERSION "2.17"
  set_default_env OPENSEARCH_PLAN_NAME "stackit-opensearch-single"
  require_env_vars OPENSEARCH_INSTANCE_NAME OPENSEARCH_VERSION OPENSEARCH_PLAN_NAME
}

opensearch_stackit_placeholder_host() {
  local region
  region="${STACKIT_REGION:-${BLUEPRINT_STACKIT_REGION:-eu01}}"
  printf '%s.opensearch.%s.stackit.invalid' "$OPENSEARCH_INSTANCE_NAME" "$region"
}

opensearch_host() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_host" "$(opensearch_stackit_placeholder_host)"
    return 0
  fi
  printf '%s' "$(opensearch_stackit_placeholder_host)"
}

opensearch_hosts() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_hosts" "$(opensearch_host)"
    return 0
  fi
  printf '%s' "$(opensearch_host)"
}

opensearch_port() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_port" "443"
    return 0
  fi
  printf '%s' "443"
}

opensearch_scheme() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_scheme" "https"
    return 0
  fi
  printf '%s' "https"
}

opensearch_uri() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default \
      "opensearch_uri" \
      "https://provider-generated:provider-generated@$(opensearch_stackit_placeholder_host):443"
    return 0
  fi
  printf 'https://provider-generated:provider-generated@%s:%s' "$(opensearch_host)" "$(opensearch_port)"
}

opensearch_dashboard_url() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_dashboard_url" "https://$(opensearch_stackit_placeholder_host)"
    return 0
  fi
  printf 'https://%s' "$(opensearch_host)"
}

opensearch_username() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_username" "provider-generated"
    return 0
  fi
  printf '%s' "provider-generated"
}

opensearch_password() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "opensearch_password" "provider-generated"
    return 0
  fi
  printf '%s' "provider-generated"
}
