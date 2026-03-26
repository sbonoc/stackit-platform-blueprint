#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"

start_script_metric_trap "infra_local_crossplane_bootstrap"

usage() {
  cat <<'USAGE'
Usage: local_crossplane_bootstrap.sh

Bootstraps local Crossplane core provisioning baseline:
- applies local crossplane kustomize base,
- installs/updates Crossplane Helm chart,
- verifies Crossplane API readiness in execution mode,
- writes execution state under artifacts/infra.
USAGE
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! is_local_profile; then
  log_info "BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE is not local-*; skipping local crossplane bootstrap"
  exit 0
fi

set_default_env CROSSPLANE_NAMESPACE "crossplane-system"
set_default_env CROSSPLANE_HELM_RELEASE "blueprint-crossplane"
set_default_env CROSSPLANE_HELM_CHART "crossplane-stable/crossplane"
set_default_env CROSSPLANE_HELM_CHART_VERSION "$CROSSPLANE_CHART_VERSION"

crossplane_values_file="$(local_core_helm_values_file "crossplane")"
crossplane_kustomize_dir="$(local_crossplane_kustomize_dir)"

if [[ ! -f "$crossplane_values_file" ]]; then
  log_fatal "missing crossplane values file: $crossplane_values_file"
fi

run_kustomize_apply "$crossplane_kustomize_dir"
run_helm_upgrade_install \
  "$CROSSPLANE_HELM_RELEASE" \
  "$CROSSPLANE_NAMESPACE" \
  "$CROSSPLANE_HELM_CHART" \
  "$CROSSPLANE_HELM_CHART_VERSION" \
  "$crossplane_values_file"

verification_mode="dry-run-state"
if tooling_is_execution_enabled; then
  require_command kubectl

  run_cmd kubectl rollout status deployment/"$CROSSPLANE_HELM_RELEASE" \
    --namespace "$CROSSPLANE_NAMESPACE" \
    --timeout=300s
  run_cmd kubectl rollout status deployment/"$CROSSPLANE_HELM_RELEASE-rbac-manager" \
    --namespace "$CROSSPLANE_NAMESPACE" \
    --timeout=300s

  run_cmd kubectl wait --for=condition=Established \
    crd/compositeresourcedefinitions.apiextensions.crossplane.io \
    --timeout=300s

  verification_mode="kubectl-rollout-and-crd"
fi

state_file="$(
  write_state_file "local_crossplane_bootstrap" \
    "profile=$BLUEPRINT_PROFILE" \
    "stack=$(active_stack)" \
    "tooling_mode=$(tooling_execution_mode)" \
    "bootstrap_driver=crossplane_helm" \
    "kustomize_path=$crossplane_kustomize_dir" \
    "crossplane_values_file=$crossplane_values_file" \
    "crossplane_release=$CROSSPLANE_HELM_RELEASE" \
    "crossplane_namespace=$CROSSPLANE_NAMESPACE" \
    "crossplane_chart=$CROSSPLANE_HELM_CHART" \
    "crossplane_chart_version=$CROSSPLANE_HELM_CHART_VERSION" \
    "verification_mode=$verification_mode" \
    "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
)"

log_info "local crossplane bootstrap state written to $state_file"
