#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/k8s_wait.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_stackit_runtime_prerequisites"

usage() {
  cat <<'USAGE'
Usage: stackit_runtime_prerequisites.sh

Validates STACKIT runtime deployment prerequisites.

Optional environment variables:
  STACKIT_RUNTIME_KUBECONFIG_MODE        fetch|refresh|skip (default: fetch)
  STACKIT_FOUNDATION_KUBECONFIG_OUTPUT   Kubeconfig output path
  STACKIT_RUNTIME_GITOPS_REPO_URL        Optional GitOps repo URL (must end with .git when set)
  K8S_WAIT_POLL_SECONDS                  Readiness poll interval for kube API waits
  K8S_TIMEOUT_SLOW_SECONDS               Readiness timeout for freshly created kube APIs
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_stackit_profile; then
  log_fatal "infra-stackit-runtime-prerequisites requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

if tooling_is_execution_enabled; then
  require_env_vars STACKIT_PROJECT_ID STACKIT_REGION
else
  set_default_env STACKIT_PROJECT_ID "${BLUEPRINT_STACKIT_PROJECT_ID:-project-placeholder}"
  set_default_env STACKIT_REGION "${BLUEPRINT_STACKIT_REGION:-eu01}"
fi
set_default_env STACKIT_RUNTIME_KUBECONFIG_MODE "fetch"
set_default_env STACKIT_FOUNDATION_KUBECONFIG_OUTPUT "${HOME}/.kube/stackit-${BLUEPRINT_PROFILE}.yaml"

kubeconfig_mode="$STACKIT_RUNTIME_KUBECONFIG_MODE"
case "$kubeconfig_mode" in
fetch | refresh | skip)
  ;;
*)
  log_fatal "unsupported STACKIT_RUNTIME_KUBECONFIG_MODE=$kubeconfig_mode (expected fetch|refresh|skip)"
  ;;
esac

kubeconfig_output="$STACKIT_FOUNDATION_KUBECONFIG_OUTPUT"
if [[ "$kubeconfig_output" != /* ]]; then
  kubeconfig_output="$ROOT_DIR/$kubeconfig_output"
fi

if [[ "$kubeconfig_mode" == "refresh" ]]; then
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_refresh_kubeconfig.sh"
elif [[ "$kubeconfig_mode" == "fetch" && ! -f "$kubeconfig_output" ]]; then
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh"
fi

if [[ "$kubeconfig_mode" != "skip" && ! -f "$kubeconfig_output" ]]; then
  log_fatal "missing kubeconfig at $kubeconfig_output; run make infra-stackit-foundation-fetch-kubeconfig"
fi

if [[ -n "${STACKIT_RUNTIME_GITOPS_REPO_URL:-}" && ! "${STACKIT_RUNTIME_GITOPS_REPO_URL}" =~ \.git$ ]]; then
  log_fatal "STACKIT_RUNTIME_GITOPS_REPO_URL must end with .git when provided"
fi

kube_api_server="none"
kube_api_status="skipped"
if [[ -f "$kubeconfig_output" ]]; then
  kube_api_server="$(k8s_kubeconfig_server_url "$kubeconfig_output" 2>/dev/null || echo "unknown")"
fi

if tooling_is_execution_enabled && [[ -f "$kubeconfig_output" ]]; then
  # Fresh STACKIT kubeconfigs can arrive before the SKE API hostname is
  # resolvable everywhere. Gate deploy-time kubectl calls on explicit API
  # readiness so runtime seeding/bootstrap do not fail on transient DNS lag.
  wait_for_kube_api_ready "$kubeconfig_output" "$(k8s_timeout_seconds slow)"
  kube_api_status="ready"
fi

state_file="$(
  write_state_file "stackit_runtime_prerequisites" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "project_id=$STACKIT_PROJECT_ID" \
    "region=$STACKIT_REGION" \
    "kubeconfig_mode=$kubeconfig_mode" \
    "kubeconfig_output=$kubeconfig_output" \
    "kube_api_server=$kube_api_server" \
    "kube_api_status=$kube_api_status" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "STACKIT runtime prerequisites passed api_server=$kube_api_server kube_api_status=$kube_api_status"
log_info "stackit runtime prerequisites state written to $state_file"
