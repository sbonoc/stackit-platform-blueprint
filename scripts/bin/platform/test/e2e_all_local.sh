#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"

start_script_metric_trap "test_e2e_all_local"

usage() {
  cat <<'USAGE'
Usage: e2e_all_local.sh [--scope fast|full] [--execute]

Runs the aggregate local E2E chain:
- infra-provision-deploy (local-lite, observability=false)
- backend-test-e2e (always)
- touchpoints-test-e2e (full scope only)

Options:
  --scope     e2e coverage scope (`fast` or `full`, default: `fast`)
  --execute   force execute mode for infra-provision-deploy (DRY_RUN=false)

Budget knobs:
  E2E_FAST_BUDGET_SECONDS     max duration for --scope fast (default: 900)
  E2E_FULL_BUDGET_SECONDS     max duration for --scope full (default: 1800)
  E2E_BUDGET_ENFORCE          fail when budget exceeded (defaults to CI value)
USAGE
}

execute_mode="false"
scope="fast"

while (($#)); do
  case "${1:-}" in
  --execute)
    execute_mode="true"
    shift
    ;;
  --scope)
    if [[ $# -lt 2 ]]; then
      log_fatal "--scope requires a value (fast|full)"
    fi
    scope="$2"
    shift 2
    ;;
  --help)
    usage
    exit 0
    ;;
  *)
    log_fatal "unknown argument: ${1}"
    ;;
  esac
done

case "$scope" in
fast | full)
  ;;
*)
  log_fatal "invalid scope: $scope (expected fast|full)"
  ;;
esac

set_default_env BLUEPRINT_PROFILE "local-lite"
set_default_env OBSERVABILITY_ENABLED "false"
set_default_env E2E_FAST_BUDGET_SECONDS "900"
set_default_env E2E_FULL_BUDGET_SECONDS "1800"
set_default_env E2E_BUDGET_ENFORCE "$(shell_normalize_bool_truefalse "${CI:-false}")"

validate_budget_seconds() {
  local label="$1"
  local value="$2"
  local fallback="$3"
  if [[ "$value" =~ ^[0-9]+$ ]] && (( value > 0 )); then
    printf '%s\n' "$value"
    return 0
  fi
  log_warn "invalid ${label}=${value}; using ${fallback}"
  printf '%s\n' "$fallback"
}

lane_budget_seconds="$E2E_FAST_BUDGET_SECONDS"
lane_budget_fallback="900"
lane_budget_label="E2E_FAST_BUDGET_SECONDS"
if [[ "$scope" == "full" ]]; then
  lane_budget_seconds="$E2E_FULL_BUDGET_SECONDS"
  lane_budget_fallback="1800"
  lane_budget_label="E2E_FULL_BUDGET_SECONDS"
fi
lane_budget_seconds="$(validate_budget_seconds "$lane_budget_label" "$lane_budget_seconds" "$lane_budget_fallback")"

suite_start_epoch="$(now_epoch_seconds)"
log_info "running aggregate local e2e chain scope=$scope execute=$execute_mode budget_seconds=$lane_budget_seconds"

if [[ "$execute_mode" == "true" ]]; then
  log_info "running local execute-mode infra chain before aggregate e2e test lanes"
  run_cmd make -C "$ROOT_DIR" DRY_RUN=false BLUEPRINT_PROFILE="$BLUEPRINT_PROFILE" OBSERVABILITY_ENABLED="$OBSERVABILITY_ENABLED" infra-provision-deploy
else
  log_info "running local dry-run-state infra chain before aggregate e2e test lanes"
  run_cmd make -C "$ROOT_DIR" BLUEPRINT_PROFILE="$BLUEPRINT_PROFILE" OBSERVABILITY_ENABLED="$OBSERVABILITY_ENABLED" infra-provision-deploy
fi

run_cmd make -C "$ROOT_DIR" backend-test-e2e
if [[ "$scope" == "full" ]]; then
  run_cmd make -C "$ROOT_DIR" touchpoints-test-e2e
fi

duration_seconds="$(( $(now_epoch_seconds) - suite_start_epoch ))"
if (( duration_seconds > lane_budget_seconds )); then
  log_metric \
    "aggregate_e2e_budget_total" \
    "1" \
    "scope=$scope execute=$execute_mode status=exceeded duration_seconds=$duration_seconds budget_seconds=$lane_budget_seconds"
  if [[ "$(shell_normalize_bool_truefalse "$E2E_BUDGET_ENFORCE")" == "true" ]]; then
    log_fatal \
      "aggregate local e2e chain exceeded budget scope=$scope duration_seconds=$duration_seconds budget_seconds=$lane_budget_seconds"
  fi
  log_warn \
    "aggregate local e2e chain exceeded budget scope=$scope duration_seconds=$duration_seconds budget_seconds=$lane_budget_seconds"
else
  log_metric \
    "aggregate_e2e_budget_total" \
    "1" \
    "scope=$scope execute=$execute_mode status=within duration_seconds=$duration_seconds budget_seconds=$lane_budget_seconds"
fi
