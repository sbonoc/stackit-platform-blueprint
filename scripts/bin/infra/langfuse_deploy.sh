#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/langfuse.sh"

start_script_metric_trap "infra_langfuse_deploy"

if ! is_module_enabled langfuse; then
  log_info "LANGFUSE_ENABLED=false; skipping langfuse deploy"
  exit 0
fi

langfuse_init_env
if ! state_file_exists langfuse_apply; then
  log_fatal "missing langfuse apply artifact; run infra-langfuse-apply first"
fi

resolve_optional_module_execution "langfuse" "deploy"
deploy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
deploy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$deploy_driver" in
argocd_optional_manifest)
  run_manifest_apply "$deploy_path"
  ;;
*)
  optional_module_unexpected_driver "langfuse" "deploy"
  ;;
esac

run_cmd "$ROOT_DIR/scripts/bin/infra/langfuse_keycloak_reconcile.sh"
keycloak_reconcile_state="none"
if state_file_exists langfuse_keycloak_reconcile; then
  keycloak_reconcile_state="$(state_file_path langfuse_keycloak_reconcile)"
fi

state_file="$(write_state_file "langfuse_deploy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "deploy_driver=$deploy_driver" \
  "deploy_path=$deploy_path" \
  "public_url=$(langfuse_public_url)" \
  "health_status=Healthy" \
  "oidc_mode=app_level_oidc" \
  "keycloak_reconcile_state=$keycloak_reconcile_state" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "langfuse deploy state written to $state_file"
