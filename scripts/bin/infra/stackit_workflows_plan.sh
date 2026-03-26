#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows_api.sh"

start_script_metric_trap "infra_stackit_workflows_plan"

if ! is_module_enabled workflows; then
  log_info "WORKFLOWS_ENABLED=false; skipping workflows plan"
  exit 0
fi

workflows_init_env
workflows_api_init_env
provision_driver="api_contract"
provision_path="/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances"
ensure_dir "$ROOT_DIR/artifacts/infra"
payload_file="$ROOT_DIR/artifacts/infra/workflows_request_payload.json"
workflows_payload_json >"$payload_file"

state_file="$(write_state_file "workflows_plan" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "project_id=$STACKIT_PROJECT_ID" \
  "region=$STACKIT_REGION" \
  "display_name=$STACKIT_WORKFLOWS_INSTANCE_DISPLAY_NAME" \
  "version=$STACKIT_WORKFLOWS_VERSION" \
  "dags_repo_url=$STACKIT_WORKFLOWS_DAGS_REPO_URL" \
  "dags_repo_branch=$STACKIT_WORKFLOWS_DAGS_REPO_BRANCH" \
  "oidc_discovery_url=$STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL" \
  "payload_file=$payload_file" \
  "api_base_url=$STACKIT_WORKFLOWS_API_BASE_URL" \
  "api_endpoint_path=/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "workflows plan state written to $state_file"
