#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"

start_script_metric_trap "infra_core_runtime_bootstrap"

usage() {
  cat <<'USAGE'
Usage: core_runtime_bootstrap.sh

Bootstraps execution-ready runtime core components on the current cluster:
- installs/updates ArgoCD via Helm,
- installs/updates External Secrets Operator via Helm,
- installs/updates cert-manager via Helm,
- verifies CRD readiness in execution mode,
- writes state under artifacts/infra.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

wait_for_crd_established() {
  local crd_name="$1"
  local timeout_seconds="${2:-300}"
  local started_at
  local now
  local elapsed
  local conditions

  started_at="$(date +%s)"
  log_info "waiting for CRD to report Established=True: $crd_name"

  while true; do
    # Some clusters briefly return CRDs before `.status.conditions` is
    # populated, which makes `kubectl wait` fail with an accessor error. Poll
    # the CRD conditions directly so runtime bootstrap tolerates that window.
    conditions="$(kubectl get "crd/$crd_name" -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}' 2>/dev/null || true)"
    if printf '%s\n' "$conditions" | grep -qx 'Established=True'; then
      log_metric "runtime_crd_wait_total" "1" "crd=$crd_name status=ready"
      return 0
    fi

    now="$(date +%s)"
    elapsed="$((now - started_at))"
    if (( elapsed >= timeout_seconds )); then
      log_metric "runtime_crd_wait_total" "1" "crd=$crd_name status=timeout"
      log_fatal "timed out waiting for CRD to report Established=True: $crd_name"
    fi

    sleep 2
  done
}

wait_for_deployments_by_instance_label() {
  local namespace="$1"
  local helm_release="$2"
  local timeout_seconds="${3:-300}"

  local deployments
  deployments="$(kubectl get deployment --namespace "$namespace" -l "app.kubernetes.io/instance=$helm_release" -o name 2>/dev/null || true)"
  if [[ -z "$deployments" ]]; then
    log_warn "no deployments found for release=$helm_release namespace=$namespace; skipping rollout wait"
    return 0
  fi

  local deployment
  while IFS= read -r deployment; do
    [[ -n "$deployment" ]] || continue
    run_cmd kubectl rollout status "$deployment" --namespace "$namespace" --timeout="${timeout_seconds}s"
  done <<<"$deployments"
}

set_default_env ARGOCD_NAMESPACE "argocd"
set_default_env ARGOCD_HELM_RELEASE "blueprint-argocd"
set_default_env ARGOCD_HELM_CHART "argo/argo-cd"
set_default_env ARGOCD_HELM_CHART_VERSION "$ARGOCD_CHART_VERSION"

set_default_env EXTERNAL_SECRETS_NAMESPACE "external-secrets"
set_default_env EXTERNAL_SECRETS_HELM_RELEASE "blueprint-external-secrets"
set_default_env EXTERNAL_SECRETS_HELM_CHART "external-secrets/external-secrets"
set_default_env EXTERNAL_SECRETS_HELM_CHART_VERSION "$EXTERNAL_SECRETS_CHART_VERSION"

set_default_env CERT_MANAGER_NAMESPACE "cert-manager"
set_default_env CERT_MANAGER_HELM_RELEASE "blueprint-cert-manager"
set_default_env CERT_MANAGER_HELM_CHART "jetstack/cert-manager"
set_default_env CERT_MANAGER_HELM_CHART_VERSION "$CERT_MANAGER_CHART_VERSION"

argocd_values_file="$(local_core_helm_values_file "argocd")"
external_secrets_values_file="$(local_core_helm_values_file "external-secrets")"
cert_manager_values_file="$(local_core_helm_values_file "cert-manager")"

if [[ ! -f "$argocd_values_file" ]]; then
  log_fatal "missing ArgoCD values file: $argocd_values_file"
fi
if [[ ! -f "$external_secrets_values_file" ]]; then
  log_fatal "missing External Secrets values file: $external_secrets_values_file"
fi
if [[ ! -f "$cert_manager_values_file" ]]; then
  log_fatal "missing cert-manager values file: $cert_manager_values_file"
fi

prepare_cluster_access

run_helm_upgrade_install \
  "$ARGOCD_HELM_RELEASE" \
  "$ARGOCD_NAMESPACE" \
  "$ARGOCD_HELM_CHART" \
  "$ARGOCD_HELM_CHART_VERSION" \
  "$argocd_values_file"

run_helm_upgrade_install \
  "$EXTERNAL_SECRETS_HELM_RELEASE" \
  "$EXTERNAL_SECRETS_NAMESPACE" \
  "$EXTERNAL_SECRETS_HELM_CHART" \
  "$EXTERNAL_SECRETS_HELM_CHART_VERSION" \
  "$external_secrets_values_file"

run_helm_upgrade_install \
  "$CERT_MANAGER_HELM_RELEASE" \
  "$CERT_MANAGER_NAMESPACE" \
  "$CERT_MANAGER_HELM_CHART" \
  "$CERT_MANAGER_HELM_CHART_VERSION" \
  "$cert_manager_values_file"

verification_mode="dry-run-state"
if tooling_is_execution_enabled; then
  require_command kubectl

  wait_for_crd_established "applications.argoproj.io"
  wait_for_crd_established "applicationsets.argoproj.io"
  wait_for_crd_established "appprojects.argoproj.io"

  wait_for_crd_established "externalsecrets.external-secrets.io"
  wait_for_crd_established "secretstores.external-secrets.io"
  wait_for_crd_established "clustersecretstores.external-secrets.io"
  wait_for_crd_established "certificates.cert-manager.io"
  wait_for_crd_established "issuers.cert-manager.io"
  wait_for_crd_established "certificaterequests.cert-manager.io"

  wait_for_deployments_by_instance_label "$ARGOCD_NAMESPACE" "$ARGOCD_HELM_RELEASE"
  wait_for_deployments_by_instance_label "$EXTERNAL_SECRETS_NAMESPACE" "$EXTERNAL_SECRETS_HELM_RELEASE"
  wait_for_deployments_by_instance_label "$CERT_MANAGER_NAMESPACE" "$CERT_MANAGER_HELM_RELEASE"

  verification_mode="kubectl-crd-and-rollout"
fi

state_file="$(
  write_state_file "core_runtime_bootstrap" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "argocd_release=$ARGOCD_HELM_RELEASE" \
    "argocd_namespace=$ARGOCD_NAMESPACE" \
    "argocd_chart=$ARGOCD_HELM_CHART" \
    "argocd_chart_version=$ARGOCD_HELM_CHART_VERSION" \
    "argocd_values_file=$argocd_values_file" \
    "external_secrets_release=$EXTERNAL_SECRETS_HELM_RELEASE" \
    "external_secrets_namespace=$EXTERNAL_SECRETS_NAMESPACE" \
    "external_secrets_chart=$EXTERNAL_SECRETS_HELM_CHART" \
    "external_secrets_chart_version=$EXTERNAL_SECRETS_HELM_CHART_VERSION" \
    "external_secrets_values_file=$external_secrets_values_file" \
    "cert_manager_release=$CERT_MANAGER_HELM_RELEASE" \
    "cert_manager_namespace=$CERT_MANAGER_NAMESPACE" \
    "cert_manager_chart=$CERT_MANAGER_HELM_CHART" \
    "cert_manager_chart_version=$CERT_MANAGER_HELM_CHART_VERSION" \
    "cert_manager_values_file=$cert_manager_values_file" \
    "verification_mode=$verification_mode" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "core runtime bootstrap state written to $state_file"
