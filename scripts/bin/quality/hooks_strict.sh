#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "quality_hooks_strict"

usage() {
  cat <<'EOF'
Usage: hooks_strict.sh

Runs the slower audit-focused quality gate:
- infra version audit
- apps version audit
- blueprint template smoke (template-source repos only)
  Verifies that validate_contract.py passes in generated-consumer mode after
  blueprint-init-repo removes source-only paths.  This is the local equivalent
  of the quality-ci-generated-consumer-smoke CI job; running it before push
  catches contract additions that break consumer validation before CI sees them.
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

log_info "quality hooks strict gate start"
run_cmd make -C "$ROOT_DIR" infra-audit-version
run_cmd make -C "$ROOT_DIR" apps-audit-versions

# The template smoke simulates make blueprint-init-repo → validate_contract inside
# a clean temp copy of the repo.  It is the canonical way to verify that changes
# to blueprint/contract.yaml (e.g. new required_files or source_only entries) do
# not break generated-consumer validation.  Skipped in generated-consumer repos
# because consumers run the smoke against the blueprint source, not themselves.
if blueprint_repo_is_generated_consumer; then
  log_metric "quality_template_smoke_total" "1" "status=skipped repo_mode=generated-consumer"
  log_info "skipping blueprint-template-smoke in generated-consumer repo"
else
  log_info "running blueprint-template-smoke (CI-equivalent generated-consumer conformance check)"
  run_cmd make -C "$ROOT_DIR" blueprint-template-smoke
  log_metric "quality_template_smoke_total" "1" "status=success repo_mode=template-source"
fi

log_info "quality hooks strict gate completed"
