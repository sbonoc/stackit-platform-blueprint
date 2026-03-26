#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "test_unit_all"

log_info "running aggregate unit test lanes"
run_cmd make -C "$ROOT_DIR" backend-test-unit
run_cmd make -C "$ROOT_DIR" touchpoints-test-unit
