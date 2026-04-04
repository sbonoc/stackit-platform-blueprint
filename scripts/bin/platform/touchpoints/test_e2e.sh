#!/usr/bin/env bash
# ownership: platform-owned
# generated-consumer maintainers own touchpoints e2e implementation and dependency bootstrap.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/platform/testing.sh"

start_script_metric_trap "touchpoints_test_e2e"

run_touchpoints_pnpm_lane \
  "touchpoints e2e" \
  "playwright" \
  "$ROOT_DIR/apps/touchpoints" \
  "test:e2e" \
  "test:playwright" \
  "e2e"
