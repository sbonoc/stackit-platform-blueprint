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

start_script_metric_trap "infra_rabbitmq_destroy"

rabbitmq_init_env
destroy_driver="none"
destroy_path="none"
if is_stackit_profile; then
  destroy_driver="terraform"
  destroy_path="$(stackit_terraform_module_dir "rabbitmq")"
  run_terraform_action destroy "$destroy_path"
elif is_local_profile; then
  destroy_driver="helm"
  destroy_path="$RABBITMQ_HELM_RELEASE@$RABBITMQ_NAMESPACE"
  run_helm_uninstall "$RABBITMQ_HELM_RELEASE" "$RABBITMQ_NAMESPACE"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

remove_state_files_by_prefix "rabbitmq_"
state_file="$(write_state_file "rabbitmq_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "rabbitmq artifacts destroyed"
log_info "rabbitmq destroy state written to $state_file"
