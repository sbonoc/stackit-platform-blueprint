#!/usr/bin/env bash
set -euo pipefail

profile_env() {
  if declare -F profile_environment >/dev/null 2>&1; then
    profile_environment
    return 0
  fi
  case "${BLUEPRINT_PROFILE:-local-full}" in
  stackit-dev)
    echo "dev"
    ;;
  stackit-stage)
    echo "stage"
    ;;
  stackit-prod)
    echo "prod"
    ;;
  local-full | local-lite)
    echo "local"
    ;;
  *)
    echo "unknown"
    ;;
  esac
}

stackit_terraform_env_dir() {
  local env_name
  env_name="$(profile_env)"
  printf '%s/infra/cloud/stackit/terraform/environments/%s' "$ROOT_DIR" "$env_name"
}

stackit_terraform_module_dir() {
  local module_name="$1"
  printf '%s/infra/cloud/stackit/terraform/modules/%s' "$ROOT_DIR" "$module_name"
}

argocd_overlay_dir() {
  local env_name
  env_name="$(profile_env)"
  printf '%s/infra/gitops/argocd/overlays/%s' "$ROOT_DIR" "$env_name"
}

argocd_base_dir() {
  printf '%s/infra/gitops/argocd/base' "$ROOT_DIR"
}

argocd_optional_manifest() {
  local module_name="$1"
  local env_name
  env_name="$(profile_env)"
  printf '%s/infra/gitops/argocd/optional/%s/%s.yaml' "$ROOT_DIR" "$env_name" "$module_name"
}

local_crossplane_kustomize_dir() {
  printf '%s/infra/local/crossplane' "$ROOT_DIR"
}

local_argocd_overlay_dir() {
  printf '%s/infra/gitops/argocd/overlays/local' "$ROOT_DIR"
}

local_observability_values_file() {
  printf '%s/infra/local/helm/observability/grafana.values.yaml' "$ROOT_DIR"
}

local_otel_collector_values_file() {
  printf '%s/infra/local/helm/observability/otel-collector.values.yaml' "$ROOT_DIR"
}

local_module_helm_values_file() {
  local module_name="$1"
  printf '%s/infra/local/helm/%s/values.yaml' "$ROOT_DIR" "$module_name"
}
