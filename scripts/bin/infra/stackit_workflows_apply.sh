#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows_api.sh"

start_script_metric_trap "infra_stackit_workflows_apply"

resolve_workflows_payload_file() {
  local payload_file=""
  if state_file_exists workflows_plan; then
    payload_file="$(grep -E '^payload_file=' "$(state_file_path workflows_plan)" | head -n1 | cut -d= -f2-)"
  fi

  if [[ -z "$payload_file" ]]; then
    payload_file="$ROOT_DIR/artifacts/infra/workflows_request_payload.json"
  fi

  if [[ ! -f "$payload_file" ]]; then
    ensure_dir "$ROOT_DIR/artifacts/infra"
    workflows_payload_json >"$payload_file"
  fi

  printf '%s' "$payload_file"
}

normalize_workflows_status() {
  local status_value="${1:-Active}"
  local lowered
  lowered="$(printf '%s' "$status_value" | tr '[:upper:]' '[:lower:]')"
  case "$lowered" in
  active)
    printf '%s' "Active"
    ;;
  pending)
    printf '%s' "Pending"
    ;;
  *)
    printf '%s' "$status_value"
    ;;
  esac
}

if ! is_module_enabled workflows; then
  log_info "WORKFLOWS_ENABLED=false; skipping workflows apply"
  exit 0
fi

workflows_init_env
workflows_api_init_env
if ! state_file_exists workflows_plan; then
  log_fatal "missing workflows plan artifact; run infra-stackit-workflows-plan first"
fi

# Keep Keycloak realm/client/admin prerequisites converged before calling the
# managed Workflows API identity provider contract.
run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_workflows_keycloak_reconcile.sh"

provision_driver="api_contract"
provision_path="/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances"

instance_name="$(workflows_compute_instance_name)"
instance_id="${STACKIT_WORKFLOWS_INSTANCE_ID:-$(workflows_compute_instance_id "$instance_name") }"
instance_id="${instance_id// /}"
instance_status="Active"
instance_fqdn="$(workflows_compute_instance_fqdn "$instance_name" "$instance_id")"
web_url="https://$instance_fqdn"
redirect_uri="$web_url/oauth-authorized/keycloak"
api_mode="simulated"
api_http_status="0"
keycloak_reconcile_state="none"
if state_file_exists workflows_keycloak_reconcile; then
  keycloak_reconcile_state="$(state_file_path workflows_keycloak_reconcile)"
fi

payload_file="$(resolve_workflows_payload_file)"
api_log="$ROOT_DIR/artifacts/infra/workflows_api_calls.log"
ensure_dir "$(dirname "$api_log")"

if tooling_is_execution_enabled; then
  list_path="/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances"
  response_file="$(mktemp)"
  list_file="$(mktemp)"
  trap 'rm -f "$response_file" "$list_file"' RETURN

  api_http_status="$(workflows_api_request POST "$list_path" "$payload_file" "$response_file" "200,201,202,409")"

  if [[ "$api_http_status" == "409" ]]; then
    api_http_status="$(workflows_api_request GET "$list_path" "" "$list_file" "200")"
    resolved_id="$(workflows_api_find_instance_id_by_display_name "$list_file" "$instance_name")"
    if [[ -z "$resolved_id" ]]; then
      log_fatal "workflows API conflict and no instance found for displayName=$instance_name"
    fi
    instance_id="$resolved_id"
    detail_path="/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances/$instance_id"
    api_http_status="$(workflows_api_request GET "$detail_path" "" "$response_file" "200")"
  fi

  instance_id="$(workflows_api_json_pick "$response_file" "$instance_id" "id" "instanceId" "instance.id" "metadata.id")"
  instance_name="$(workflows_api_json_pick "$response_file" "$instance_name" "displayName" "name" "instanceName")"
  instance_status="$(workflows_api_json_pick "$response_file" "$instance_status" "status" "state" "instance.status")"
  web_url="$(workflows_api_json_pick "$response_file" "$web_url" "endpointUrl" "endpoint.url" "webUrl" "instance.endpointUrl")"

  if [[ -z "$instance_id" ]]; then
    log_fatal "workflows API response did not include an instance id"
  fi
  if [[ -z "$web_url" || "$web_url" != http*://* ]]; then
    instance_fqdn="$(workflows_compute_instance_fqdn "$instance_name" "$instance_id")"
    web_url="https://$instance_fqdn"
  else
    instance_fqdn="$(printf '%s' "$web_url" | sed -E 's#^https?://([^/]+)/?.*$#\1#')"
  fi
  redirect_uri="$web_url/oauth-authorized/keycloak"
  api_mode="live"

  {
    echo "POST $list_path"
    echo "payload_file=$payload_file"
    echo "response_file=$response_file"
    cat "$response_file"
  } >"$api_log"
else
  cat >"$api_log" <<LOG
POST /projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/instances
payload_file=$payload_file
response={"status":"Active","instanceId":"$instance_id"}
LOG
fi

instance_status="$(normalize_workflows_status "$instance_status")"

state_file="$(write_state_file "workflows_instance" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "instance_id=$instance_id" \
  "instance_name=$instance_name" \
  "instance_fqdn=$instance_fqdn" \
  "web_url=$web_url" \
  "health_status=$instance_status" \
  "redirect_uri=$redirect_uri" \
  "oidc_client_id=$STACKIT_WORKFLOWS_OIDC_CLIENT_ID" \
  "oidc_discovery_url=$STACKIT_WORKFLOWS_OIDC_DISCOVERY_URL" \
  "keycloak_reconcile_state=$keycloak_reconcile_state" \
  "api_mode=$api_mode" \
  "api_http_status=$api_http_status" \
  "api_base_url=$STACKIT_WORKFLOWS_API_BASE_URL" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "workflows instance state written to $state_file"
log_info "workflows API trace written to $api_log"
