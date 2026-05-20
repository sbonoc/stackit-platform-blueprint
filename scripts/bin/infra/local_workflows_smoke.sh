#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/workflows_local.sh"

start_script_metric_trap "infra_local_workflows_smoke"

if [[ "${WORKFLOWS_LOCAL_ENABLED:-false}" != "true" ]]; then
  log_info "WORKFLOWS_LOCAL_ENABLED=false; skipping local-workflows smoke"
  exit 0
fi

workflows_local_init_env
if ! state_file_exists local_workflows_deploy; then
  log_fatal "missing local-workflows deploy artifact; run infra-local-workflows-deploy first"
fi

public_url="$(workflows_local_public_url)"
health_url="${public_url}/health"
health_response="$(curl -sf --max-time 10 "$health_url" || true)"

if [[ -z "$health_response" ]]; then
  log_fatal "local-workflows /health check failed: no response from $health_url"
fi

state_file="$(write_state_file "local_workflows_smoke" \
  "profile=$BLUEPRINT_PROFILE" \
  "status=passed" \
  "health_response=$health_response" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "local-workflows smoke state written to $state_file"
