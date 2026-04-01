#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "blueprint_upgrade_consumer"

usage() {
  cat <<'USAGE'
Usage: upgrade_consumer.sh [--source URL|PATH] [--ref REF] [--apply | --dry-run] [--allow-dirty] [--allow-delete]
                         [--plan-path PATH] [--apply-path PATH] [--summary-path PATH]

Plan/apply a non-destructive generated-consumer blueprint upgrade from a pinned source ref.

Default mode is plan-only (dry-run).

Environment variables:
  BLUEPRINT_UPGRADE_SOURCE                Upgrade source repository URL/path.
                                          Default: remote.upstream.url when set, otherwise remote.origin.url.
  BLUEPRINT_UPGRADE_REF                   REQUIRED upgrade source ref (tag/branch/commit).
  BLUEPRINT_UPGRADE_APPLY                 Default: false (set true for apply mode).
  BLUEPRINT_UPGRADE_ALLOW_DIRTY           Default: false.
  BLUEPRINT_UPGRADE_ALLOW_DELETE          Default: false.
  BLUEPRINT_UPGRADE_PLAN_PATH             Default: artifacts/blueprint/upgrade_plan.json
  BLUEPRINT_UPGRADE_APPLY_PATH            Default: artifacts/blueprint/upgrade_apply.json
  BLUEPRINT_UPGRADE_SUMMARY_PATH          Default: artifacts/blueprint/upgrade_summary.md

Notes:
  - Apply mode enforces non-destructive 3-way merge behavior for diverged blueprint-managed files.
  - Use `make blueprint-upgrade-consumer-validate` after apply to run the post-upgrade validation bundle.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
require_command git

blueprint_load_env_defaults

is_truthy() {
  case "$1" in
  1 | true | TRUE | True | yes | YES | on | ON)
    return 0
    ;;
  *)
    return 1
    ;;
  esac
}

