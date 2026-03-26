#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/rabbitmq.sh"

start_script_metric_trap "infra_rabbitmq_apply"

if ! is_module_enabled rabbitmq; then
  log_info "RABBITMQ_ENABLED=false; skipping rabbitmq apply"
  exit 0
fi

rabbitmq_init_env
if ! state_file_exists rabbitmq_plan; then
  log_fatal "missing rabbitmq plan artifact; run infra-rabbitmq-plan first"
fi

provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="terraform"
  provision_path="$(stackit_terraform_module_dir "rabbitmq")"
  run_terraform_action apply "$provision_path"
elif is_local_profile; then
  provision_driver="helm"
  provision_path="$(local_module_helm_values_file "rabbitmq")"
  run_helm_upgrade_install \
    "$RABBITMQ_HELM_RELEASE" \
    "$RABBITMQ_NAMESPACE" \
    "$RABBITMQ_HELM_CHART" \
    "$RABBITMQ_HELM_CHART_VERSION" \
    "$provision_path"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "rabbitmq_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "host=$(rabbitmq_host)" \
  "port=$RABBITMQ_PORT" \
  "uri=$(rabbitmq_uri)" \
  "username=$RABBITMQ_USERNAME" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "rabbitmq runtime state written to $state_file"
