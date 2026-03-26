#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/neo4j.sh"

start_script_metric_trap "infra_neo4j_smoke"

if ! is_module_enabled neo4j; then
  log_info "NEO4J_ENABLED=false; skipping neo4j smoke"
  exit 0
fi

neo4j_init_env
if ! state_file_exists neo4j_deploy; then
  log_fatal "missing neo4j deploy artifact"
fi
if ! grep -q '^uri=bolt://' "$(state_file_path neo4j_deploy)"; then
  log_fatal "neo4j deploy URI is invalid"
fi

state_file="$(write_state_file "neo4j_smoke" \
  "status=passed" \
  "uri=$(neo4j_uri)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "neo4j smoke state written to $state_file"
