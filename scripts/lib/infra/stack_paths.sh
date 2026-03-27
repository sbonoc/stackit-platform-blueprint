#!/usr/bin/env bash
set -euo pipefail

stackit_terraform_module_dir() {
  local module_name="$1"
  printf '%s/infra/cloud/stackit/terraform/modules/%s' "$ROOT_DIR" "$module_name"
}

stackit_terraform_layer_dir() {
  local layer="$1"
  case "$layer" in
  bootstrap | foundation)
    printf '%s/infra/cloud/stackit/terraform/%s' "$ROOT_DIR" "$layer"
    ;;
  *)
    return 1
    ;;
  esac
}

stackit_terraform_layer_backend_file() {
  local layer="$1"
  local env_name
  env_name="$(profile_environment)"
  printf '%s/infra/cloud/stackit/terraform/%s/state-backend/%s.hcl' "$ROOT_DIR" "$layer" "$env_name"
}

stackit_terraform_layer_var_file() {
  local layer="$1"
  local env_name
  env_name="$(profile_environment)"
  printf '%s/infra/cloud/stackit/terraform/%s/env/%s.tfvars' "$ROOT_DIR" "$layer" "$env_name"
}

argocd_overlay_dir() {
  local env_name
  env_name="$(profile_environment)"
  printf '%s/infra/gitops/argocd/overlays/%s' "$ROOT_DIR" "$env_name"
}

argocd_base_dir() {
  printf '%s/infra/gitops/argocd/base' "$ROOT_DIR"
}

argocd_optional_manifest() {
  local module_name="$1"
  local env_name
  env_name="$(profile_environment)"
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

rendered_module_helm_values_file() {
  local module_name="$1"
  printf '%s/artifacts/infra/rendered/%s.values.yaml' "$ROOT_DIR" "$module_name"
}

public_endpoints_gateway_manifest_file() {
  printf '%s/artifacts/infra/rendered/public-endpoints.gateway.yaml' "$ROOT_DIR"
}

rendered_optional_module_secret_artifacts_dir() {
  printf '%s/artifacts/infra/rendered/secrets' "$ROOT_DIR"
}

local_core_helm_values_file() {
  local component_name="$1"
  printf '%s/infra/local/helm/core/%s.values.yaml' "$ROOT_DIR" "$component_name"
}

local_crossplane_manifest_file() {
  local manifest_name="$1"
  printf '%s/infra/local/crossplane/%s.yaml' "$ROOT_DIR" "$manifest_name"
}
