#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/stackit_layers.sh"

start_script_metric_trap "infra_stackit_foundation_destroy"

usage() {
  cat <<'USAGE'
Usage: stackit_foundation_destroy.sh

Runs terraform destroy for the STACKIT foundation layer.

Environment variables:
  STACKIT_FOUNDATION_NAMESPACE_DELETE_TIMEOUT_SECONDS  Best-effort wait for blueprint namespace deletion before SKE destroy (default: 300)
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

set_default_env STACKIT_FOUNDATION_NAMESPACE_DELETE_TIMEOUT_SECONDS "300"
STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS="not_started"

stackit_foundation_prepare_namespace_cleanup_access() {
  local kubeconfig_path
  local fetch_status=0
  local current_context=""

  kubeconfig_path="$(stackit_kubeconfig_path)"
  if [[ ! -f "$kubeconfig_path" ]]; then
    log_info "STACKIT kubeconfig not found for namespace cleanup; fetching current foundation kubeconfig path=$kubeconfig_path"
    set +e
    run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_fetch_kubeconfig.sh"
    fetch_status=$?
    set -e
    if [[ "$fetch_status" -ne 0 ]]; then
      STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS="skipped_kubeconfig_fetch_failed"
      log_warn "skipping STACKIT namespace cleanup because kubeconfig fetch failed status=$fetch_status"
      log_metric "stackit_foundation_namespace_cleanup_total" "1" "status=skipped_kubeconfig_fetch_failed"
      return 1
    fi
  fi

  export KUBECONFIG="$kubeconfig_path"
  current_context="$(kubectl --kubeconfig "$kubeconfig_path" config current-context 2>/dev/null || true)"
  export BLUEPRINT_ACTIVE_KUBECONFIG="$kubeconfig_path"
  export BLUEPRINT_ACTIVE_KUBE_CONTEXT="${current_context:-unset}"
  export BLUEPRINT_ACTIVE_KUBE_SOURCE="stackit-kubeconfig"

  if ! kubectl --kubeconfig "$kubeconfig_path" --request-timeout=10s get namespace default >/dev/null 2>&1; then
    STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS="skipped_cluster_unreachable"
    log_warn "skipping STACKIT namespace cleanup because cluster access is unavailable kubeconfig=$kubeconfig_path"
    log_metric "stackit_foundation_namespace_cleanup_total" "1" "status=skipped_cluster_unreachable"
    return 1
  fi

  return 0
}

stackit_foundation_cleanup_namespaces_before_destroy() {
  local cleanup_status=0

  if ! tooling_is_execution_enabled; then
    STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS="dry_run"
    log_metric "stackit_foundation_namespace_cleanup_total" "1" "status=dry_run"
    delete_blueprint_managed_namespaces \
      "$STACKIT_FOUNDATION_NAMESPACE_DELETE_TIMEOUT_SECONDS" \
      "stackit_foundation_namespace_cleanup"
    return 0
  fi

  if ! warn_if_missing_command kubectl; then
    STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS="skipped_missing_kubectl"
    log_metric "stackit_foundation_namespace_cleanup_total" "1" "status=skipped_missing_kubectl"
    return 0
  fi

  if ! stackit_foundation_prepare_namespace_cleanup_access; then
    return 0
  fi

  # Runtime workloads can keep cloud load balancers, target groups, and route
  # attachments alive longer than the SKE control plane delete expects. Clear
  # blueprint-managed namespaces first so the cluster drains before Terraform
  # asks STACKIT to delete the cluster itself.
  log_info "deleting blueprint-managed namespaces before STACKIT foundation destroy context=${BLUEPRINT_ACTIVE_KUBE_CONTEXT:-unset}"
  set +e
  delete_blueprint_managed_namespaces \
    "$STACKIT_FOUNDATION_NAMESPACE_DELETE_TIMEOUT_SECONDS" \
    "stackit_foundation_namespace_cleanup"
  cleanup_status=$?
  set -e
  if [[ "$cleanup_status" -ne 0 ]]; then
    STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS="partial_failure"
    log_warn "namespace cleanup encountered errors before STACKIT destroy; continuing with Terraform destroy status=$cleanup_status"
    log_metric "stackit_foundation_namespace_cleanup_total" "1" "status=partial_failure"
    return 0
  fi
  STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS="executed"
  log_metric "stackit_foundation_namespace_cleanup_total" "1" "status=executed"
}

stackit_layer_preflight "foundation"
foundation_dir="$(stackit_layer_dir "foundation")"
backend_file="$(stackit_layer_backend_file "foundation")"
var_file="$(stackit_layer_var_file "foundation")"
tf_var_args=()
while IFS= read -r arg; do
  [[ -n "$arg" ]] || continue
  tf_var_args+=("$arg")
done < <(stackit_layer_var_args "foundation")
stackit_foundation_cleanup_namespaces_before_destroy
run_terraform_action_with_backend destroy "$foundation_dir" "$backend_file" "$var_file" "${tf_var_args[@]}"

state_file="$(
  write_state_file "stackit_foundation_destroy" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "environment=$(profile_environment)" \
    "terraform_dir=$foundation_dir" \
    "backend_file=$backend_file" \
    "var_file=$var_file" \
    "tfstate_credential_source=${STACKIT_TFSTATE_CREDENTIAL_SOURCE:-unknown}" \
    "namespace_cleanup_status=$STACKIT_FOUNDATION_NAMESPACE_CLEANUP_STATUS" \
    "namespace_delete_timeout_seconds=$STACKIT_FOUNDATION_NAMESPACE_DELETE_TIMEOUT_SECONDS" \
    "action=destroy" \
    "tooling_mode=$(tooling_execution_mode)" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "stackit foundation destroy state written to $state_file"
