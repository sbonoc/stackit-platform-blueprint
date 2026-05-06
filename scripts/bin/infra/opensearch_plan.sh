#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/opensearch.sh"

start_script_metric_trap "infra_opensearch_plan"

if ! is_module_enabled opensearch; then
  log_info "OPENSEARCH_ENABLED=false; skipping opensearch plan"
  exit 0
fi

opensearch_init_env
resolve_optional_module_execution "opensearch" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_warn_missing_foundation_diff "opensearch"
  ;;
helm)
  provision_path="$(opensearch_render_values_file)"
  run_helm_template \
    "$OPENSEARCH_HELM_RELEASE" \
    "$OPENSEARCH_NAMESPACE" \
    "$OPENSEARCH_HELM_CHART" \
    "$OPENSEARCH_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
noop)
  optional_module_log_execution_note
  ;;
*)
  optional_module_unexpected_driver "opensearch" "plan"
  ;;
esac

state_file="$(write_state_file "opensearch_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "instance_name=$OPENSEARCH_INSTANCE_NAME" \
  "version=$OPENSEARCH_VERSION" \
  "plan_name=$OPENSEARCH_PLAN_NAME" \
  "host=$(opensearch_host)" \
  "port=$(opensearch_port)" \
  "scheme=$(opensearch_scheme)" \
  "dashboard_url=$(opensearch_dashboard_url)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "opensearch plan state written to $state_file"
