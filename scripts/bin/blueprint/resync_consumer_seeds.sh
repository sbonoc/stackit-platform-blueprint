#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "blueprint_resync_consumer_seeds"

usage() {
  cat <<'USAGE'
Usage: resync_consumer_seeds.sh [--dry-run] [--apply-safe | --apply-all] [--report-path PATH]

Resync generated-consumer seed files from scripts/templates/consumer/init.

Default mode is dry-run and only prints classification:
- auto-refresh: safe deterministic updates
- manual-merge: requires human merge decision

Options:
  --dry-run               preview classifications and planned changes (default).
  --apply-safe            apply only files classified as auto-refresh.
  --apply-all             apply all drifted/missing seeded files (overwrites manual-merge files).
  --report-path PATH      write JSON report to PATH (absolute or repo-relative).

Environment variables:
  BLUEPRINT_RESYNC_APPLY_SAFE=true
  BLUEPRINT_RESYNC_APPLY_ALL=true
  BLUEPRINT_RESYNC_REPORT_PATH=<path>
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
require_command git

blueprint_load_env_defaults

apply_mode="dry-run"
report_path="${BLUEPRINT_RESYNC_REPORT_PATH:-}"

case "${BLUEPRINT_RESYNC_APPLY_SAFE:-false}" in
1 | true | TRUE | True | yes | YES | on | ON)
  apply_mode="apply-safe"
  ;;
esac

case "${BLUEPRINT_RESYNC_APPLY_ALL:-false}" in
1 | true | TRUE | True | yes | YES | on | ON)
  if [[ "$apply_mode" != "dry-run" ]]; then
    log_fatal "BLUEPRINT_RESYNC_APPLY_SAFE and BLUEPRINT_RESYNC_APPLY_ALL are mutually exclusive"
  fi
  apply_mode="apply-all"
  ;;
esac

while [[ "$#" -gt 0 ]]; do
  case "$1" in
  --dry-run)
    apply_mode="dry-run"
    shift
    ;;
  --apply-safe)
    if [[ "$apply_mode" == "apply-all" ]]; then
      log_fatal "--apply-safe and --apply-all are mutually exclusive"
    fi
    apply_mode="apply-safe"
    shift
    ;;
  --apply-all)
    if [[ "$apply_mode" == "apply-safe" ]]; then
      log_fatal "--apply-safe and --apply-all are mutually exclusive"
    fi
    apply_mode="apply-all"
    shift
    ;;
  --report-path)
    [[ "$#" -ge 2 ]] || log_fatal "--report-path requires a value"
    report_path="$2"
    shift 2
    ;;
  *)
    log_fatal "unknown argument: $1"
    ;;
  esac
done

resync_args=(
  --repo-root "$ROOT_DIR"
)

case "$apply_mode" in
dry-run)
  resync_args+=(--dry-run)
  ;;
apply-safe)
  resync_args+=(--apply-safe)
  ;;
apply-all)
  resync_args+=(--apply-all)
  ;;
esac

if [[ -n "$report_path" ]]; then
  resync_args+=(--report-path "$report_path")
fi

run_cmd "$ROOT_DIR/scripts/lib/blueprint/resync_consumer_seeds.py" "${resync_args[@]}"
