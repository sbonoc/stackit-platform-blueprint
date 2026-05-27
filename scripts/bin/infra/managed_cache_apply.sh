#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/module_execution.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/managed_cache.sh"

start_script_metric_trap "infra_managed_cache_apply"

if ! is_module_enabled managed-cache; then
  log_info "MANAGED_CACHE_ENABLED=false; skipping managed-cache apply"
  exit 0
fi

managed_cache_init_env

resolve_optional_module_execution "managed-cache" "apply"

write_state_file "managed_cache_runtime" \
  "host=$(managed_cache_host)" \
  "port=$(managed_cache_port)" \
  "uri=$(managed_cache_uri)"
