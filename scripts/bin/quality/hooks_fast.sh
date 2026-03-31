#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"

start_script_metric_trap "quality_hooks_fast"

usage() {
  cat <<'EOF'
Usage: hooks_fast.sh

Runs the fast local quality gate:
- pre-commit (if available)
- shellcheck (required)
- docs lint
- blueprint docs/template sync checks
- generated docs sync checks
- runtime identity summary sync checks
- generated module contract summary sync checks
- test pyramid
- infra validation
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

log_info "quality hooks fast gate start"
if command -v pre-commit >/dev/null 2>&1; then
  run_cmd pre-commit run --all-files
else
  log_warn "pre-commit not installed; skipping pre-commit checks"
fi

require_command shellcheck
shell_scripts=()
while IFS= read -r shell_script; do
  shell_scripts+=("$shell_script")
done < <(find "$ROOT_DIR/scripts" -type f -name '*.sh' | sort)
if [[ "${#shell_scripts[@]}" -gt 0 ]]; then
  run_cmd shellcheck --severity=error --exclude=SC1090,SC1091 "${shell_scripts[@]}"
fi

run_cmd make -C "$ROOT_DIR" quality-docs-lint
run_cmd make -C "$ROOT_DIR" quality-docs-check-blueprint-template-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-core-targets-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-contract-metadata-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-runtime-identity-summary-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-module-contract-summaries-sync
run_cmd make -C "$ROOT_DIR" quality-test-pyramid
run_cmd make -C "$ROOT_DIR" infra-validate

log_info "quality hooks fast gate completed"
