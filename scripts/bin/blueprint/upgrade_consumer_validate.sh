#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "blueprint_upgrade_consumer_validate"

usage() {
  cat <<'USAGE'
Usage: upgrade_consumer_validate.sh [--report-path PATH]

Run the post-upgrade validation bundle and strict unresolved merge-marker checks.

Environment variables:
  BLUEPRINT_UPGRADE_VALIDATE_PATH      Default: artifacts/blueprint/upgrade_validate.json
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

report_path="$BLUEPRINT_UPGRADE_VALIDATE_PATH"

resolve_report_path() {
  local value="$1"
  if [[ "$value" = /* ]]; then
    printf '%s\n' "$value"
    return 0
  fi
  printf '%s/%s\n' "$ROOT_DIR" "$value"
}

emit_validate_report_metrics() {
  local validate_report_path="$1"
  local python_exit=0

  while IFS='=' read -r key value; do
    [[ -n "$key" ]] || continue
    case "$key" in
    validate_status)
      log_metric "blueprint_upgrade_validate_status_total" "1" "status=$value"
      ;;
    validate_commands_total)
      log_metric "blueprint_upgrade_validate_commands_total" "$value"
      ;;
    validate_failed_targets_total)
      log_metric "blueprint_upgrade_validate_failed_targets_total" "$value"
      ;;
    validate_merge_markers_pre_total)
      log_metric "blueprint_upgrade_validate_merge_markers_total" "$value" "phase=pre"
      ;;
    validate_merge_markers_post_total)
      log_metric "blueprint_upgrade_validate_merge_markers_total" "$value" "phase=post"
      ;;
    validate_runtime_dependency_missing_total)
      log_metric "blueprint_upgrade_validate_runtime_dependency_missing_total" "$value"
      ;;
    esac
  done < <(
    python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_report_metrics.py" \
      validate \
      --report-path "$validate_report_path"
  ) || python_exit=$?

  if [[ "$python_exit" -ne 0 ]]; then
    log_warn "failed parsing upgrade validate report for metrics"
  fi
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --report-path)
    [[ "$#" -ge 2 ]] || log_fatal "--report-path requires a value"
    report_path="$2"
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

log_info "running blueprint consumer upgrade validation report_path=${report_path}"
validate_report="$(resolve_report_path "$report_path")"

if run_cmd "$ROOT_DIR/scripts/lib/blueprint/upgrade_consumer_validate.py" \
  --repo-root "$ROOT_DIR" \
  --report-path "$report_path"; then
  validate_rc=0
else
  validate_rc=$?
fi

emit_validate_report_metrics "$validate_report"
if [[ "$validate_rc" -ne 0 ]]; then
  log_error "blueprint consumer upgrade validation failed (see ${report_path})"
fi
exit "$validate_rc"
