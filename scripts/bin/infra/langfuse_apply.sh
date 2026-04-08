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

start_script_metric_trap "infra_langfuse_apply"

if ! is_module_enabled langfuse; then
  log_info "LANGFUSE_ENABLED=false; skipping langfuse apply"
  exit 0
fi

langfuse_init_env
if ! state_file_exists langfuse_plan; then
  log_fatal "missing langfuse plan artifact; run infra-langfuse-plan first"
fi

resolve_optional_module_execution "langfuse" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
provision_status="applied"
case "$provision_driver" in
argocd_optional_manifest)
  provision_status="deferred_to_deploy"
  log_info "deferring langfuse ArgoCD manifest apply to deploy phase path=$provision_path"
  ;;
*)
  optional_module_unexpected_driver "langfuse" "apply"
  ;;
esac

state_file="$(write_state_file "langfuse_apply" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "provision_status=$provision_status" \
  "public_url=$(langfuse_public_url)" \
  "health_status=Provisioned" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "langfuse apply state written to $state_file"
