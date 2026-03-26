#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows_api.sh"

start_script_metric_trap "infra_stackit_workflows_smoke"

if ! is_module_enabled workflows; then
  log_info "WORKFLOWS_ENABLED=false; skipping workflows smoke"
  exit 0
fi

workflows_init_env
workflows_api_init_env
if ! state_file_exists workflows_instance; then
  log_fatal "missing workflows instance state"
fi
if ! state_file_exists workflows_dag_deploy; then
  log_fatal "missing workflows dag deploy state"
fi

instance_state_file="$(state_file_path workflows_instance)"
instance_id="$(grep -E '^instance_id=' "$instance_state_file" | head -n1 | cut -d= -f2-)"
instance_status="$(grep -E '^health_status=' "$instance_state_file" | head -n1 | cut -d= -f2-)"
if [[ -z "$instance_status" ]]; then
  instance_status="unknown"
fi

validation_mode="artifact"
if tooling_is_execution_enabled; then
  if [[ -z "$instance_id" ]]; then
    log_fatal "missing workflows instance id in state; run infra-stackit-workflows-apply first"
  fi

  detail_path="/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances/$instance_id"
  response_file="$(mktemp)"
  trap 'rm -f "$response_file"' RETURN

  workflows_api_request GET "$detail_path" "" "$response_file" "200" >/dev/null
  instance_status="$(workflows_api_json_pick "$response_file" "$instance_status" "status" "state" "instance.status")"
  repo_url="$(workflows_api_json_pick "$response_file" "$STACKIT_WORKFLOWS_DAGS_REPO_URL" "dagsRepository.url" "dags_repository.url")"
  repo_branch="$(workflows_api_json_pick "$response_file" "$STACKIT_WORKFLOWS_DAGS_REPO_BRANCH" "dagsRepository.branch" "dags_repository.branch")"

  if [[ "$(printf '%s' "$instance_status" | tr '[:upper:]' '[:lower:]')" != "active" ]]; then
    log_fatal "workflows instance is not active; instance_id=$instance_id status=$instance_status"
  fi

  # Normalize '.git' suffix to avoid false negatives when API canonicalizes repository URLs.
  if [[ "${repo_url%.git}" != "${STACKIT_WORKFLOWS_DAGS_REPO_URL%.git}" ]]; then
    log_fatal "workflows dags repo mismatch expected=$STACKIT_WORKFLOWS_DAGS_REPO_URL actual=$repo_url"
  fi
  if [[ "$repo_branch" != "$STACKIT_WORKFLOWS_DAGS_REPO_BRANCH" ]]; then
    log_fatal "workflows dags repo branch mismatch expected=$STACKIT_WORKFLOWS_DAGS_REPO_BRANCH actual=$repo_branch"
  fi

  validation_mode="api"
else
  if [[ "$(printf '%s' "$instance_status" | tr '[:upper:]' '[:lower:]')" != "active" ]]; then
    log_fatal "workflows instance is not Active"
  fi
fi

run_cmd make -C "$ROOT_DIR" infra-stackit-workflows-dag-parse-smoke

state_file="$(write_state_file "workflows_smoke" \
  "status=passed" \
  "validation_mode=$validation_mode" \
  "instance_id=$instance_id" \
  "instance_status=$instance_status" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "workflows smoke state written to $state_file"
