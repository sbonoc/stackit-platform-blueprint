#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/postgres.sh"

start_script_metric_trap "infra_postgres_smoke"

if ! is_module_enabled postgres; then
  log_info "POSTGRES_ENABLED=false; skipping postgres smoke"
  exit 0
fi

postgres_init_env
if ! state_file_exists postgres_runtime; then
  log_fatal "missing postgres runtime artifact"
fi

if ! grep -q '^dsn=postgresql://' "$(state_file_path postgres_runtime)"; then
  log_fatal "postgres runtime DSN is invalid"
fi
if ! [[ "$POSTGRES_CONNECT_TIMEOUT_SECONDS" =~ ^[0-9]+$ ]]; then
  log_fatal "POSTGRES_CONNECT_TIMEOUT_SECONDS must be numeric"
fi

state_file="$(write_state_file "postgres_smoke" \
  "status=passed" \
  "dsn=$(postgres_dsn)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "postgres smoke state written to $state_file"
