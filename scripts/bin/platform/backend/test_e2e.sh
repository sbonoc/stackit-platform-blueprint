#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/platform/testing.sh"

start_script_metric_trap "backend_test_e2e"

run_python_pytest_lane "backend e2e" "$ROOT_DIR/tests/backend/e2e"
