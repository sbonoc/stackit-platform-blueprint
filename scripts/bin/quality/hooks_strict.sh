#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"
source "$ROOT_DIR/scripts/lib/shell/keep_going.sh"

start_script_metric_trap "quality_hooks_strict"

usage() {
  cat <<'EOF'
Usage: hooks_strict.sh [--keep-going]

Runs the slower audit-focused quality gate:
- infra version audit
- apps version audit
- blueprint template smoke (template-source repos only)
  Verifies that validate_contract.py passes in generated-consumer mode after
  blueprint-init-repo removes source-only paths.  This is the local equivalent
  of the quality-ci-generated-consumer-smoke CI job; running it before push
  catches contract additions that break consumer validation before CI sees them.

Flags:
  --keep-going    Aggregate all independent failures and emit a consolidated
                  summary block instead of aborting on the first failure.
                  Equivalent to setting QUALITY_HOOKS_KEEP_GOING=true.

Environment variables:
  QUALITY_HOOKS_KEEP_GOING        Set to 'true' to enable keep-going mode
                                  (equivalent to --keep-going flag).
  QUALITY_HOOKS_KEEP_GOING_TAIL_LINES
                                  Number of output lines to re-emit on per-check
                                  failure in keep-going mode (default: 40).
  QUALITY_HOOKS_PHASE             Phase label used in keep-going metrics (set
                                  automatically to 'strict' by this script).
EOF
}

_KEEP_GOING=false
for _arg in "$@"; do
  case "$_arg" in
    --keep-going) _KEEP_GOING=true ;;
    --help) usage; exit 0 ;;
  esac
done
if [[ "$_KEEP_GOING" == "true" ]]; then
  export QUALITY_HOOKS_KEEP_GOING=true
fi
export QUALITY_HOOKS_PHASE=strict

log_info "quality hooks strict gate start"

if keep_going_active; then
  keep_going_init
fi

if keep_going_active; then
  run_check "infra-audit-version" -- make -C "$ROOT_DIR" infra-audit-version
  run_check "apps-audit-versions" -- make -C "$ROOT_DIR" apps-audit-versions
else
  run_cmd make -C "$ROOT_DIR" infra-audit-version
  run_cmd make -C "$ROOT_DIR" apps-audit-versions
fi

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
  if keep_going_active; then
    run_check "blueprint-template-smoke" -- make -C "$ROOT_DIR" blueprint-template-smoke
  else
    run_cmd make -C "$ROOT_DIR" blueprint-template-smoke
  fi
  log_metric "quality_template_smoke_total" "1" "status=success repo_mode=template-source"
fi

if keep_going_active; then
  keep_going_finalize
fi

log_info "quality hooks strict gate completed"
