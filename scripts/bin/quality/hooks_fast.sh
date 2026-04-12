#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "quality_hooks_fast"

usage() {
  cat <<'EOF'
Usage: hooks_fast.sh

Runs the fast local quality gate:
- pre-commit (if available)
- shellcheck (required)
- root-resolution prelude drift check
- infra shell source-edge graph check
- CI workflow sync checks (template-source only)
- docs lint
- blueprint docs/template sync checks
- platform docs/template sync checks
- generated docs sync checks
- runtime identity summary sync checks
- generated module contract summary sync checks
- test pyramid
- infra validation
- fast infra contract helper CLI tests
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

run_cmd make -C "$ROOT_DIR" quality-root-dir-prelude-check
run_cmd make -C "$ROOT_DIR" quality-infra-shell-source-graph-check
run_cmd make -C "$ROOT_DIR" quality-docs-lint
if blueprint_repo_is_generated_consumer; then
  log_metric "quality_ci_check_sync_total" "1" "status=skipped repo_mode=generated-consumer"
  log_info "skipping quality-ci-check-sync in generated-consumer repo"
else
  run_cmd make -C "$ROOT_DIR" quality-ci-check-sync
  log_metric "quality_ci_check_sync_total" "1" "status=success repo_mode=template-source"
fi
run_cmd make -C "$ROOT_DIR" quality-docs-check-blueprint-template-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-platform-seed-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-core-targets-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-contract-metadata-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-runtime-identity-summary-sync
run_cmd make -C "$ROOT_DIR" quality-docs-check-module-contract-summaries-sync
run_cmd make -C "$ROOT_DIR" quality-test-pyramid
run_cmd make -C "$ROOT_DIR" infra-validate
run_cmd make -C "$ROOT_DIR" infra-contract-test-fast

log_info "quality hooks fast gate completed"
