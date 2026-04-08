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

k8s_kubeconfig_server_url() {
  local kubeconfig_path="$1"
  python3 "$ROOT_DIR/scripts/lib/infra/k8s_wait_helpers.py" server-url "$kubeconfig_path"
}

k8s_kubeconfig_server_host() {
  local kubeconfig_path="$1"
  python3 "$ROOT_DIR/scripts/lib/infra/k8s_wait_helpers.py" server-host "$kubeconfig_path"
}

wait_for_kube_api_ready() {
  local kubeconfig_path="$1"
  local timeout_seconds="${2:-$(k8s_timeout_seconds slow)}"
  local request_timeout="${3:-10s}"

  require_command python3
  require_command kubectl

  if [[ ! -f "$kubeconfig_path" ]]; then
    log_fatal "kubeconfig not found: $kubeconfig_path"
  fi

  local server_url
  if ! server_url="$(k8s_kubeconfig_server_url "$kubeconfig_path")"; then
    log_fatal "unable to resolve kubernetes api server URL from kubeconfig: $kubeconfig_path"
  fi
  local server_host
  if ! server_host="$(k8s_kubeconfig_server_host "$kubeconfig_path")"; then
    log_fatal "unable to resolve kubernetes api hostname from kubeconfig: $kubeconfig_path"
  fi

  local start_epoch
  start_epoch="$(date +%s)"
  local deadline_epoch=$((start_epoch + timeout_seconds))
  local resolution_attempts=0
  local readiness_attempts=0

  log_info "waiting for kubernetes api readiness server=$server_url timeout=${timeout_seconds}s poll=${K8S_WAIT_POLL_SECONDS}s"

  # STACKIT can return a kubeconfig before the new SKE API hostname is fully
  # published. Resolve DNS first so subsequent kubectl readiness probes fail
  # for real API reasons instead of transient name lookup churn.
  while true; do
    resolution_attempts=$((resolution_attempts + 1))
    if python3 "$ROOT_DIR/scripts/lib/infra/k8s_wait_helpers.py" dns-resolves "$server_host"
    then
      break
    fi

    if (( $(date +%s) >= deadline_epoch )); then
      local elapsed_seconds=$(( $(date +%s) - start_epoch ))
      log_metric "k8s_hostname_resolution_attempts" "$resolution_attempts" "host=$server_host status=failure"
      log_metric "k8s_api_readiness_wait_seconds" "$elapsed_seconds" "host=$server_host status=failure phase=dns"
      log_fatal "timed out waiting for kubernetes api hostname resolution host=$server_host timeout=${timeout_seconds}s"
    fi
    sleep "$K8S_WAIT_POLL_SECONDS"
  done
  log_metric "k8s_hostname_resolution_attempts" "$resolution_attempts" "host=$server_host status=success"

  while true; do
    readiness_attempts=$((readiness_attempts + 1))
    if kubectl --kubeconfig "$kubeconfig_path" --request-timeout="$request_timeout" get --raw=/readyz >/dev/null 2>&1; then
      local elapsed_seconds=$(( $(date +%s) - start_epoch ))
      log_metric "k8s_api_readiness_attempts" "$readiness_attempts" "host=$server_host status=success"
      log_metric "k8s_api_readiness_wait_seconds" "$elapsed_seconds" "host=$server_host status=success phase=readyz"
      log_info "kubernetes api ready host=$server_host attempts=$readiness_attempts elapsed=${elapsed_seconds}s"
      return 0
    fi

    if (( $(date +%s) >= deadline_epoch )); then
      local elapsed_seconds=$(( $(date +%s) - start_epoch ))
      log_metric "k8s_api_readiness_attempts" "$readiness_attempts" "host=$server_host status=failure"
      log_metric "k8s_api_readiness_wait_seconds" "$elapsed_seconds" "host=$server_host status=failure phase=readyz"
      log_fatal "timed out waiting for kubernetes api readiness host=$server_host timeout=${timeout_seconds}s"
    fi
    sleep "$K8S_WAIT_POLL_SECONDS"
  done
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
