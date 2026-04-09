#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/identity_aware_proxy.sh"

start_script_metric_trap "infra_identity_aware_proxy_destroy"

# Destroy flow does not require live OIDC wiring, but init helpers enforce a full
# OIDC contract. Provide deterministic placeholders so disable/prune teardown can
# run even when runtime auth configuration has already been removed.
set_default_env KEYCLOAK_ISSUER_URL "https://keycloak.placeholder.invalid/realms/placeholder"
set_default_env KEYCLOAK_CLIENT_ID "placeholder-client-id"
set_default_env KEYCLOAK_CLIENT_SECRET "placeholder-client-secret"
set_default_env IAP_COOKIE_SECRET "0123456789abcdef0123456789abcdef"
identity_aware_proxy_init_env
resolve_optional_module_execution "identity-aware-proxy" "destroy"
destroy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
destroy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$destroy_driver" in
argocd_application_chart)
  run_manifest_delete "$destroy_path"
  identity_aware_proxy_delete_runtime_secret
  ;;
helm)
  destroy_path="$IAP_HELM_RELEASE@$IAP_NAMESPACE"
  run_helm_uninstall "$IAP_HELM_RELEASE" "$IAP_NAMESPACE"
  identity_aware_proxy_delete_runtime_secret
  ;;
*)
  optional_module_unexpected_driver "identity-aware-proxy" "destroy"
  ;;
esac

remove_state_files_by_prefix "identity_aware_proxy_"
state_file="$(write_state_file "identity_aware_proxy_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "identity-aware-proxy artifacts destroyed"
log_info "identity-aware-proxy destroy state written to $state_file"
