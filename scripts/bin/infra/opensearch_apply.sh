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
source "$ROOT_DIR/scripts/lib/infra/opensearch.sh"

start_script_metric_trap "infra_opensearch_apply"

if ! is_module_enabled opensearch; then
  log_info "OPENSEARCH_ENABLED=false; skipping opensearch apply"
  exit 0
fi

opensearch_init_env
if ! state_file_exists opensearch_plan; then
  log_fatal "missing opensearch plan artifact; run infra-opensearch-plan first"
fi

resolve_optional_module_execution "opensearch" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_apply_foundation_contract "opensearch"
  ;;
helm)
  provision_path="$(opensearch_render_values_file)"
  opensearch_reconcile_runtime_secret
  run_helm_upgrade_install \
    "$OPENSEARCH_HELM_RELEASE" \
    "$OPENSEARCH_NAMESPACE" \
    "$OPENSEARCH_HELM_CHART" \
    "$OPENSEARCH_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "opensearch" "apply"
  ;;
esac

state_file="$(write_state_file "opensearch_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "host=$(opensearch_host)" \
  "hosts=$(opensearch_hosts)" \
  "port=$(opensearch_port)" \
  "scheme=$(opensearch_scheme)" \
  "uri=$(opensearch_uri)" \
  "dashboard_url=$(opensearch_dashboard_url)" \
  "username=$(opensearch_username)" \
  "password=$(opensearch_password)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "opensearch runtime state written to $state_file"
