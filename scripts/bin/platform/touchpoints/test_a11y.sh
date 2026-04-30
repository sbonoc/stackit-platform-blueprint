#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "touchpoints_test_a11y"

A11Y_BASE_URL="${A11Y_BASE_URL:-http://localhost:3000}"
A11Y_ROUTES="${A11Y_ROUTES:-/}"
A11Y_FAIL_ON_IMPACT="${A11Y_FAIL_ON_IMPACT:-critical,serious}"

log_info "running axe WCAG 2.1 AA accessibility scan"
log_info "base_url=$A11Y_BASE_URL routes=$A11Y_ROUTES fail_on_impact=$A11Y_FAIL_ON_IMPACT"

run_cmd node \
  "$ROOT_DIR/scripts/lib/platform/touchpoints/axe_page_scan.mjs" \
  --base-url "$A11Y_BASE_URL" \
  --routes "$A11Y_ROUTES" \
  --fail-on-impact "$A11Y_FAIL_ON_IMPACT"
