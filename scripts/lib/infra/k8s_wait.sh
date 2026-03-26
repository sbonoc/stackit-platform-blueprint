#!/usr/bin/env bash
set -euo pipefail

k8s_wait_init_defaults() {
  : "${K8S_WAIT_POLL_SECONDS:=2}"
  : "${K8S_TIMEOUT_FAST_SECONDS:=45}"
  : "${K8S_TIMEOUT_NORMAL_SECONDS:=180}"
  : "${K8S_TIMEOUT_SLOW_SECONDS:=300}"
}

k8s_timeout_seconds() {
  local level="${1:-normal}"
  if [[ "$level" =~ ^[0-9]+$ ]]; then
    printf '%s' "$level"
    return 0
  fi
  case "$level" in
  fast)
    printf '%s' "$K8S_TIMEOUT_FAST_SECONDS"
    ;;
  normal)
    printf '%s' "$K8S_TIMEOUT_NORMAL_SECONDS"
    ;;
  slow)
    printf '%s' "$K8S_TIMEOUT_SLOW_SECONDS"
    ;;
  *)
    log_fatal "unsupported k8s timeout level: $level"
    ;;
  esac
}

k8s_timeout_kubectl() {
  printf '%ss' "$(k8s_timeout_seconds "${1:-normal}")"
}

wait_for_deployment_if_present() {
  local namespace="$1"
  local name="$2"
  local timeout="${3:-$(k8s_timeout_kubectl slow)}"

  if ! command -v kubectl >/dev/null 2>&1; then
    return 0
  fi
  if ! kubectl -n "$namespace" get deploy "$name" >/dev/null 2>&1; then
    return 0
  fi
  kubectl -n "$namespace" rollout status "deploy/$name" --timeout="$timeout"
}

k8s_wait_init_defaults
