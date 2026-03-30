#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/platform/testing.sh"

start_script_metric_trap "touchpoints_test_unit"

run_touchpoints_pnpm_lane \
  "touchpoints unit" \
  "vitest" \
  "$ROOT_DIR/apps/touchpoints" \
  "test:unit" \
  "test:unit:ci" \
  "test"
