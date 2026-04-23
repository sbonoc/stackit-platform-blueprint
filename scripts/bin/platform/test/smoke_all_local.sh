#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "test_smoke_all_local"

usage() {
  cat <<'EOF'
Usage: smoke_all_local.sh [--skip-provision]

Runs the full local endpoint smoke lane against a local cluster:

  1. infra-provision-deploy  (execute mode; skipped with --skip-provision)
  2. infra-smoke             (infra-level pod-health + contract smoke)
  3. test_smoke_endpoints.py (port-forward + HTTP endpoint assertions)

The port-forward lifecycle is managed inside the pytest test. A trap
ensures infra-port-forward-cleanup runs on any exit — including failures —
so stale port-forwards do not accumulate between runs.

Options:
  --skip-provision   Skip infra-provision-deploy (use when the cluster is
                     already provisioned and deployed).

Environment variables:
  BLUEPRINT_PROFILE              Active profile (default: local-lite)
  OBSERVABILITY_ENABLED          Observability flag (default: false)
  SMOKE_BACKEND_BASE_URL         Backend API base URL (default: http://localhost:18080)
  SMOKE_BACKEND_HEALTH_PATH      Health endpoint path (default: /health)
  SMOKE_BACKEND_AUTH_GATE_PATH   Protected endpoint for auth-gate check (optional)
  SMOKE_PF_WAIT_TIMEOUT          Port-forward readiness timeout in seconds (default: 30)
EOF
}

skip_provision="false"

while (($#)); do
  case "${1:-}" in
  --skip-provision)
    skip_provision="true"
    shift
    ;;
  --help)
    usage
    exit 0
    ;;
  *)
    log_fatal "unknown argument: ${1}"
    ;;
  esac
done

set_default_env BLUEPRINT_PROFILE "local-lite"
set_default_env OBSERVABILITY_ENABLED "false"

# Safety net: clean up any port-forwards left open by test failures.
# The pytest tearDownClass also runs cleanup, so this handles the edge
# case where the Python process is killed before teardown completes.
cleanup() {
  local exit_code=$?
  log_info "smoke_all_local cleanup: running infra-port-forward-cleanup"
  make -C "$ROOT_DIR" infra-port-forward-cleanup 2>/dev/null || true
  exit "$exit_code"
}
trap cleanup EXIT

log_info "test smoke all local start"
log_info "profile=$BLUEPRINT_PROFILE observability=$OBSERVABILITY_ENABLED skip_provision=$skip_provision"

if [[ "$skip_provision" != "true" ]]; then
  log_info "step 1/3: infra-provision-deploy (execute mode)"
  run_cmd make -C "$ROOT_DIR" \
    BLUEPRINT_PROFILE="$BLUEPRINT_PROFILE" \
    OBSERVABILITY_ENABLED="$OBSERVABILITY_ENABLED" \
    DRY_RUN=false \
    infra-provision-deploy
else
  log_info "step 1/3: skipped (--skip-provision)"
fi

log_info "step 2/3: infra-smoke"
run_cmd make -C "$ROOT_DIR" \
  BLUEPRINT_PROFILE="$BLUEPRINT_PROFILE" \
  OBSERVABILITY_ENABLED="$OBSERVABILITY_ENABLED" \
  infra-smoke

log_info "step 3/3: endpoint smoke tests"
require_command pytest
run_cmd pytest \
  -v \
  --tb=short \
  "$ROOT_DIR/tests/e2e/test_smoke_endpoints.py"

log_metric "test_smoke_all_local_total" "1" "status=success profile=$BLUEPRINT_PROFILE"
log_info "test smoke all local completed"
