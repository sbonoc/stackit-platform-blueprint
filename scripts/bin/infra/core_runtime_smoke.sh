#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_core_runtime_smoke"

usage() {
  cat <<'USAGE'
Usage: core_runtime_smoke.sh

Validates runtime core bootstrap state generated during infra-deploy.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! state_file_exists core_runtime_bootstrap; then
  log_warn "core_runtime_bootstrap state not found; run infra-deploy first"
  exit 0
fi

runtime_state="$ROOT_DIR/artifacts/infra/core_runtime_bootstrap.env"
if ! grep -q '^argocd_chart=' "$runtime_state"; then
  log_fatal "argocd_chart missing from core runtime state: $runtime_state"
fi
if ! grep -q '^external_secrets_chart=' "$runtime_state"; then
  log_fatal "external_secrets_chart missing from core runtime state: $runtime_state"
fi

state_file="$(
  write_state_file "core_runtime_smoke" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "runtime_state=$runtime_state" \
    "status=ok" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "core runtime smoke state written to $state_file"
