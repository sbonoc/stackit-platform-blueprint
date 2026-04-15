#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/port_forward.sh"

start_script_metric_trap "infra_port_forward"

usage() {
  cat <<'USAGE'
Usage:
  port_forward.sh start
  port_forward.sh stop
  port_forward.sh cleanup

Environment contract for start:
  PF_NAME           Port-forward registry key (default: app-runtime)
  PF_NAMESPACE      Kubernetes namespace (default: apps)
  PF_RESOURCE       Kubernetes resource ref (default: svc/backend-api)
  PF_LOCAL_PORT     Local port (default: 18080)
  PF_REMOTE_PORT    Remote port (default: 8080)
  PF_LOG_PATH       Optional log path (default: artifacts/infra/port-forward-<name>.log)
  PF_WAIT_READY     true|false, wait for local port readiness (default: true)
  PF_WAIT_TIMEOUT   Wait timeout seconds when PF_WAIT_READY=true (default: PORT_FORWARD_WAIT_TIMEOUT_SECONDS)

Environment contract for stop/cleanup:
  PF_NAME           Registry key for stop (default: app-runtime)
  PF_FORCE_KILL     true|false (default: PORT_FORWARD_FORCE_KILL)
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

action="${1:-}"
if [[ -z "$action" ]]; then
  usage
  exit 1
fi

set_default_env PF_NAME "app-runtime"
set_default_env PF_NAMESPACE "apps"
set_default_env PF_RESOURCE "svc/backend-api"
set_default_env PF_LOCAL_PORT "18080"
set_default_env PF_REMOTE_PORT "8080"
set_default_env PF_LOG_PATH "$ROOT_DIR/artifacts/infra/port-forward-${PF_NAME}.log"
set_default_env PF_WAIT_READY "true"
set_default_env PF_WAIT_TIMEOUT "$PORT_FORWARD_WAIT_TIMEOUT_SECONDS"
set_default_env PF_FORCE_KILL "$PORT_FORWARD_FORCE_KILL"

case "$action" in
start)
  start_port_forward \
    "$PF_NAME" \
    "$PF_NAMESPACE" \
    "$PF_RESOURCE" \
    "$PF_LOCAL_PORT" \
    "$PF_REMOTE_PORT" \
    "$PF_LOG_PATH"
  if [[ "$(tooling_normalize_bool "${PF_WAIT_READY:-true}")" == "true" ]]; then
    wait_for_local_port "$PF_NAME" "$PF_LOCAL_PORT" "$PF_WAIT_TIMEOUT"
  fi
  log_info "port-forward started name=$PF_NAME namespace=$PF_NAMESPACE resource=$PF_RESOURCE local=$PF_LOCAL_PORT remote=$PF_REMOTE_PORT"
  ;;
stop)
  stop_port_forward "$PF_NAME" "$PF_FORCE_KILL"
  log_info "port-forward stop completed name=$PF_NAME"
  ;;
cleanup)
  cleanup_port_forwards "$PF_FORCE_KILL"
  log_info "port-forward cleanup completed"
  ;;
*)
  log_fatal "unsupported action '$action' (use: start|stop|cleanup)"
  ;;
esac
