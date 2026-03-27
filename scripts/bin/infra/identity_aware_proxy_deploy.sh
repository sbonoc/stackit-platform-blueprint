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

start_script_metric_trap "infra_identity_aware_proxy_deploy"

if ! is_module_enabled identity-aware-proxy; then
  log_info "IDENTITY_AWARE_PROXY_ENABLED=false; skipping identity-aware-proxy deploy"
  exit 0
fi

identity_aware_proxy_init_env
if ! state_file_exists identity_aware_proxy_runtime; then
  log_fatal "missing identity-aware-proxy runtime artifact; run infra-identity-aware-proxy-apply first"
fi

resolve_optional_module_execution "identity-aware-proxy" "deploy"
deploy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
deploy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
deploy_status="already_applied"
case "$deploy_driver" in
argocd_application_chart)
  identity_aware_proxy_reconcile_runtime_secret
  run_manifest_apply "$deploy_path"
  deploy_status="applied_via_argocd_manifest"
  ;;
helm)
  # Local Helm-backed IAP already installs the protected route during apply.
  :
  ;;
*)
  optional_module_unexpected_driver "identity-aware-proxy" "deploy"
  ;;
esac

state_file="$(write_state_file "identity_aware_proxy_deploy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "deploy_driver=$deploy_driver" \
  "deploy_path=$deploy_path" \
  "deploy_status=$deploy_status" \
  "public_host=$(identity_aware_proxy_public_host)" \
  "public_url=$(identity_aware_proxy_public_url)" \
  "gateway_name=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
  "gateway_namespace=$PUBLIC_ENDPOINTS_NAMESPACE" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "identity-aware-proxy deploy state written to $state_file"
