#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "blueprint_ci_upgrade_validate"

usage() {
  cat <<'EOF'
Usage: ci_upgrade_validate.sh

Runs the end-to-end consumer upgrade validation lane using the upgrade fixture
matrix (tests/blueprint/fixtures/upgrade_matrix).

Exercises the full upgrade pipeline — resync dry-run, resync apply-safe, upgrade
plan, and upgrade apply — against the fixture matrix in a temp directory, then
writes a JUnit XML report to BLUEPRINT_CI_UPGRADE_ARTIFACTS_DIR.

This is the Phase 1 foundation for the upgrade CI gate (#169). Phase 2 issues
(#162, #163) extend this script with additional correctness checks.

Environment variables:
  BLUEPRINT_CI_UPGRADE_ARTIFACTS_DIR  Directory for JUnit XML output
                                      (default: $ROOT_DIR/artifacts/blueprint/upgrade_validate)
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

artifacts_dir="${BLUEPRINT_CI_UPGRADE_ARTIFACTS_DIR:-$ROOT_DIR/artifacts/blueprint/upgrade_validate}"
junit_xml="$artifacts_dir/upgrade_validate_junit.xml"

log_info "blueprint ci upgrade validate start"
log_info "artifacts_dir=$artifacts_dir"

ensure_dir "$artifacts_dir"

require_command pytest

run_cmd pytest \
  -v \
  --tb=short \
  --junitxml="$junit_xml" \
  "$ROOT_DIR/tests/blueprint/test_upgrade_fixture_matrix.py"

log_metric "blueprint_ci_upgrade_validate_total" "1" "status=success"
log_info "blueprint ci upgrade validate completed; junit_xml=$junit_xml"
