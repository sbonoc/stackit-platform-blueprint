#!/usr/bin/env bash
set -euo pipefail

LOG_NAMESPACE="${LOG_NAMESPACE:-blueprint}"

_log_emit() {
  local level="$1"
  shift
  local ts
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  printf '[%s] [%s] [%s] %s\n' "$ts" "$LOG_NAMESPACE" "$level" "$*"
}

log_info() {
  _log_emit "INFO" "$*"
}

log_warn() {
  _log_emit "WARN" "$*" >&2
}

log_error() {
  _log_emit "ERROR" "$*" >&2
}

log_fatal() {
  _log_emit "FATAL" "$*" >&2
  exit 1
}

log_metric() {
  local metric_name="$1"
  local metric_value="$2"
  shift 2 || true
  local labels=""
  if (($#)); then
    labels=" $*"
  fi
  _log_emit "METRIC" "name=${metric_name} value=${metric_value}${labels}"
}
