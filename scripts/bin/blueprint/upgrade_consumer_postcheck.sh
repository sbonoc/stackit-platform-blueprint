#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "blueprint_upgrade_consumer_postcheck"

usage() {
  cat <<'USAGE'
Usage: upgrade_consumer_postcheck.sh [--validate-report-path PATH] [--reconcile-report-path PATH] [--report-path PATH]
                                   [--plan-path PATH] [--apply-path PATH]

Run deterministic post-upgrade convergence checks after blueprint consumer upgrade.
This wrapper composes:
1) blueprint-upgrade-consumer-validate
2) merge-marker + reconcile bucket checks
3) repo-mode-aware optional docs hooks

Environment variables:
  BLUEPRINT_UPGRADE_VALIDATE_PATH         Default: artifacts/blueprint/upgrade_validate.json
  BLUEPRINT_UPGRADE_RECONCILE_REPORT_PATH Default: artifacts/blueprint/upgrade/upgrade_reconcile_report.json
  BLUEPRINT_UPGRADE_PLAN_PATH             Default: artifacts/blueprint/upgrade_plan.json
  BLUEPRINT_UPGRADE_APPLY_PATH            Default: artifacts/blueprint/upgrade_apply.json
  BLUEPRINT_UPGRADE_POSTCHECK_PATH        Default: artifacts/blueprint/upgrade_postcheck.json
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
require_command make
require_command git

blueprint_load_env_defaults
set_default_env BLUEPRINT_UPGRADE_VALIDATE_PATH "artifacts/blueprint/upgrade_validate.json"
set_default_env BLUEPRINT_UPGRADE_RECONCILE_REPORT_PATH "artifacts/blueprint/upgrade/upgrade_reconcile_report.json"
set_default_env BLUEPRINT_UPGRADE_PLAN_PATH "artifacts/blueprint/upgrade_plan.json"
set_default_env BLUEPRINT_UPGRADE_APPLY_PATH "artifacts/blueprint/upgrade_apply.json"
set_default_env BLUEPRINT_UPGRADE_POSTCHECK_PATH "artifacts/blueprint/upgrade_postcheck.json"

validate_report_path="$BLUEPRINT_UPGRADE_VALIDATE_PATH"
reconcile_report_path="$BLUEPRINT_UPGRADE_RECONCILE_REPORT_PATH"
plan_path="$BLUEPRINT_UPGRADE_PLAN_PATH"
apply_path="$BLUEPRINT_UPGRADE_APPLY_PATH"
postcheck_report_path="$BLUEPRINT_UPGRADE_POSTCHECK_PATH"

resolve_report_path() {
  local value="$1"
  if [[ "$value" = /* ]]; then
    printf '%s\n' "$value"
    return 0
  fi
  printf '%s/%s\n' "$ROOT_DIR" "$value"
}

emit_postcheck_report_metrics() {
  local report_path="$1"
  local python_exit=0

  while IFS='=' read -r key value; do
    [[ -n "$key" ]] || continue
    case "$key" in
    postcheck_status)
      log_metric "blueprint_upgrade_postcheck_status_total" "1" "status=$value"
      ;;
    postcheck_commands_total)
      log_metric "blueprint_upgrade_postcheck_commands_total" "$value"
      ;;
    postcheck_merge_markers_total)
      log_metric "blueprint_upgrade_postcheck_merge_markers_total" "$value"
      ;;
    postcheck_conflicts_unresolved_total)
      log_metric "blueprint_upgrade_postcheck_conflicts_unresolved_total" "$value"
      ;;
    postcheck_docs_hook_failed_targets_total)
      log_metric "blueprint_upgrade_postcheck_docs_hook_failed_targets_total" "$value"
      ;;
    postcheck_blocked_reasons_total)
      log_metric "blueprint_upgrade_postcheck_blocked_reasons_total" "$value"
      ;;
    postcheck_validate_failure_total)
      log_metric "blueprint_upgrade_postcheck_validate_failure_total" "$value"
      ;;
    postcheck_contract_load_error_total)
      log_metric "blueprint_upgrade_postcheck_contract_load_error_total" "$value"
      ;;
    esac
  done < <(
    python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_report_metrics.py" \
      postcheck \
      --report-path "$report_path"
  ) || python_exit=$?

  if [[ "$python_exit" -ne 0 ]]; then
    log_warn "failed parsing upgrade postcheck report for metrics"
  fi
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --validate-report-path)
    [[ "$#" -ge 2 ]] || log_fatal "--validate-report-path requires a value"
    validate_report_path="$2"
    shift 2
    ;;
  --reconcile-report-path)
    [[ "$#" -ge 2 ]] || log_fatal "--reconcile-report-path requires a value"
    reconcile_report_path="$2"
    shift 2
    ;;
  --report-path)
    [[ "$#" -ge 2 ]] || log_fatal "--report-path requires a value"
    postcheck_report_path="$2"
    shift 2
    ;;
  --plan-path)
    [[ "$#" -ge 2 ]] || log_fatal "--plan-path requires a value"
    plan_path="$2"
    shift 2
    ;;
  --apply-path)
    [[ "$#" -ge 2 ]] || log_fatal "--apply-path requires a value"
    apply_path="$2"
    shift 2
    ;;
  --help)
    usage
    exit 0
    ;;
  *)
    log_fatal "unknown argument: $1"
    ;;
  esac
done

log_info "running blueprint consumer upgrade postcheck report_path=${postcheck_report_path}"
postcheck_report_abs="$(resolve_report_path "$postcheck_report_path")"

if run_cmd "$ROOT_DIR/scripts/bin/blueprint/upgrade_consumer_validate.sh" \
  --report-path "$validate_report_path"; then
  validate_rc=0
else
  validate_rc=$?
fi

if run_cmd python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_consumer_postcheck.py" \
  --repo-root "$ROOT_DIR" \
  --validate-report-path "$validate_report_path" \
  --reconcile-report-path "$reconcile_report_path" \
  --plan-path "$plan_path" \
  --apply-path "$apply_path" \
  --output-path "$postcheck_report_path"; then
  postcheck_rc=0
else
  postcheck_rc=$?
fi

emit_postcheck_report_metrics "$postcheck_report_abs"

if [[ "$validate_rc" -ne 0 || "$postcheck_rc" -ne 0 ]]; then
  log_error "blueprint consumer upgrade postcheck failed (see ${postcheck_report_path})"
fi

if [[ "$validate_rc" -ne 0 ]]; then
  exit "$validate_rc"
fi
exit "$postcheck_rc"
