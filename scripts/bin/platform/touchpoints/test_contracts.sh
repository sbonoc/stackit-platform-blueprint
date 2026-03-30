#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/platform/testing.sh"

start_script_metric_trap "touchpoints_test_contracts"

run_touchpoints_pnpm_lane \
  "touchpoints contracts" \
  "pact" \
  "$ROOT_DIR/apps/touchpoints" \
  "test:contracts" \
  "test:contract" \
  "test:pact"

# Keep optional Python contract assertions as a complementary lane when
# consumer repos also maintain pytest-based touchpoint contract checks.
run_python_pytest_lane "touchpoints contracts" "$ROOT_DIR/tests/touchpoints/contracts"
