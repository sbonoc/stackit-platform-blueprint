#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_postgres_destroy"

destroy_driver="none"
destroy_path="none"
if is_stackit_profile; then
  destroy_driver="foundation_reconcile_apply"
  destroy_path="$(stackit_terraform_layer_dir foundation)"
  run_cmd env POSTGRES_ENABLED=false "$ROOT_DIR/scripts/bin/infra/stackit_foundation_preflight.sh"
  run_cmd env POSTGRES_ENABLED=false "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
elif is_local_profile; then
  set_default_env POSTGRES_NAMESPACE "data"
  set_default_env POSTGRES_HELM_RELEASE "blueprint-postgres"
  destroy_driver="helm"
  destroy_path="${POSTGRES_HELM_RELEASE}@${POSTGRES_NAMESPACE}"
  run_helm_uninstall "$POSTGRES_HELM_RELEASE" "$POSTGRES_NAMESPACE"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

remove_state_files_by_prefix "postgres_"
state_file="$(write_state_file "postgres_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "postgres artifacts destroyed"
log_info "postgres destroy state written to $state_file"
