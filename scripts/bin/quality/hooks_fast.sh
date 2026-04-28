#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"
source "$ROOT_DIR/scripts/lib/shell/keep_going.sh"
source "$ROOT_DIR/scripts/lib/shell/quality_gating.sh"

start_script_metric_trap "quality_hooks_fast"

usage() {
  cat <<'EOF'
Usage: hooks_fast.sh [--keep-going]

Runs the fast local quality gate:
- pre-commit (if available; always fail-fast)
- shellcheck (required)
- root-resolution prelude drift check
- infra shell source-edge graph check
- Spec-Driven Development sync drift checks + governance wiring check
- spec-pr-ready check (skipped when SPEC_READY: false; phase-gated)
- CI workflow sync checks (template-source only)
- docs sync drift checks for changed scope
- infra validation (path-gated)
- fast infra contract helper CLI tests (path-gated)

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
  QUALITY_HOOKS_FORCE_FULL        Set to 'true' to override path-gating and
                                  phase-gating; all checks run regardless of
                                  changed paths or spec readiness.
  QUALITY_HOOKS_PHASE             Phase label used in keep-going metrics (set
                                  automatically to 'fast' by this script).
  QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL
                                  Path to a sentinel file written after pre-commit
                                  passes (used by hooks_run.sh in keep-going mode).
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
export QUALITY_HOOKS_PHASE=fast

log_info "quality hooks fast gate start"

# pre-commit always runs fail-fast (before keep-going aggregation)
if command -v pre-commit >/dev/null 2>&1; then
  run_cmd pre-commit run --all-files
else
  log_warn "pre-commit not installed — install pre-commit to enable quality-docs-lint, quality-test-pyramid, and other local hooks: https://pre-commit.com/"
fi

# Signal to hooks_run.sh that pre-commit passed (if sentinel path is provided)
if [[ -n "${QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL:-}" ]]; then
  echo "1" > "$QUALITY_HOOKS_PRECOMMIT_PASSED_SENTINEL"
fi

# Initialize keep-going aggregation if active
if keep_going_active; then
  keep_going_init
fi

require_command shellcheck
shell_scripts=()
while IFS= read -r shell_script; do
  shell_scripts+=("$shell_script")
done < <(find "$ROOT_DIR/scripts" -type f -name '*.sh' | sort)
if [[ "${#shell_scripts[@]}" -gt 0 ]]; then
  if keep_going_active; then
    run_check "shellcheck" -- shellcheck --severity=error --exclude=SC1090,SC1091 "${shell_scripts[@]}"
  else
    run_cmd shellcheck --severity=error --exclude=SC1090,SC1091 "${shell_scripts[@]}"
  fi
fi

if keep_going_active; then
  run_check "quality-root-dir-prelude-check" -- make -C "$ROOT_DIR" quality-root-dir-prelude-check
  run_check "quality-infra-shell-source-graph-check" -- make -C "$ROOT_DIR" quality-infra-shell-source-graph-check
  run_check "quality-sdd-check-all" -- make -C "$ROOT_DIR" quality-sdd-check-all
else
  run_cmd make -C "$ROOT_DIR" quality-root-dir-prelude-check
  run_cmd make -C "$ROOT_DIR" quality-infra-shell-source-graph-check
  run_cmd make -C "$ROOT_DIR" quality-sdd-check-all
fi

_current_branch="$(git branch --show-current 2>/dev/null || true)"
if [[ "$_current_branch" =~ ^codex/[0-9]{4}-[0-9]{2}-[0-9]{2}- ]]; then
  _spec_slug="${_current_branch#codex/}"
  _spec_dir="$ROOT_DIR/specs/$_spec_slug"
  if [[ -d "$_spec_dir" ]]; then
    if [[ "${QUALITY_HOOKS_FORCE_FULL:-}" == "true" ]] || quality_spec_is_ready "$_spec_dir"; then
      if keep_going_active; then
        run_check "quality-spec-pr-ready" -- make -C "$ROOT_DIR" quality-spec-pr-ready
      else
        run_cmd make -C "$ROOT_DIR" quality-spec-pr-ready
      fi
    else
      log_info "skipping quality-spec-pr-ready: spec-not-ready"
      log_metric "quality_hooks_skip_total" "1" "phase=fast check=quality-spec-pr-ready reason=spec-not-ready"
    fi
  else
    log_info "skipping quality-spec-pr-ready: no-spec-dir"
    log_metric "quality_hooks_skip_total" "1" "phase=fast check=quality-spec-pr-ready reason=no-spec-dir"
  fi
fi

if blueprint_repo_is_generated_consumer; then
  log_metric "quality_ci_check_sync_total" "1" "status=skipped repo_mode=generated-consumer"
  log_info "skipping quality-ci-check-sync in generated-consumer repo"
else
  if keep_going_active; then
    run_check "quality-ci-check-sync" -- make -C "$ROOT_DIR" quality-ci-check-sync
  else
    run_cmd make -C "$ROOT_DIR" quality-ci-check-sync
  fi
  log_metric "quality_ci_check_sync_total" "1" "status=success repo_mode=template-source"
fi

if keep_going_active; then
  run_check "quality-docs-check-changed" -- make -C "$ROOT_DIR" quality-docs-check-changed
else
  if run_cmd make -C "$ROOT_DIR" quality-docs-check-changed; then
    log_metric "quality_docs_check_changed_total" "1" "status=success"
  else
    log_metric "quality_docs_check_changed_total" "1" "status=failure"
    exit 1
  fi
fi

# Infra checks: path-gated
_changed_paths="$(_quality_changed_paths)"
if [[ "${QUALITY_HOOKS_FORCE_FULL:-}" == "true" ]] || quality_paths_match_infra_gate "$_changed_paths"; then
  if keep_going_active; then
    run_check "infra-validate" -- make -C "$ROOT_DIR" infra-validate
  else
    run_cmd make -C "$ROOT_DIR" infra-validate
  fi
else
  log_info "skipping infra-validate: no-relevant-paths"
  log_metric "quality_hooks_skip_total" "1" "phase=fast check=infra-validate reason=no-relevant-paths"
fi

if [[ "${QUALITY_HOOKS_FORCE_FULL:-}" == "true" ]] || quality_paths_match_infra_gate "$_changed_paths"; then
  if keep_going_active; then
    run_check "infra-contract-test-fast" -- make -C "$ROOT_DIR" infra-contract-test-fast
  else
    run_cmd make -C "$ROOT_DIR" infra-contract-test-fast
  fi
else
  log_info "skipping infra-contract-test-fast: no-relevant-paths"
  log_metric "quality_hooks_skip_total" "1" "phase=fast check=infra-contract-test-fast reason=no-relevant-paths"
fi

if keep_going_active; then
  keep_going_finalize
fi

log_info "quality hooks fast gate completed"
