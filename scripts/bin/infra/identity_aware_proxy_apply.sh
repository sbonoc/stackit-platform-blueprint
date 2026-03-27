#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"
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

resolve_optional_module_execution "identity-aware-proxy" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
argocd_application_chart)
  identity_aware_proxy_reconcile_runtime_secret
  run_manifest_apply "$provision_path"
  ;;
helm)
  provision_path="$(identity_aware_proxy_render_values_file)"
  identity_aware_proxy_reconcile_runtime_secret
  run_helm_upgrade_install \
    "$IAP_HELM_RELEASE" \
    "$IAP_NAMESPACE" \
    "$IAP_HELM_CHART" \
    "$IAP_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "identity-aware-proxy" "apply"
  ;;
esac

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
