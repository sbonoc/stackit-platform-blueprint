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

start_script_metric_trap "infra_stackit_workflows_dag_deploy"

if ! is_module_enabled workflows; then
  log_info "WORKFLOWS_ENABLED=false; skipping workflows dag deploy"
  exit 0
fi

workflows_init_env
workflows_api_init_env
if ! state_file_exists workflows_instance; then
  log_fatal "missing workflows instance state; run infra-stackit-workflows-apply first"
fi
if [[ ! -d "$ROOT_DIR/dags" ]]; then
  log_fatal "missing dags directory: $ROOT_DIR/dags"
fi

instance_id="$(grep -E '^instance_id=' "$(state_file_path workflows_instance)" | head -n1 | cut -d= -f2-)"
if [[ -z "$instance_id" ]]; then
  instance_id="${STACKIT_WORKFLOWS_INSTANCE_ID:-}"
fi
if [[ -z "$instance_id" ]]; then
  log_fatal "missing workflows instance id; run infra-stackit-workflows-apply first"
fi

dag_count="$(find "$ROOT_DIR/dags" -type f -name '*.py' | wc -l | tr -d ' ')"
api_mode="simulated"
api_http_status="0"

if tooling_is_execution_enabled; then
  payload_file="$(mktemp)"
  response_file="$(mktemp)"
  trap 'rm -f "$payload_file" "$response_file"' RETURN

  cat >"$payload_file" <<JSON
{
  "url": "$STACKIT_WORKFLOWS_DAGS_REPO_URL",
  "branch": "$STACKIT_WORKFLOWS_DAGS_REPO_BRANCH",
  "auth": {
    "type": "basic",
    "username": "$STACKIT_WORKFLOWS_DAGS_REPO_USERNAME",
    "password": "$STACKIT_WORKFLOWS_DAGS_REPO_TOKEN"
  }
}
JSON

  endpoint="/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances/$instance_id/dags-repository"
  api_http_status="$(workflows_api_request PATCH "$endpoint" "$payload_file" "$response_file" "200,202")"
  api_mode="live"
fi

state_file="$(write_state_file "workflows_dag_deploy" \
  "status=synced" \
  "api_mode=$api_mode" \
  "api_http_status=$api_http_status" \
  "instance_id=$instance_id" \
  "dags_repo_url=$STACKIT_WORKFLOWS_DAGS_REPO_URL" \
  "dags_repo_branch=$STACKIT_WORKFLOWS_DAGS_REPO_BRANCH" \
  "dag_file_count=$dag_count" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "workflows DAG deploy state written to $state_file"
