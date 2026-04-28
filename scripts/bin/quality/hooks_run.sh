#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"

start_script_metric_trap "quality_hooks_run"

usage() {
  cat <<'EOF'
Usage: hooks_run.sh [--keep-going]

Runs the full quality gate by composing:
- `hooks_fast.sh` (fast checks; pre-commit always fail-fast)
- `hooks_strict.sh` (audit checks; only when fast's pre-commit passed)

Flags:
  --keep-going    Aggregate all independent failures across both phases and
                  emit a consolidated summary block instead of aborting on the
                  first failure. Equivalent to setting QUALITY_HOOKS_KEEP_GOING=true.

Environment variables:
  QUALITY_HOOKS_KEEP_GOING        Set to 'true' to enable keep-going mode
                                  (equivalent to --keep-going flag).
  QUALITY_HOOKS_KEEP_GOING_TAIL_LINES
                                  Number of output lines to re-emit on per-check
                                  failure in keep-going mode (default: 40).
  QUALITY_HOOKS_FORCE_FULL        Set to 'true' to override path-gating and
                                  phase-gating in child invocations; all checks
                                  run regardless of changed paths or spec readiness.
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

_keep_going_active() {
  [[ "${QUALITY_HOOKS_KEEP_GOING:-}" == "true" ]]
}

log_info "quality hooks run start"

if _keep_going_active; then
  # In keep-going mode: use sentinel file so strict only runs when pre-commit passed
  _precommit_passed_sentinel="$(mktemp)"
  _fast_exit=0
  QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL="$_precommit_passed_sentinel" \
    "$ROOT_DIR/scripts/bin/quality/hooks_fast.sh" || _fast_exit=$?

  _strict_exit=0
  if [[ "$(cat "$_precommit_passed_sentinel" 2>/dev/null)" == "1" ]]; then
    "$ROOT_DIR/scripts/bin/quality/hooks_strict.sh" || _strict_exit=$?
  else
    log_warn "skipping strict phase: pre-commit did not pass in fast phase"
  fi
  rm -f "$_precommit_passed_sentinel"

  if [[ "$_fast_exit" -ne 0 || "$_strict_exit" -ne 0 ]]; then
    log_info "quality hooks run completed with failures"
    exit 1
  fi
else
  run_cmd "$ROOT_DIR/scripts/bin/quality/hooks_fast.sh"
  run_cmd "$ROOT_DIR/scripts/bin/quality/hooks_strict.sh"
fi

log_info "quality hooks run completed"
