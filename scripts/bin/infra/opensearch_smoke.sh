#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/opensearch.sh"

start_script_metric_trap "infra_opensearch_smoke"

if ! is_module_enabled opensearch; then
  log_info "OPENSEARCH_ENABLED=false; skipping opensearch smoke"
  exit 0
fi

opensearch_init_env
if ! state_file_exists opensearch_runtime; then
  log_fatal "missing opensearch runtime artifact"
fi

runtime_state="$(state_file_path opensearch_runtime)"
if ! grep -Eq '^uri=https?://' "$runtime_state"; then
  log_fatal "opensearch runtime URI contract is invalid"
fi
if ! grep -Eq '^dashboard_url=(https?://.*)?$' "$runtime_state"; then
  log_fatal "opensearch runtime dashboard URL contract is invalid"
fi

state_file="$(write_state_file "opensearch_smoke" \
  "status=passed" \
  "uri=$(opensearch_uri)" \
  "dashboard_url=$(opensearch_dashboard_url)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "opensearch smoke state written to $state_file"
