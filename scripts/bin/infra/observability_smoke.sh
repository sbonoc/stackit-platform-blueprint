#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"

start_script_metric_trap "infra_observability_smoke"

if ! is_module_enabled observability; then
  log_info "OBSERVABILITY_ENABLED=false; skipping observability smoke"
  exit 0
fi

if ! state_file_exists observability_runtime; then
  log_fatal "missing observability runtime artifact"
fi
if ! state_file_exists observability_deploy; then
  log_fatal "missing observability deploy artifact"
fi

if ! grep -q '^otel_endpoint=http' "$(state_file_path observability_runtime)"; then
  log_fatal "observability runtime OTEL endpoint is invalid"
fi
if ! grep -q '^health_status=Healthy$' "$(state_file_path observability_deploy)"; then
  log_fatal "observability deploy state is not healthy"
fi

state_file="$(
  write_state_file "observability_smoke" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "status=passed" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "observability smoke state written to $state_file"
