#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/blueprint/contract_runtime.sh"

start_script_metric_trap "blueprint_uplift_status"

usage() {
  cat <<'USAGE'
Usage: uplift_status.sh

Report blueprint uplift convergence status for tracked upstream issues in the
consumer backlog. Reads AGENTS.backlog.md (or BLUEPRINT_UPLIFT_BACKLOG_PATH),
detects unchecked Markdown issue links referencing BLUEPRINT_UPLIFT_REPO, queries
each issue state via the gh CLI, and classifies each as:
  required  — issue is CLOSED but unresolved backlog references remain
  aligned   — issue is CLOSED and all references are checked
  none      — issue is still OPEN

Environment variables:
  BLUEPRINT_UPLIFT_REPO         Upstream blueprint GitHub org/repo (e.g. sbonoc/stackit-platform-blueprint)
                                Defaults to BLUEPRINT_GITHUB_ORG/BLUEPRINT_GITHUB_REPO from blueprint/repo.init.env
  BLUEPRINT_UPLIFT_BACKLOG_PATH Backlog file path relative to repo root (default: AGENTS.backlog.md)
  BLUEPRINT_UPLIFT_STATUS_PATH  Output artifact path (default: artifacts/blueprint/uplift_status.json)
  BLUEPRINT_UPLIFT_STRICT       true|false — exit non-zero when action_required_count > 0
                                or query_failures > 0 or unknown_count > 0 (default: false)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command python3
require_command gh

blueprint_load_env_defaults

set_default_env BLUEPRINT_UPLIFT_REPO "${BLUEPRINT_GITHUB_ORG:-}/${BLUEPRINT_GITHUB_REPO:-}"
set_default_env BLUEPRINT_UPLIFT_BACKLOG_PATH "AGENTS.backlog.md"
set_default_env BLUEPRINT_UPLIFT_STATUS_PATH "artifacts/blueprint/uplift_status.json"
set_default_env BLUEPRINT_UPLIFT_STRICT "false"

strict_flag=""
if [[ "$(shell_normalize_bool_truefalse "$BLUEPRINT_UPLIFT_STRICT")" == "true" ]]; then
  strict_flag="--strict"
fi

log_info "blueprint-uplift-status repo=${BLUEPRINT_UPLIFT_REPO} backlog=${BLUEPRINT_UPLIFT_BACKLOG_PATH}"

uplift_rc=0
if run_cmd python3 "$ROOT_DIR/scripts/lib/blueprint/uplift_status.py" \
  --repo-root "$ROOT_DIR" \
  --uplift-repo "$BLUEPRINT_UPLIFT_REPO" \
  --backlog-path "$BLUEPRINT_UPLIFT_BACKLOG_PATH" \
  --output-path "$BLUEPRINT_UPLIFT_STATUS_PATH" \
  $strict_flag; then
  uplift_rc=0
else
  uplift_rc=$?
fi

# Emit metrics from the artifact
emit_uplift_metrics() {
  local report_path="$1"
  local python_exit=0

  while IFS='=' read -r key value; do
    [[ -n "$key" ]] || continue
    case "$key" in
    tracked_total)
      log_metric "blueprint_uplift_status_tracked_total" "$value"
      ;;
    open_count)
      log_metric "blueprint_uplift_status_issues_total" "$value" "state=open"
      ;;
    closed_count)
      log_metric "blueprint_uplift_status_issues_total" "$value" "state=closed"
      ;;
    unknown_count)
      log_metric "blueprint_uplift_status_issues_total" "$value" "state=unknown"
      ;;
    aligned_closed_count)
      log_metric "blueprint_uplift_status_aligned_total" "$value"
      ;;
    action_required_count)
      log_metric "blueprint_uplift_status_action_required_total" "$value"
      ;;
    query_failures)
      log_metric "blueprint_uplift_status_query_failures_total" "$value"
      ;;
    status)
      log_metric "blueprint_uplift_status_run_total" "1" "status=$value"
      ;;
    esac
  done < <(
    python3 "$ROOT_DIR/scripts/lib/blueprint/uplift_status.py" \
      --repo-root "$ROOT_DIR" \
      --uplift-repo "$BLUEPRINT_UPLIFT_REPO" \
      --backlog-path "$BLUEPRINT_UPLIFT_BACKLOG_PATH" \
      --output-path "$BLUEPRINT_UPLIFT_STATUS_PATH" \
      --emit-metrics \
      2>/dev/null
  ) || python_exit=$?

  if [[ "$python_exit" -ne 0 ]]; then
    log_warn "failed parsing uplift status report for metrics"
  fi
}

emit_uplift_metrics "$BLUEPRINT_UPLIFT_STATUS_PATH"

log_metric "blueprint_uplift_status_total" "1"
exit "$uplift_rc"
