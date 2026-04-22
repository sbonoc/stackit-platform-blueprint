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
- Spec-Driven Development sync drift checks + governance wiring check
- CI workflow sync checks (template-source only)
- docs lint
- docs sync drift checks for changed scope
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
run_cmd make -C "$ROOT_DIR" quality-sdd-check-all
_current_branch="$(git branch --show-current 2>/dev/null || true)"
if [[ "$_current_branch" =~ ^codex/[0-9]{4}-[0-9]{2}-[0-9]{2}- ]]; then
  _spec_slug="${_current_branch#codex/}"
  if [[ -d "$ROOT_DIR/specs/$_spec_slug" ]]; then
    run_cmd make -C "$ROOT_DIR" quality-spec-pr-ready
  fi
fi
run_cmd make -C "$ROOT_DIR" quality-docs-lint
if blueprint_repo_is_generated_consumer; then
  log_metric "quality_ci_check_sync_total" "1" "status=skipped repo_mode=generated-consumer"
  log_info "skipping quality-ci-check-sync in generated-consumer repo"
else
  run_cmd make -C "$ROOT_DIR" quality-ci-check-sync
  log_metric "quality_ci_check_sync_total" "1" "status=success repo_mode=template-source"
fi
if run_cmd make -C "$ROOT_DIR" quality-docs-check-changed; then
  log_metric "quality_docs_check_changed_total" "1" "status=success"
else
  log_metric "quality_docs_check_changed_total" "1" "status=failure"
  exit 1
fi
run_cmd make -C "$ROOT_DIR" quality-test-pyramid
run_cmd make -C "$ROOT_DIR" infra-validate
run_cmd make -C "$ROOT_DIR" infra-contract-test-fast

log_info "quality hooks fast gate completed"
