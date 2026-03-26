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

start_script_metric_trap "infra_postgres_plan"

if ! is_module_enabled postgres; then
  log_info "POSTGRES_ENABLED=false; skipping postgres plan"
  exit 0
fi

postgres_init_env
provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="foundation_contract"
  provision_path="$(stackit_terraform_layer_dir foundation)"
  if ! state_file_exists stackit_foundation_plan && ! state_file_exists stackit_foundation_apply; then
    log_warn "STACKIT foundation plan/apply state not found; run infra-stackit-foundation-plan for full terraform diff"
  fi
elif is_local_profile; then
  provision_driver="helm"
  provision_path="$(local_module_helm_values_file "postgres")"
  run_helm_template \
    "$POSTGRES_HELM_RELEASE" \
    "$POSTGRES_NAMESPACE" \
    "$POSTGRES_HELM_CHART" \
    "$POSTGRES_HELM_CHART_VERSION" \
    "$provision_path"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "postgres_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "instance_name=$POSTGRES_INSTANCE_NAME" \
  "version=${POSTGRES_VERSION:-16}" \
  "host=$(postgres_host)" \
  "port=$POSTGRES_PORT" \
  "database=$POSTGRES_DB_NAME" \
  "username=$POSTGRES_USER" \
  "connect_timeout_seconds=$POSTGRES_CONNECT_TIMEOUT_SECONDS" \
  "extra_allowed_cidrs=${POSTGRES_EXTRA_ALLOWED_CIDRS:-}" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "postgres plan state written to $state_file"
