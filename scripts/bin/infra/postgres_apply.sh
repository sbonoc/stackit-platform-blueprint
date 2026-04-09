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
source "$ROOT_DIR/scripts/lib/infra/postgres.sh"

start_script_metric_trap "infra_postgres_apply"

if ! is_module_enabled postgres; then
  log_info "POSTGRES_ENABLED=false; skipping postgres apply"
  exit 0
fi

postgres_init_env
if ! state_file_exists postgres_plan; then
  log_fatal "missing postgres plan artifact; run infra-postgres-plan first"
fi

resolve_optional_module_execution "postgres" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_apply_foundation_contract "postgres"
  ;;
helm)
  provision_path="$(postgres_render_values_file)"
  run_helm_upgrade_install \
    "$POSTGRES_HELM_RELEASE" \
    "$POSTGRES_NAMESPACE" \
    "$POSTGRES_HELM_CHART" \
    "$POSTGRES_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "postgres" "apply"
  ;;
esac

state_file="$(write_state_file "postgres_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "host=$(postgres_host)" \
  "port=$(postgres_port)" \
  "database=$(postgres_database)" \
  "username=$(postgres_username)" \
  "password=$(postgres_password)" \
  "dsn=$(postgres_dsn)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "postgres runtime state written to $state_file"
