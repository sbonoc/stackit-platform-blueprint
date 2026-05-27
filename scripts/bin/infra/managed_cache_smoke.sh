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

start_script_metric_trap "infra_managed_cache_smoke"

if ! is_module_enabled managed-cache; then
  log_info "MANAGED_CACHE_ENABLED=false; skipping managed-cache smoke"
  exit 0
fi

managed_cache_init_env

uri="$(managed_cache_uri)"
if [[ -z "$uri" ]]; then
  log_fatal "managed_cache_uri returned empty — smoke failed"
fi
if ! printf '%s' "$uri" | grep -Eq '^redis://'; then
  log_fatal "managed_cache_uri must start with redis:// — got: $uri"
fi

log_info "managed-cache smoke: URI present and redis://-prefixed"
