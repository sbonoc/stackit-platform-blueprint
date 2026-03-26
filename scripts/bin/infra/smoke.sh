#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh"

start_script_metric_trap "infra_smoke"

usage() {
  cat <<'EOF'
Usage: smoke.sh

Contract-driven smoke wrapper:
- validates repository contract,
- validates provision/deploy state artifacts,
- executes base and module smoke checks.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

log_info "smoke start profile=$BLUEPRINT_PROFILE stack=$(active_stack) observability=$OBSERVABILITY_ENABLED_NORMALIZED"
run_cmd "$ROOT_DIR/scripts/bin/infra/validate.sh"

if ! state_file_exists provision; then
  log_warn "provision state artifact missing"
fi
if ! state_file_exists deploy; then
  log_warn "deploy state artifact missing"
fi

run_cmd "$ROOT_DIR/scripts/bin/infra/core_runtime_smoke.sh"

run_enabled_modules_action smoke observability

run_cmd "$ROOT_DIR/scripts/bin/platform/apps/smoke.sh"

run_enabled_modules_action smoke \
  workflows langfuse postgres neo4j \
  object-storage rabbitmq dns public-endpoints secrets-manager kms identity-aware-proxy

core_runtime_smoke_state="none"
if state_file_exists core_runtime_smoke; then
  core_runtime_smoke_state="$ROOT_DIR/artifacts/infra/core_runtime_smoke.env"
fi

state_file="$(
  write_state_file "smoke" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "core_runtime_smoke_state=$core_runtime_smoke_state" \
    "observability_enabled=$OBSERVABILITY_ENABLED_NORMALIZED" \
    "enabled_modules=$(enabled_modules_csv)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"
log_info "smoke state written to $state_file"
log_info "infra smoke complete"
