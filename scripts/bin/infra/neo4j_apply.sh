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
source "$ROOT_DIR/scripts/lib/infra/neo4j.sh"

start_script_metric_trap "infra_neo4j_apply"

if ! is_module_enabled neo4j; then
  log_info "NEO4J_ENABLED=false; skipping neo4j apply"
  exit 0
fi

neo4j_init_env
if ! state_file_exists neo4j_plan; then
  log_fatal "missing neo4j plan artifact; run infra-neo4j-plan first"
fi

resolve_optional_module_execution "neo4j" "apply"
provision_driver="$OPTIONAL_MODULE_EXECUTION_DRIVER"
provision_path="$OPTIONAL_MODULE_EXECUTION_PATH"
case "$provision_driver" in
argocd_optional_manifest)
  run_manifest_apply "$provision_path"
  ;;
*)
  optional_module_unexpected_driver "neo4j" "apply"
  ;;
esac

state_file="$(write_state_file "neo4j_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "uri=$(neo4j_uri)" \
  "username=$NEO4J_AUTH_USERNAME" \
  "password=$NEO4J_AUTH_PASSWORD" \
  "database=$NEO4J_DATABASE" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "neo4j runtime state written to $state_file"
