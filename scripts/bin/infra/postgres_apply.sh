#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
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

provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="terraform"
  provision_path="$(stackit_terraform_module_dir "postgres")"
  run_terraform_action apply "$provision_path"
elif is_local_profile; then
  provision_driver="helm"
  provision_path="$(local_module_helm_values_file "postgres")"
  run_helm_upgrade_install \
    "$POSTGRES_HELM_RELEASE" \
    "$POSTGRES_NAMESPACE" \
    "$POSTGRES_HELM_CHART" \
    "$POSTGRES_HELM_CHART_VERSION" \
    "$provision_path"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "postgres_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "host=$(postgres_host)" \
  "port=$POSTGRES_PORT" \
  "database=$POSTGRES_DB_NAME" \
  "username=$POSTGRES_USER" \
  "password=$POSTGRES_PASSWORD" \
  "dsn=$(postgres_dsn)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "postgres runtime state written to $state_file"
