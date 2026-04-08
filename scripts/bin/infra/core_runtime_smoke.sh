#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/k8s_wait.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"

start_script_metric_trap "infra_core_runtime_smoke"

usage() {
  cat <<'USAGE'
Usage: core_runtime_smoke.sh

Validates runtime core bootstrap state generated during infra-deploy.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! state_file_exists core_runtime_bootstrap; then
  log_warn "core_runtime_bootstrap state not found; run infra-deploy first"
  exit 0
fi

runtime_state="$ROOT_DIR/artifacts/infra/core_runtime_bootstrap.env"
if ! grep -q '^argocd_chart=' "$runtime_state"; then
  log_fatal "argocd_chart missing from core runtime state: $runtime_state"
fi
if ! grep -q '^external_secrets_chart=' "$runtime_state"; then
  log_fatal "external_secrets_chart missing from core runtime state: $runtime_state"
fi

cert_manager_state="present"
if ! grep -q '^cert_manager_chart=' "$runtime_state"; then
  cert_manager_state="legacy-missing"
  log_warn "cert_manager_chart missing from core runtime state (legacy artifact); rerun infra-deploy to refresh: $runtime_state"
fi

if [[ "$(tooling_execution_mode)" == "execute" ]] && command -v kubectl >/dev/null 2>&1; then
  prepare_cluster_access
  wait_for_deployment_if_present "argocd" "argocd-server" "$(k8s_timeout_kubectl normal)"
  wait_for_deployment_if_present "external-secrets" "external-secrets" "$(k8s_timeout_kubectl normal)"
  wait_for_deployment_if_present "cert-manager" "blueprint-cert-manager-cert-manager" "$(k8s_timeout_kubectl normal)"
fi

state_file="$(
  write_state_file "core_runtime_smoke" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "runtime_state=$runtime_state" \
    "cert_manager_state=$cert_manager_state" \
    "status=ok" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "core runtime smoke state written to $state_file"
