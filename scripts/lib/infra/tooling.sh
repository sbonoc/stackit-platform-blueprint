#!/usr/bin/env bash
set -euo pipefail

tooling_normalize_bool() {
  local value="${1:-false}"
  case "$value" in
  1 | true | TRUE | True | yes | YES | on | ON)
    echo "true"
    ;;
  *)
    echo "false"
    ;;
  esac
}

tooling_execution_mode() {
  if [[ "$(tooling_normalize_bool "${DRY_RUN:-true}")" == "true" ]]; then
    echo "dry-run"
    return 0
  fi
  echo "execute"
}

tooling_is_execution_enabled() {
  [[ "$(tooling_execution_mode)" == "execute" ]]
}

terraform_dir_has_config() {
  local terraform_dir="$1"
  [[ -d "$terraform_dir" ]] || return 1
  find "$terraform_dir" -maxdepth 2 -type f -name '*.tf' | grep -q .
}

kustomize_dir_has_config() {
  local kustomize_dir="$1"
  [[ -f "$kustomize_dir/kustomization.yaml" ]] || [[ -f "$kustomize_dir/kustomization.yml" ]] || [[ -f "$kustomize_dir/Kustomization" ]]
}

run_terraform_action() {
  local action="$1"
  local terraform_dir="$2"
  if ! terraform_dir_has_config "$terraform_dir"; then
    log_warn "terraform config not found; skipping action=$action dir=$terraform_dir"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command terraform
    run_cmd terraform -chdir="$terraform_dir" init -input=false -no-color
    case "$action" in
    plan)
      run_cmd terraform -chdir="$terraform_dir" plan -input=false -no-color
      ;;
    apply)
      run_cmd terraform -chdir="$terraform_dir" apply -input=false -auto-approve -no-color
      ;;
    destroy)
      run_cmd terraform -chdir="$terraform_dir" destroy -input=false -auto-approve -no-color
      ;;
    *)
      log_fatal "unsupported terraform action: $action"
      ;;
    esac
    return 0
  fi

  log_info "dry-run terraform action=$action dir=$terraform_dir (set DRY_RUN=false to execute)"
}

run_kustomize_apply() {
  local kustomize_dir="$1"
  if ! kustomize_dir_has_config "$kustomize_dir"; then
    log_warn "kustomization not found; skipping dir=$kustomize_dir"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command kubectl
    run_cmd kubectl apply -k "$kustomize_dir"
    return 0
  fi

  log_info "dry-run kubectl apply -k $kustomize_dir (set DRY_RUN=false to execute)"
}

run_kustomize_delete() {
  local kustomize_dir="$1"
  if ! kustomize_dir_has_config "$kustomize_dir"; then
    log_warn "kustomization not found; skipping dir=$kustomize_dir"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command kubectl
    run_cmd kubectl delete -k "$kustomize_dir" --ignore-not-found
    return 0
  fi

  log_info "dry-run kubectl delete -k $kustomize_dir (set DRY_RUN=false to execute)"
}

run_manifest_apply() {
  local manifest_file="$1"
  if [[ ! -f "$manifest_file" ]]; then
    log_warn "manifest file not found; skipping file=$manifest_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command kubectl
    run_cmd kubectl apply -f "$manifest_file"
    return 0
  fi

  log_info "dry-run kubectl apply -f $manifest_file (set DRY_RUN=false to execute)"
}

run_manifest_delete() {
  local manifest_file="$1"
  if [[ ! -f "$manifest_file" ]]; then
    log_warn "manifest file not found; skipping file=$manifest_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command kubectl
    run_cmd kubectl delete -f "$manifest_file" --ignore-not-found
    return 0
  fi

  log_info "dry-run kubectl delete -f $manifest_file (set DRY_RUN=false to execute)"
}

run_helm_upgrade_install() {
  local release_name="$1"
  local namespace="$2"
  local chart_ref="$3"
  local chart_version="$4"
  local values_file="$5"

  if [[ ! -f "$values_file" ]]; then
    log_warn "helm values file not found; skipping values_file=$values_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command helm
    prepare_helm_repo_for_chart "$chart_ref"
    run_cmd helm upgrade --install \
      "$release_name" \
      "$chart_ref" \
      --namespace "$namespace" \
      --create-namespace \
      --version "$chart_version" \
      --values "$values_file"
    return 0
  fi

  log_info "dry-run helm upgrade --install release=$release_name chart=$chart_ref version=$chart_version values=$values_file (set DRY_RUN=false to execute)"
}

run_helm_uninstall() {
  local release_name="$1"
  local namespace="$2"

  if tooling_is_execution_enabled; then
    require_command helm
    run_cmd helm uninstall "$release_name" --namespace "$namespace" --ignore-not-found
    return 0
  fi

  log_info "dry-run helm uninstall release=$release_name namespace=$namespace (set DRY_RUN=false to execute)"
}

run_helm_template() {
  local release_name="$1"
  local namespace="$2"
  local chart_ref="$3"
  local chart_version="$4"
  local values_file="$5"

  if [[ ! -f "$values_file" ]]; then
    log_warn "helm values file not found; skipping values_file=$values_file"
    return 0
  fi

  if tooling_is_execution_enabled; then
    require_command helm
    prepare_helm_repo_for_chart "$chart_ref"
    run_cmd helm template \
      "$release_name" \
      "$chart_ref" \
      --namespace "$namespace" \
      --version "$chart_version" \
      --values "$values_file" >/dev/null
    return 0
  fi

  log_info "dry-run helm template release=$release_name chart=$chart_ref version=$chart_version values=$values_file (set DRY_RUN=false to execute)"
}

prepare_helm_repo_for_chart() {
  local chart_ref="$1"
  if [[ "$chart_ref" == oci://* ]]; then
    return 0
  fi

  local repo_name
  repo_name="${chart_ref%%/*}"
  local repo_url=""
  case "$repo_name" in
  bitnami)
    repo_url="https://charts.bitnami.com/bitnami"
    ;;
  neo4j)
    repo_url="https://helm.neo4j.com/neo4j"
    ;;
  grafana)
    repo_url="https://grafana.github.io/helm-charts"
    ;;
  langfuse)
    repo_url="https://langfuse.github.io/langfuse-k8s"
    ;;
  open-telemetry)
    repo_url="https://open-telemetry.github.io/opentelemetry-helm-charts"
    ;;
  ingress-nginx)
    repo_url="https://kubernetes.github.io/ingress-nginx"
    ;;
  oauth2-proxy)
    repo_url="https://oauth2-proxy.github.io/manifests"
    ;;
  *)
    log_warn "unknown helm repository prefix '$repo_name'; continuing without repo bootstrap"
    return 0
    ;;
  esac

  run_cmd helm repo add "$repo_name" "$repo_url"
  run_cmd helm repo update
}
