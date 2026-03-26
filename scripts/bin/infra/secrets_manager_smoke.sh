#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/secrets_manager.sh"

start_script_metric_trap "infra_secrets_manager_smoke"

if ! is_module_enabled secrets-manager; then
  log_info "SECRETS_MANAGER_ENABLED=false; skipping secrets-manager smoke"
  exit 0
fi

secrets_manager_init_env
if ! state_file_exists secrets_manager_runtime; then
  log_fatal "missing secrets-manager runtime artifact"
fi

runtime_state="$(state_file_path secrets_manager_runtime)"
if ! grep -q '^endpoint=https://secrets\.' "$runtime_state"; then
  log_fatal "secrets-manager runtime endpoint contract is invalid"
fi

state_file="$(write_state_file "secrets_manager_smoke" \
  "status=passed" \
  "endpoint=$(secrets_manager_endpoint)" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "secrets-manager smoke state written to $state_file"
