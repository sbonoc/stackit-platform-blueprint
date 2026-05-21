#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows_local.sh"
source "$ROOT_DIR/scripts/lib/infra/port_forward.sh"

start_script_metric_trap "infra_local_workflows_smoke"

if [[ "${WORKFLOWS_LOCAL_ENABLED:-false}" != "true" ]]; then
  log_info "WORKFLOWS_LOCAL_ENABLED=false; skipping local-workflows smoke"
  exit 0
fi

workflows_local_init_env
if ! state_file_exists local_workflows_deploy; then
  log_fatal "missing local-workflows deploy artifact; run infra-local-workflows-deploy first"
fi

start_port_forward "local-workflows-smoke" \
  "$WORKFLOWS_LOCAL_NAMESPACE" \
  "svc/${WORKFLOWS_LOCAL_HELM_RELEASE}-webserver" \
  "$WORKFLOWS_LOCAL_AIRFLOW_PORT" \
  "$WORKFLOWS_LOCAL_AIRFLOW_PORT"

if ! wait_for_local_port "local-workflows-smoke" "$WORKFLOWS_LOCAL_AIRFLOW_PORT"; then
  stop_port_forward "local-workflows-smoke"
  log_fatal "port-forward for local-workflows-smoke timed out on port $WORKFLOWS_LOCAL_AIRFLOW_PORT"
fi

public_url="$(workflows_local_public_url)"
health_url="${public_url}/health"
health_response="$(curl -sf --max-time 10 "$health_url" || true)"

if [[ -z "$health_response" ]]; then
  stop_port_forward "local-workflows-smoke"
  log_fatal "local-workflows /health check failed: no response from $health_url"
fi
if ! echo "$health_response" | grep -q '"healthy"'; then
  stop_port_forward "local-workflows-smoke"
  log_fatal "local-workflows /health check failed: status not healthy — response: $health_response"
fi

state_file="$(write_state_file "local_workflows_smoke" \
  "profile=$BLUEPRINT_PROFILE" \
  "status=passed" \
  "health_response=$health_response" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

stop_port_forward "local-workflows-smoke"
log_info "local-workflows smoke state written to $state_file"
