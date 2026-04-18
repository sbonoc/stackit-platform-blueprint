#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "blueprint_upgrade_consumer_preflight"

usage() {
  cat <<'USAGE'
Usage: upgrade_consumer_preflight.sh [--source URL|PATH] [--ref REF] [--allow-dirty] [--allow-delete]
                                    [--plan-path PATH] [--apply-path PATH] [--summary-path PATH]
                                    [--preflight-path PATH] [--reconcile-report-path PATH]

Run a plan-only generated-consumer upgrade preflight and emit machine-readable guidance:
- auto-apply candidates
- manual-merge/conflict candidates
- required manual actions + follow-up commands

Environment variables:
  BLUEPRINT_UPGRADE_SOURCE                Upgrade source repository URL/path.
                                          Default: remote.upstream.url when set, otherwise remote.origin.url.
  BLUEPRINT_UPGRADE_REF                   REQUIRED upgrade source ref (tag/branch/commit).
  BLUEPRINT_UPGRADE_PLAN_PATH             Default: artifacts/blueprint/upgrade_plan.json
  BLUEPRINT_UPGRADE_APPLY_PATH            Default: artifacts/blueprint/upgrade_apply.json
  BLUEPRINT_UPGRADE_SUMMARY_PATH          Default: artifacts/blueprint/upgrade_summary.md
  BLUEPRINT_UPGRADE_PREFLIGHT_PATH        Default: artifacts/blueprint/upgrade_preflight.json
  BLUEPRINT_UPGRADE_RECONCILE_REPORT_PATH Default: artifacts/blueprint/upgrade/upgrade_reconcile_report.json
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3

blueprint_load_env_defaults

set_default_env BLUEPRINT_UPGRADE_PLAN_PATH "artifacts/blueprint/upgrade_plan.json"
set_default_env BLUEPRINT_UPGRADE_APPLY_PATH "artifacts/blueprint/upgrade_apply.json"
set_default_env BLUEPRINT_UPGRADE_SUMMARY_PATH "artifacts/blueprint/upgrade_summary.md"
set_default_env BLUEPRINT_UPGRADE_PREFLIGHT_PATH "artifacts/blueprint/upgrade_preflight.json"
set_default_env BLUEPRINT_UPGRADE_RECONCILE_REPORT_PATH "artifacts/blueprint/upgrade/upgrade_reconcile_report.json"

plan_path="$BLUEPRINT_UPGRADE_PLAN_PATH"
apply_path="$BLUEPRINT_UPGRADE_APPLY_PATH"
summary_path="$BLUEPRINT_UPGRADE_SUMMARY_PATH"
preflight_path="$BLUEPRINT_UPGRADE_PREFLIGHT_PATH"
reconcile_report_path="$BLUEPRINT_UPGRADE_RECONCILE_REPORT_PATH"

forward_args=()
while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --apply)
    log_fatal "preflight is plan-only; omit --apply and use make blueprint-upgrade-consumer for apply mode"
    ;;
  --dry-run)
    shift
    ;;
  --plan-path)
    [[ "$#" -ge 2 ]] || log_fatal "--plan-path requires a value"
    plan_path="$2"
    forward_args+=("$1" "$2")
    shift 2
    ;;
  --apply-path)
    [[ "$#" -ge 2 ]] || log_fatal "--apply-path requires a value"
    apply_path="$2"
    forward_args+=("$1" "$2")
    shift 2
    ;;
  --summary-path)
    [[ "$#" -ge 2 ]] || log_fatal "--summary-path requires a value"
    summary_path="$2"
    forward_args+=("$1" "$2")
    shift 2
    ;;
  --preflight-path)
    [[ "$#" -ge 2 ]] || log_fatal "--preflight-path requires a value"
    preflight_path="$2"
    shift 2
    ;;
  --reconcile-report-path)
    [[ "$#" -ge 2 ]] || log_fatal "--reconcile-report-path requires a value"
    reconcile_report_path="$2"
    shift 2
    ;;
  --help)
    usage
    exit 0
    ;;
  *)
    forward_args+=("$1")
    shift
    ;;
  esac
done

log_info "running blueprint upgrade preflight source=${BLUEPRINT_UPGRADE_SOURCE:-auto} ref=${BLUEPRINT_UPGRADE_REF:-unset}"
if [[ "${#forward_args[@]}" -gt 0 ]]; then
  run_cmd "$ROOT_DIR/scripts/bin/blueprint/upgrade_consumer.sh" \
    --dry-run \
    --plan-path "$plan_path" \
    --apply-path "$apply_path" \
    --summary-path "$summary_path" \
    --reconcile-report-path "$reconcile_report_path" \
    "${forward_args[@]}"
else
  run_cmd "$ROOT_DIR/scripts/bin/blueprint/upgrade_consumer.sh" \
    --dry-run \
    --plan-path "$plan_path" \
    --apply-path "$apply_path" \
    --summary-path "$summary_path" \
    --reconcile-report-path "$reconcile_report_path"
fi

run_cmd python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_preflight.py" \
  --repo-root "$ROOT_DIR" \
  --plan-path "$plan_path" \
  --apply-path "$apply_path" \
  --reconcile-report-path "$reconcile_report_path" \
  --output-path "$preflight_path"

log_metric "blueprint_upgrade_preflight_report_total" "1" "status=success"
