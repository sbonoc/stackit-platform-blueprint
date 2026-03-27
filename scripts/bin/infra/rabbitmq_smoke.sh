#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/rabbitmq.sh"

start_script_metric_trap "infra_rabbitmq_smoke"

if ! is_module_enabled rabbitmq; then
  log_info "RABBITMQ_ENABLED=false; skipping rabbitmq smoke"
  exit 0
fi

rabbitmq_init_env
if ! state_file_exists rabbitmq_runtime; then
  log_fatal "missing rabbitmq runtime artifact"
fi

runtime_state="$(state_file_path rabbitmq_runtime)"
if ! grep -Eq '^uri=amqps?://' "$runtime_state"; then
  log_fatal "rabbitmq runtime URI contract is invalid"
fi

state_file="$(write_state_file "rabbitmq_smoke" \
  "status=passed" \
  "uri=$(rabbitmq_uri)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "rabbitmq smoke state written to $state_file"
