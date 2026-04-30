#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "apps_a11y_smoke"

# Smoke defaults: home route only, fail on critical violations.
export A11Y_BASE_URL="${A11Y_BASE_URL:-http://localhost:3000}"
export A11Y_ROUTES="${A11Y_ROUTES:-/}"
export A11Y_FAIL_ON_IMPACT="${A11Y_FAIL_ON_IMPACT:-critical}"

log_info "running a11y smoke scan (routes=$A11Y_ROUTES fail_on_impact=$A11Y_FAIL_ON_IMPACT)"

run_cmd bash "$ROOT_DIR/scripts/bin/platform/touchpoints/test_a11y.sh"
