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

start_script_metric_trap "infra_neo4j_destroy"

resolve_optional_module_execution "neo4j" "destroy"
destroy_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
destroy_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$destroy_driver" in
argocd_optional_manifest)
  run_manifest_delete "$destroy_path"
  ;;
*)
  optional_module_unexpected_driver "neo4j" "destroy"
  ;;
esac

remove_state_files_by_prefix "neo4j_"
state_file="$(write_state_file "neo4j_destroy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "destroy_driver=$destroy_driver" \
  "destroy_path=$destroy_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "neo4j artifacts destroyed"
log_info "neo4j destroy state written to $state_file"
