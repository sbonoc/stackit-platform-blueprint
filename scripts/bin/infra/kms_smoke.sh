#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/kms.sh"

start_script_metric_trap "infra_kms_smoke"

if ! is_module_enabled kms; then
  log_info "KMS_ENABLED=false; skipping kms smoke"
  exit 0
fi

kms_init_env
if ! state_file_exists kms_runtime; then
  log_fatal "missing kms runtime artifact"
fi

runtime_state="$(state_file_path kms_runtime)"
if ! grep -q '^key_id=kms://' "$runtime_state"; then
  log_fatal "kms runtime key_id contract is invalid"
fi

state_file="$(write_state_file "kms_smoke" \
  "status=passed" \
  "key_id=$(kms_key_id)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "kms smoke state written to $state_file"
