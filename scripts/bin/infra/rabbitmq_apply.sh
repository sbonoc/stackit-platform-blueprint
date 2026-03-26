#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
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

resolve_optional_module_execution "rabbitmq" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
argocd_optional_manifest)
  run_manifest_apply "$provision_path"
  ;;
helm)
  run_helm_upgrade_install \
    "$RABBITMQ_HELM_RELEASE" \
    "$RABBITMQ_NAMESPACE" \
    "$RABBITMQ_HELM_CHART" \
    "$RABBITMQ_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "rabbitmq" "apply"
  ;;
esac

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
