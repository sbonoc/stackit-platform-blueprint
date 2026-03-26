#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/object_storage.sh"

start_script_metric_trap "infra_object_storage_smoke"

if ! is_module_enabled object-storage; then
  log_info "OBJECT_STORAGE_ENABLED=false; skipping object-storage smoke"
  exit 0
fi

object_storage_init_env
if ! state_file_exists object_storage_runtime; then
  log_fatal "missing object-storage runtime artifact"
fi

runtime_state="$(state_file_path object_storage_runtime)"
if ! grep -q '^endpoint=https\?://' "$runtime_state"; then
  log_fatal "object-storage runtime endpoint contract is invalid"
fi
if ! grep -q '^bucket=' "$runtime_state"; then
  log_fatal "object-storage runtime bucket contract is missing"
fi

state_file="$(write_state_file "object_storage_smoke" \
  "status=passed" \
  "endpoint=$(object_storage_endpoint)" \
  "bucket=$OBJECT_STORAGE_BUCKET_NAME" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "object-storage smoke state written to $state_file"
