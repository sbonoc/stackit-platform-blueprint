#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows_api.sh"

start_script_metric_trap "infra_stackit_workflows_destroy"

instance_id="${STACKIT_WORKFLOWS_INSTANCE_ID:-}"
if [[ -z "$instance_id" && -f "$(state_file_path workflows_instance)" ]]; then
  instance_id="$(grep -E '^instance_id=' "$(state_file_path workflows_instance)" | head -n1 | cut -d= -f2-)"
fi

api_mode="skipped"
api_http_status="0"
if tooling_is_execution_enabled; then
  if ! is_stackit_profile; then
    log_fatal "live workflows destroy requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
  fi

  set_default_env STACKIT_WORKFLOWS_API_BASE_URL "https://workflows.api.stackit.cloud/v1alpha"
  set_default_env STACKIT_WORKFLOWS_API_TIMEOUT_SECONDS "30"
  set_default_env STACKIT_WORKFLOWS_API_TOKEN "${STACKIT_WORKFLOWS_ACCESS_TOKEN:-}"
  require_command curl
  require_env_vars STACKIT_PROJECT_ID STACKIT_REGION STACKIT_WORKFLOWS_API_TOKEN

  if [[ -n "$instance_id" ]]; then
    response_file="$(mktemp)"
    trap 'rm -f "$response_file"' RETURN
    endpoint="/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances/$instance_id"
    api_http_status="$(workflows_api_request DELETE "$endpoint" "" "$response_file" "200,202,204,404")"
    api_mode="live"
  else
    log_warn "no workflows instance id found; skipping API delete"
    api_mode="live-no-instance-id"
  fi
fi

remove_state_files_by_prefix "workflows_"
rm -f "$ROOT_DIR/artifacts/infra/workflows_request_payload.json" "$ROOT_DIR/artifacts/infra/workflows_api_calls.log"

state_file="$(write_state_file "workflows_destroy" \
  "api_mode=$api_mode" \
  "api_http_status=$api_http_status" \
  "instance_id=$instance_id" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "workflows artifacts destroyed"
log_info "workflows destroy state written to $state_file"
