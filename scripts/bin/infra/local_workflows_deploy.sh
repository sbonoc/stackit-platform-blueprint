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

start_script_metric_trap "infra_local_workflows_deploy"

if [[ "${WORKFLOWS_LOCAL_ENABLED:-false}" != "true" ]]; then
  log_info "WORKFLOWS_LOCAL_ENABLED=false; skipping local-workflows deploy"
  exit 0
fi

workflows_local_init_env
if ! state_file_exists local_workflows_apply; then
  log_fatal "missing local-workflows apply artifact; run infra-local-workflows-apply first"
fi

resolve_optional_module_execution "local-workflows" "deploy"
deploy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
deploy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$deploy_driver" in
argocd_optional_manifest)
  run_manifest_apply "$deploy_path"
  ;;
*)
  optional_module_unexpected_driver "local-workflows" "deploy"
  ;;
esac

state_file="$(write_state_file "local_workflows_deploy" \
  "profile=$BLUEPRINT_PROFILE" \
  "provision_status=deployed" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "local-workflows deploy state written to $state_file"