resolve_report_path() {
  local value="$1"
  if [[ "$value" = /* ]]; then
    printf '%s\n' "$value"
    return 0
  fi
  printf '%s/%s\n' "$ROOT_DIR" "$value"
}

emit_upgrade_report_metrics() {
  local plan_report_path="$1"
  local apply_report_path="$2"
  local python_exit=0

  while IFS='=' read -r key value; do
    [[ -n "$key" ]] || continue
    case "$key" in
    plan_total)
      log_metric "blueprint_upgrade_plan_entries_total" "$value"
      ;;
    plan_create)
      log_metric "blueprint_upgrade_plan_action_total" "$value" "action=create"
      ;;
    plan_update)
      log_metric "blueprint_upgrade_plan_action_total" "$value" "action=update"
      ;;
    plan_merge_required)
      log_metric "blueprint_upgrade_plan_action_total" "$value" "action=merge-required"
      ;;
    plan_skip)
      log_metric "blueprint_upgrade_plan_action_total" "$value" "action=skip"
      ;;
    plan_conflict)
      log_metric "blueprint_upgrade_plan_action_total" "$value" "action=conflict"
      ;;
    plan_required_manual_actions)
      log_metric "blueprint_upgrade_required_manual_action_total" "$value" "scope=plan"
      ;;
    apply_status)
      log_metric "blueprint_upgrade_apply_status_total" "1" "status=$value"
      ;;
    apply_total)
      log_metric "blueprint_upgrade_apply_results_total" "$value"
      ;;
    apply_applied_count)
      log_metric "blueprint_upgrade_apply_mutations_total" "$value"
      ;;
    apply_conflict)
      log_metric "blueprint_upgrade_apply_results_by_type_total" "$value" "result=conflict"
      ;;
    apply_merged)
      log_metric "blueprint_upgrade_apply_results_by_type_total" "$value" "result=merged"
      ;;
    apply_applied)
      log_metric "blueprint_upgrade_apply_results_by_type_total" "$value" "result=applied"
      ;;
    apply_deleted)
      log_metric "blueprint_upgrade_apply_results_by_type_total" "$value" "result=deleted"
      ;;
    apply_skipped)
      log_metric "blueprint_upgrade_apply_results_by_type_total" "$value" "result=skipped"
      ;;
    apply_planned_only)
      log_metric "blueprint_upgrade_apply_results_by_type_total" "$value" "result=planned-only"
      ;;
    apply_required_manual_actions)
      log_metric "blueprint_upgrade_required_manual_action_total" "$value" "scope=apply"
      ;;
    esac
  done < <(
    python3 "$ROOT_DIR/scripts/lib/blueprint/upgrade_report_metrics.py" \
      plan-apply \
      --plan-path "$plan_report_path" \
      --apply-path "$apply_report_path"
  ) || python_exit=$?

  if [[ "$python_exit" -ne 0 ]]; then
    log_warn "failed parsing upgrade plan/apply reports for metrics"
  fi
}

resolve_default_upgrade_source() {
  local upstream origin
  upstream="$(git -C "$ROOT_DIR" config --get remote.upstream.url 2>/dev/null || true)"
  if [[ -n "$upstream" ]]; then
    printf '%s\n' "$upstream"
    return 0
  fi
  origin="$(git -C "$ROOT_DIR" config --get remote.origin.url 2>/dev/null || true)"
  printf '%s\n' "$origin"
}

set_default_env BLUEPRINT_UPGRADE_APPLY false
set_default_env BLUEPRINT_UPGRADE_ALLOW_DIRTY false
set_default_env BLUEPRINT_UPGRADE_ALLOW_DELETE false
set_default_env BLUEPRINT_UPGRADE_PLAN_PATH "artifacts/blueprint/upgrade_plan.json"
set_default_env BLUEPRINT_UPGRADE_APPLY_PATH "artifacts/blueprint/upgrade_apply.json"
set_default_env BLUEPRINT_UPGRADE_SUMMARY_PATH "artifacts/blueprint/upgrade_summary.md"

upgrade_source="${BLUEPRINT_UPGRADE_SOURCE:-}"
if [[ -z "$upgrade_source" ]]; then
  upgrade_source="$(resolve_default_upgrade_source)"
fi
upgrade_ref="${BLUEPRINT_UPGRADE_REF:-}"
plan_path="$BLUEPRINT_UPGRADE_PLAN_PATH"
apply_path="$BLUEPRINT_UPGRADE_APPLY_PATH"
summary_path="$BLUEPRINT_UPGRADE_SUMMARY_PATH"

apply_enabled="false"
if is_truthy "${BLUEPRINT_UPGRADE_APPLY:-false}"; then
  apply_enabled="true"
fi
allow_dirty="false"
if is_truthy "${BLUEPRINT_UPGRADE_ALLOW_DIRTY:-false}"; then
  allow_dirty="true"
fi
allow_delete="false"
if is_truthy "${BLUEPRINT_UPGRADE_ALLOW_DELETE:-false}"; then
  allow_delete="true"
fi

while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --source)
    [[ "$#" -ge 2 ]] || log_fatal "--source requires a value"
    upgrade_source="$2"
    shift 2
    ;;
  --ref)
    [[ "$#" -ge 2 ]] || log_fatal "--ref requires a value"
    upgrade_ref="$2"
    shift 2
    ;;
  --apply)
    apply_enabled="true"
    shift
    ;;
  --dry-run)
    apply_enabled="false"
    shift
    ;;
  --allow-dirty)
    allow_dirty="true"
    shift
    ;;
  --allow-delete)
    allow_delete="true"
    shift
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
  --summary-path)
    [[ "$#" -ge 2 ]] || log_fatal "--summary-path requires a value"
    summary_path="$2"
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

if [[ -z "$upgrade_source" ]]; then
  log_fatal "unable to infer BLUEPRINT_UPGRADE_SOURCE; set it explicitly or configure remote.upstream.url/remote.origin.url"
fi
if [[ -z "$upgrade_ref" ]]; then
  log_fatal "BLUEPRINT_UPGRADE_REF is required (set env var or pass --ref)"
fi

upgrade_args=(
  --repo-root "$ROOT_DIR"
  --source "$upgrade_source"
  --ref "$upgrade_ref"
  --plan-path "$plan_path"
  --apply-path "$apply_path"
  --summary-path "$summary_path"
)

if [[ "$apply_enabled" == "true" ]]; then
  upgrade_args+=(--apply)
fi
if [[ "$allow_dirty" == "true" ]]; then
  upgrade_args+=(--allow-dirty)
fi
if [[ "$allow_delete" == "true" ]]; then
  upgrade_args+=(--allow-delete)
fi

log_info "running blueprint consumer upgrade source=${upgrade_source} ref=${upgrade_ref} apply=${apply_enabled}"
log_metric "blueprint_upgrade_apply_enabled" "$apply_enabled"
log_metric "blueprint_upgrade_allow_dirty" "$allow_dirty"
log_metric "blueprint_upgrade_allow_delete" "$allow_delete"

plan_report="$(resolve_report_path "$plan_path")"
apply_report="$(resolve_report_path "$apply_path")"

if run_cmd "$ROOT_DIR/scripts/lib/blueprint/upgrade_consumer.py" "${upgrade_args[@]}"; then
  upgrade_rc=0
else
  upgrade_rc=$?
fi

emit_upgrade_report_metrics "$plan_report" "$apply_report"
if [[ "$upgrade_rc" -ne 0 ]]; then
  log_error "blueprint consumer upgrade failed (see ${plan_path} and ${apply_path})"
fi
exit "$upgrade_rc"
