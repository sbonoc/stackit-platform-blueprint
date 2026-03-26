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

start_script_metric_trap "infra_rabbitmq_plan"

if ! is_module_enabled rabbitmq; then
  log_info "RABBITMQ_ENABLED=false; skipping rabbitmq plan"
  exit 0
fi

rabbitmq_init_env
resolve_optional_module_execution "rabbitmq" "plan"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
argocd_optional_manifest)
  optional_module_require_manifest_present "rabbitmq" "$provision_path"
  ;;
helm)
  run_helm_template \
    "$RABBITMQ_HELM_RELEASE" \
    "$RABBITMQ_NAMESPACE" \
    "$RABBITMQ_HELM_CHART" \
    "$RABBITMQ_HELM_CHART_VERSION" \
    "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "rabbitmq" "plan"
  ;;
esac

state_file="$(write_state_file "rabbitmq_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "instance_name=$RABBITMQ_INSTANCE_NAME" \
  "host=$(rabbitmq_host)" \
  "port=$RABBITMQ_PORT" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "rabbitmq plan state written to $state_file"
