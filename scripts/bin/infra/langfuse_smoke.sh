#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/langfuse.sh"

start_script_metric_trap "infra_langfuse_smoke"

if ! is_module_enabled langfuse; then
  log_info "LANGFUSE_ENABLED=false; skipping langfuse smoke"
  exit 0
fi

langfuse_init_env
if ! state_file_exists langfuse_deploy; then
  log_fatal "missing langfuse deploy artifact"
fi
if ! grep -q '^health_status=Healthy$' "$(state_file_path langfuse_deploy)"; then
  log_fatal "langfuse deploy state is not healthy"
fi

state_file="$(write_state_file "langfuse_smoke" \
  "status=passed" \
  "public_url=$(langfuse_public_url)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "langfuse smoke state written to $state_file"
