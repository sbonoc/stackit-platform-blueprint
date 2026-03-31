#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.baseline.sh"
source "$ROOT_DIR/scripts/lib/quality/semver.sh"

start_script_metric_trap "infra_audit_version"

usage() {
  cat <<'EOF'
Usage: audit_version.sh

Audits pinned infra versions and checks drift against baseline policy:
- patch drift => fail
- minor drift => warn
- major drift => fail
- non-semver => warn
- includes local optional-module Helm chart pins from the canonical versions source
- verifies Helm-backed chart pins resolve when `helm` is available locally
EOF
}

if [[ "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

failures=0
warnings=0
helm_pin_checks_skipped="false"
docker_pin_checks_skipped="false"

normalize_optional_v_semver() {
  local value="$1"
  printf '%s' "${value#v}"
}

is_transient_registry_error() {
  local error_text="$1"
  local lowered
  lowered="$(printf '%s' "$error_text" | tr '[:upper:]' '[:lower:]')"
  [[ "$lowered" == *"502 bad gateway"* ]] && return 0
  [[ "$lowered" == *"503 service unavailable"* ]] && return 0
  [[ "$lowered" == *"504 gateway timeout"* ]] && return 0
  [[ "$lowered" == *"context deadline exceeded"* ]] && return 0
  [[ "$lowered" == *"client.timeout exceeded"* ]] && return 0
  [[ "$lowered" == *"i/o timeout"* ]] && return 0
  [[ "$lowered" == *"connection reset by peer"* ]] && return 0
  [[ "$lowered" == *"tls handshake timeout"* ]] && return 0
  [[ "$lowered" == *"too many requests"* ]] && return 0
  [[ "$lowered" == *"429"* ]] && return 0
  return 1
}

audit_var() {
  local var_name="$1"
  local current baseline current_semver baseline_semver
  current="${!var_name:-}"
  baseline="$(
    source "$ROOT_DIR/scripts/lib/infra/versions.baseline.sh"
    printf '%s' "${!var_name:-}"
  )"

  if [[ -z "$current" ]]; then
    log_error "missing pinned version for $var_name"
    failures=$((failures + 1))
    return
  fi

  if [[ "$current" == "latest" ]]; then
    log_error "unpinned value is forbidden for $var_name"
    failures=$((failures + 1))
    return
  fi

  current_semver="$(normalize_optional_v_semver "$current")"
  if ! is_semver "$current_semver"; then
    log_warn "non-semver value for $var_name: $current"
    warnings=$((warnings + 1))
    return
  fi

  if [[ -z "$baseline" ]]; then
    log_warn "no baseline defined for $var_name; skipping drift check"
    warnings=$((warnings + 1))
    return
  fi

  baseline_semver="$(normalize_optional_v_semver "$baseline")"
  if ! is_semver "$baseline_semver"; then
    log_warn "non-semver baseline for $var_name: $baseline"
    warnings=$((warnings + 1))
    return
  fi

  local drift
  drift="$(classify_semver_drift "$current_semver" "$baseline_semver")"
  case "$drift" in
  same)
    ;;
  patch | major)
    log_error "$drift drift detected for $var_name: current=$current baseline=$baseline"
    failures=$((failures + 1))
    ;;
  minor)
    log_warn "minor drift detected for $var_name: current=$current baseline=$baseline"
    warnings=$((warnings + 1))
    ;;
  non-semver)
    log_warn "non-semver drift comparison for $var_name: current=$current baseline=$baseline"
    warnings=$((warnings + 1))
    ;;
  *)
    log_error "unknown drift classification for $var_name: $drift"
    failures=$((failures + 1))
    ;;
  esac
}

