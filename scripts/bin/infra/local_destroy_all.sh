#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/module_lifecycle.sh"

start_script_metric_trap "infra_local_destroy_all"

usage() {
  cat <<'USAGE'
Usage: local_destroy_all.sh

Destroys blueprint-managed local cluster resources only:
- runs destroy actions for local-capable optional modules,
- uninstalls core Helm releases,
- removes blueprint-managed namespaces from the selected local cluster,
- preserves the underlying Kubernetes cluster itself.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_local_profile; then
  log_fatal "infra-local-destroy-all requires local-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
fi

wait_for_namespace_deletion() {
  local namespace="$1"
  local timeout_seconds="${2:-180}"
  local started_at
  local now
  local phase

  if ! tooling_is_execution_enabled; then
    log_metric "local_destroy_all_namespace_wait_total" "1" "namespace=$namespace status=dry_run"
    return 0
  fi

  started_at="$(date +%s)"
  while true; do
    if ! kubectl get namespace "$namespace" >/dev/null 2>&1; then
      log_metric "local_destroy_all_namespace_wait_total" "1" "namespace=$namespace status=deleted"
      return 0
    fi

    now="$(date +%s)"
    if (( now - started_at >= timeout_seconds )); then
      phase="$(kubectl get namespace "$namespace" -o jsonpath='{.status.phase}' 2>/dev/null || true)"
      log_metric "local_destroy_all_namespace_wait_total" "1" "namespace=$namespace status=timeout"
      log_warn "namespace did not finish deleting before timeout namespace=$namespace phase=${phase:-unknown}"
      return 0
    fi

    sleep 2
  done
}

prepare_cluster_access

set_default_env ARGOCD_NAMESPACE "argocd"
set_default_env ARGOCD_HELM_RELEASE "blueprint-argocd"
set_default_env EXTERNAL_SECRETS_NAMESPACE "external-secrets"
set_default_env EXTERNAL_SECRETS_HELM_RELEASE "blueprint-external-secrets"
set_default_env CROSSPLANE_NAMESPACE "crossplane-system"
set_default_env CROSSPLANE_HELM_RELEASE "blueprint-crossplane"

local_modules=(
  observability
  langfuse
  postgres
  neo4j
  object-storage
  rabbitmq
  opensearch
  dns
  public-endpoints
  secrets-manager
  kms
  identity-aware-proxy
)

log_info "local destroy-all start profile=$BLUEPRINT_PROFILE context=$(active_kube_context_name)"

# Destroy modules first so namespace deletion is not blocked by Helm-managed or
# GitOps-managed resources that the blueprint explicitly owns.
run_all_modules_action destroy "${local_modules[@]}"

# The overlay contains Argo CD CRDs (`Application`, `AppProject`). On a fresh
# or partially torn-down workstation cluster those CRDs may already be gone, so
# local cleanup needs to degrade to a best-effort namespace teardown instead of
# failing before it can remove the remaining blueprint-managed resources.
if cluster_crd_exists "applications.argoproj.io" && cluster_crd_exists "appprojects.argoproj.io"; then
  log_metric "local_destroy_all_argocd_overlay_delete_total" "1" "status=executed"
  run_kustomize_delete "$(local_argocd_overlay_dir)"
else
  log_metric "local_destroy_all_argocd_overlay_delete_total" "1" "status=skipped_missing_crds"
  log_warn "skipping Argo CD overlay delete because Application/AppProject CRDs are not installed"
fi

run_kustomize_delete "$(argocd_base_dir)"
run_kustomize_delete "$(local_crossplane_kustomize_dir)"

run_helm_uninstall "$ARGOCD_HELM_RELEASE" "$ARGOCD_NAMESPACE"
run_helm_uninstall "$EXTERNAL_SECRETS_HELM_RELEASE" "$EXTERNAL_SECRETS_NAMESPACE"
run_helm_uninstall "$CROSSPLANE_HELM_RELEASE" "$CROSSPLANE_NAMESPACE"

for namespace in \
  apps \
  observability \
  envoy-gateway-system \
  network \
  security \
  messaging \
  data \
  "$ARGOCD_NAMESPACE" \
  "$EXTERNAL_SECRETS_NAMESPACE" \
  "$CROSSPLANE_NAMESPACE"; do
  if tooling_is_execution_enabled; then
    run_cmd kubectl delete namespace "$namespace" --ignore-not-found --wait=false
  else
    log_info "dry-run kubectl delete namespace $namespace --ignore-not-found --wait=false (set DRY_RUN=false to execute)"
  fi
done

# Local reprovision often happens immediately after this target, so wait for
# namespace deletion to settle before returning. Otherwise Helm can fail trying
# to recreate a namespace that is still in `Terminating`.
for namespace in \
  apps \
  observability \
  envoy-gateway-system \
  network \
  security \
  messaging \
  data \
  "$ARGOCD_NAMESPACE" \
  "$EXTERNAL_SECRETS_NAMESPACE" \
  "$CROSSPLANE_NAMESPACE"; do
  wait_for_namespace_deletion "$namespace"
done

state_file="$(
  write_state_file "local_destroy_all" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "kubectl_context=$(active_kube_context_name)" \
    "kubeconfig_path=$(active_kubeconfig_path)" \
    "kube_access_source=$(active_kube_access_source)" \
    "destroy_scope=local_cluster_resources" \
    "destroyed_modules=$(IFS=,; printf '%s' "${local_modules[*]}")" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "local destroy-all state written to $state_file"
log_info "infra local destroy-all complete"
