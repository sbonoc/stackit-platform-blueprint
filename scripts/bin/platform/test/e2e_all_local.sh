#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "test_e2e_all_local"

log_info "running local-lite infra chain before aggregate e2e test lanes"
run_cmd make -C "$ROOT_DIR" BLUEPRINT_PROFILE=local-lite OBSERVABILITY_ENABLED=false infra-provision-deploy
run_cmd make -C "$ROOT_DIR" backend-test-e2e
run_cmd make -C "$ROOT_DIR" touchpoints-test-e2e
