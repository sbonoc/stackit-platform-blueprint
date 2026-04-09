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

start_script_metric_trap "infra_postgres_plan"

if ! is_module_enabled postgres; then
  log_info "POSTGRES_ENABLED=false; skipping postgres plan"
  exit 0
fi

postgres_init_env
resolve_optional_module_execution "postgres" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
foundation_contract)
  optional_module_warn_missing_foundation_diff "postgres"
  ;;
helm)
  provision_path="$(postgres_render_values_file)"
  run_helm_template \
    "$POSTGRES_HELM_RELEASE" \
    "$POSTGRES_NAMESPACE" \
    "$POSTGRES_HELM_CHART" \
    "$POSTGRES_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "postgres" "plan"
  ;;
esac

state_file="$(write_state_file "postgres_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "instance_name=$POSTGRES_INSTANCE_NAME" \
  "version=${POSTGRES_VERSION:-16}" \
  "host=$(postgres_host)" \
  "port=$(postgres_port)" \
  "database=$(postgres_database)" \
  "username=$(postgres_username)" \
  "connect_timeout_seconds=$POSTGRES_CONNECT_TIMEOUT_SECONDS" \
  "extra_allowed_cidrs=${POSTGRES_EXTRA_ALLOWED_CIDRS:-}" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "postgres plan state written to $state_file"
