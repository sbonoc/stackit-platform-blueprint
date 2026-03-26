#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
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
identity_aware_proxy_init_env
destroy_driver="none"
destroy_path="none"
if is_stackit_profile; then
  destroy_driver="argocd_optional_manifest"
  destroy_path="$(argocd_optional_manifest "identity-aware-proxy")"
  run_manifest_delete "$destroy_path"
elif is_local_profile; then
  destroy_driver="helm"
  destroy_path="$IAP_HELM_RELEASE@$IAP_NAMESPACE"
  run_helm_uninstall "$IAP_HELM_RELEASE" "$IAP_NAMESPACE"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

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
