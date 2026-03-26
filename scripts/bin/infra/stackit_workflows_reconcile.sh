#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows_api.sh"

start_script_metric_trap "infra_stackit_workflows_reconcile"

if ! is_module_enabled workflows; then
  log_info "WORKFLOWS_ENABLED=false; skipping workflows reconcile"
  exit 0
fi

workflows_init_env
workflows_api_init_env

active_instances="${STACKIT_WORKFLOWS_ACTIVE_INSTANCES_COUNT:-1}"
reconcile_source="state"

if tooling_is_execution_enabled; then
  list_path="/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances"
  list_file="$(mktemp)"
  trap 'rm -f "$list_file"' RETURN
  workflows_api_request GET "$list_path" "" "$list_file" "200" >/dev/null

  active_instances="$(workflows_api_count_instances_with_status "$list_file" "active")"
  reconcile_source="api"
fi

if [[ "${STACKIT_WORKFLOWS_REQUIRE_SINGLE_ACTIVE_INSTANCE:-true}" == "true" ]]; then
  if [[ "$active_instances" != "1" ]]; then
    log_fatal "expected exactly one active workflows instance; got $active_instances"
  fi
fi

if ! state_file_exists workflows_instance; then
  log_warn "workflows instance state not found; applying instance"
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_workflows_apply.sh"
fi

state_file="$(write_state_file "workflows_reconcile" \
  "status=reconciled" \
  "reconcile_source=$reconcile_source" \
  "active_instances_count=$active_instances" \
  "reconcile_existing_only=${STACKIT_WORKFLOWS_RECONCILE_EXISTING_ONLY:-false}" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "workflows reconcile state written to $state_file"
