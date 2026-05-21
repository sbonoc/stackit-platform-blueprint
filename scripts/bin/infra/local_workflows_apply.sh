#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows_local.sh"

start_script_metric_trap "infra_local_workflows_apply"

if [[ "${WORKFLOWS_LOCAL_ENABLED:-false}" != "true" ]]; then
  log_info "WORKFLOWS_LOCAL_ENABLED=false; skipping local-workflows apply"
  exit 0
fi

workflows_local_init_env
if ! state_file_exists local_workflows_plan; then
  log_fatal "missing local-workflows plan artifact; run infra-local-workflows-plan first"
fi

resolve_optional_module_execution "local-workflows" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
provision_status="applied"
case "$provision_driver" in
argocd_optional_manifest)
  provision_status="deferred_to_deploy"
  log_info "deferring local-workflows ArgoCD manifest apply to deploy phase path=$provision_path"
  ;;
*)
  optional_module_unexpected_driver "local-workflows" "apply"
  ;;
esac

state_file="$(write_state_file "local_workflows_apply" \
  "profile=$BLUEPRINT_PROFILE" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "provision_status=$provision_status" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "local-workflows apply state written to $state_file"
