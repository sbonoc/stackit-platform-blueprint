#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/identity_aware_proxy.sh"

start_script_metric_trap "infra_identity_aware_proxy_apply"

if ! is_module_enabled identity-aware-proxy; then
  log_info "IDENTITY_AWARE_PROXY_ENABLED=false; skipping identity-aware-proxy apply"
  exit 0
fi

identity_aware_proxy_init_env
if ! state_file_exists identity_aware_proxy_plan; then
  log_fatal "missing identity-aware-proxy plan artifact; run infra-identity-aware-proxy-plan first"
fi

provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="argocd_optional_manifest"
  provision_path="$(argocd_optional_manifest "identity-aware-proxy")"
  run_manifest_apply "$provision_path"
elif is_local_profile; then
  provision_driver="helm"
  provision_path="$(local_module_helm_values_file "identity-aware-proxy")"
  run_helm_upgrade_install \
    "$IAP_HELM_RELEASE" \
    "$IAP_NAMESPACE" \
    "$IAP_HELM_CHART" \
    "$IAP_HELM_CHART_VERSION" \
    "$provision_path"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "identity_aware_proxy_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "public_url=$(identity_aware_proxy_public_url)" \
  "upstream_url=$IAP_UPSTREAM_URL" \
  "keycloak_issuer=$KEYCLOAK_ISSUER_URL" \
  "keycloak_client_id=$KEYCLOAK_CLIENT_ID" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "identity-aware-proxy runtime state written to $state_file"
