#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/neo4j.sh"

start_script_metric_trap "infra_neo4j_deploy"

if ! is_module_enabled neo4j; then
  log_info "NEO4J_ENABLED=false; skipping neo4j deploy"
  exit 0
fi

neo4j_init_env
if ! state_file_exists neo4j_runtime; then
  log_fatal "missing neo4j runtime artifact; run infra-neo4j-apply first"
fi

state_file="$(write_state_file "neo4j_deploy" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "deploy_driver=argocd_optional_manifest" \
  "deploy_path=$(argocd_optional_manifest "neo4j")" \
  "status=deployed" \
  "uri=$(neo4j_uri)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "neo4j deploy state written to $state_file"
