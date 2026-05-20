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

start_script_metric_trap "infra_local_workflows_plan"

if [[ "${WORKFLOWS_LOCAL_ENABLED:-false}" != "true" ]]; then
  log_info "WORKFLOWS_LOCAL_ENABLED=false; skipping local-workflows plan"
  exit 0
fi

workflows_local_init_env
resolve_optional_module_execution "local-workflows" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
argocd_optional_manifest)
  optional_module_require_manifest_present "local-workflows" "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "local-workflows" "plan"
  ;;
esac

state_file="$(write_state_file "local_workflows_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "public_url=$(workflows_local_public_url)" \
  "chart_version=$(workflows_local_chart_version)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "local-workflows plan state written to $state_file"