audit_helm_chart_pin() {
  local var_name="$1"
  local chart_ref="$2"
  local version="${!var_name:-}"

  if [[ -z "$version" ]]; then
    return 0
  fi

  if ! shell_has_cmd helm; then
    if [[ "$helm_pin_checks_skipped" == "false" ]]; then
      log_warn "helm not installed; skipping Helm chart pin resolution checks"
      helm_pin_checks_skipped="true"
    fi
    return 0
  fi

  if [[ "$chart_ref" == oci://* ]]; then
    if helm show chart "$chart_ref" --version "$version" >/dev/null 2>&1; then
      log_metric "helm_chart_pin_check_total" "1" "chart=$chart_ref version=$version status=found"
      return 0
    fi

    log_metric "helm_chart_pin_check_total" "1" "chart=$chart_ref version=$version status=missing"
    log_error "pinned Helm chart version not found for $var_name: chart=$chart_ref version=$version"
    failures=$((failures + 1))
    return 0
  fi

  prepare_helm_repo_for_chart "$chart_ref"

  if helm search repo "$chart_ref" --versions | awk -v version="$version" 'NR > 1 && $2 == version { found = 1 } END { exit found ? 0 : 1 }'; then
    log_metric "helm_chart_pin_check_total" "1" "chart=$chart_ref version=$version status=found"
    return 0
  fi

  log_metric "helm_chart_pin_check_total" "1" "chart=$chart_ref version=$version status=missing"
  log_error "pinned Helm chart version not found for $var_name: chart=$chart_ref version=$version"
  failures=$((failures + 1))
}

audit_container_image_pin() {
  local registry_var="$1"
  local repository_var="$2"
  local tag_var="$3"
  local registry="${!registry_var:-}"
  local repository="${!repository_var:-}"
  local tag="${!tag_var:-}"

  if [[ -z "$registry" || -z "$repository" || -z "$tag" ]]; then
    log_error "missing runtime image pin values for $registry_var/$repository_var/$tag_var"
    failures=$((failures + 1))
    return 0
  fi

  if ! shell_has_cmd docker; then
    if [[ "$docker_pin_checks_skipped" == "false" ]]; then
      log_warn "docker not installed; skipping runtime image manifest resolution checks"
      docker_pin_checks_skipped="true"
    fi
    return 0
  fi

  local image_ref="${registry}/${repository}:${tag}"
  local inspect_output=""
  if inspect_output="$(docker manifest inspect "$image_ref" 2>&1 >/dev/null)"; then
    log_metric "container_image_pin_check_total" "1" "image=$image_ref status=found"
    return 0
  fi

  if is_transient_registry_error "$inspect_output"; then
    log_metric "container_image_pin_check_total" "1" "image=$image_ref status=unavailable"
    log_warn "container registry check unavailable for pinned image: $image_ref ($inspect_output)"
    warnings=$((warnings + 1))
    return 0
  fi

  log_metric "container_image_pin_check_total" "1" "image=$image_ref status=missing"
  log_error "pinned container image not found: $image_ref"
  failures=$((failures + 1))
}

tracked_vars=(
  TERRAFORM_VERSION
  HELM_VERSION
  KUBECTL_VERSION
  KIND_VERSION
  EXTERNAL_SECRETS_CHART_VERSION
  CERT_MANAGER_CHART_VERSION
  ARGOCD_CHART_VERSION
  CROSSPLANE_CHART_VERSION
  OTEL_COLLECTOR_CHART_VERSION
  GRAFANA_CHART_VERSION
  LOKI_CHART_VERSION
  TEMPO_CHART_VERSION
  POSTGRES_HELM_CHART_VERSION_PIN
  OBJECT_STORAGE_HELM_CHART_VERSION_PIN
  RABBITMQ_HELM_CHART_VERSION_PIN
  NEO4J_HELM_CHART_VERSION_PIN
  PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN
  IAP_HELM_CHART_VERSION_PIN
  KEYCLOAK_HELM_CHART_VERSION_PIN
  KEYCLOAK_IMAGE_TAG_PIN
)

for var_name in "${tracked_vars[@]}"; do
  audit_var "$var_name"
done

audit_helm_chart_pin "POSTGRES_HELM_CHART_VERSION_PIN" "bitnami/postgresql"
audit_helm_chart_pin "OBJECT_STORAGE_HELM_CHART_VERSION_PIN" "bitnami/minio"
audit_helm_chart_pin "RABBITMQ_HELM_CHART_VERSION_PIN" "bitnami/rabbitmq"
audit_helm_chart_pin "NEO4J_HELM_CHART_VERSION_PIN" "neo4j/neo4j"
audit_helm_chart_pin "PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN" "oci://docker.io/envoyproxy/gateway-helm"
audit_helm_chart_pin "IAP_HELM_CHART_VERSION_PIN" "oauth2-proxy/oauth2-proxy"
audit_helm_chart_pin "KEYCLOAK_HELM_CHART_VERSION_PIN" "codecentric/keycloakx"
audit_helm_chart_pin "CERT_MANAGER_CHART_VERSION" "jetstack/cert-manager"

audit_container_image_pin "POSTGRES_LOCAL_IMAGE_REGISTRY" "POSTGRES_LOCAL_IMAGE_REPOSITORY" "POSTGRES_LOCAL_IMAGE_TAG"
audit_container_image_pin "OBJECT_STORAGE_LOCAL_IMAGE_REGISTRY" "OBJECT_STORAGE_LOCAL_IMAGE_REPOSITORY" "OBJECT_STORAGE_LOCAL_IMAGE_TAG"
audit_container_image_pin "OBJECT_STORAGE_LOCAL_CLIENT_IMAGE_REGISTRY" "OBJECT_STORAGE_LOCAL_CLIENT_IMAGE_REPOSITORY" "OBJECT_STORAGE_LOCAL_CLIENT_IMAGE_TAG"
audit_container_image_pin "RABBITMQ_LOCAL_IMAGE_REGISTRY" "RABBITMQ_LOCAL_IMAGE_REPOSITORY" "RABBITMQ_LOCAL_IMAGE_TAG"
audit_container_image_pin "IAP_LOCAL_IMAGE_REGISTRY" "IAP_LOCAL_IMAGE_REPOSITORY" "IAP_LOCAL_IMAGE_TAG"

if [[ $warnings -gt 0 ]]; then
  log_warn "version audit completed with $warnings warning(s)"
fi

if [[ $failures -gt 0 ]]; then
  log_fatal "version audit failed with $failures failure(s)"
fi

log_info "infra version audit passed"
