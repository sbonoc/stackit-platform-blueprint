#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/blueprint/bootstrap_templates.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"

public_endpoints_seed_env_defaults() {
  set_default_env PUBLIC_ENDPOINTS_BASE_DOMAIN "apps.local"
  set_default_env PUBLIC_ENDPOINTS_NAMESPACE "network"
  set_default_env PUBLIC_ENDPOINTS_CONTROLLER_NAMESPACE "envoy-gateway-system"
  set_default_env PUBLIC_ENDPOINTS_GATEWAY_NAME "public-endpoints"
  set_default_env PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME "public-endpoints"
  set_default_env PUBLIC_ENDPOINTS_HELM_RELEASE "blueprint-public-endpoints"
  set_default_env PUBLIC_ENDPOINTS_HELM_CHART "oci://docker.io/envoyproxy/gateway-helm"
  set_default_env PUBLIC_ENDPOINTS_HELM_CHART_VERSION "$PUBLIC_ENDPOINTS_HELM_CHART_VERSION_PIN"
}

public_endpoints_init_env() {
  public_endpoints_seed_env_defaults
  require_env_vars PUBLIC_ENDPOINTS_BASE_DOMAIN
}

public_endpoints_gateway_manifest_content() {
  render_bootstrap_template_content \
    "infra" \
    "infra/gateway/public-endpoints.yaml.tmpl" \
    "PUBLIC_ENDPOINTS_NAMESPACE=$PUBLIC_ENDPOINTS_NAMESPACE" \
    "PUBLIC_ENDPOINTS_GATEWAY_NAME=$PUBLIC_ENDPOINTS_GATEWAY_NAME" \
    "PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME=$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME"
}

public_endpoints_namespace_manifest_file() {
  printf '%s\n' "$ROOT_DIR/artifacts/infra/rendered/public-endpoints.namespace.yaml"
}

public_endpoints_render_namespace_manifest() {
  local target_path
  target_path="$(public_endpoints_namespace_manifest_file)"
  ensure_dir "$(dirname "$target_path")"
  cat >"$target_path" <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: ${PUBLIC_ENDPOINTS_NAMESPACE}
EOF
  log_metric \
    "public_endpoints_gateway_namespace_manifest_render_total" \
    "1" \
    "target=$target_path namespace=$PUBLIC_ENDPOINTS_NAMESPACE" >&2
  log_info "rendered public-endpoints namespace manifest: $target_path" >&2
  printf '%s\n' "$target_path"
}

public_endpoints_render_gateway_manifest() {
  local target_path
  target_path="$(public_endpoints_gateway_manifest_file)"
  ensure_dir "$(dirname "$target_path")"
  printf '%s' "$(public_endpoints_gateway_manifest_content)" >"$target_path"
  # This helper is used in command substitutions, so stdout must stay reserved
  # for the rendered artifact path and diagnostics go to stderr.
  log_metric \
    "public_endpoints_gateway_manifest_render_total" \
    "1" \
    "target=$target_path namespace=$PUBLIC_ENDPOINTS_NAMESPACE gateway=$PUBLIC_ENDPOINTS_GATEWAY_NAME" >&2
  log_info "rendered public-endpoints gateway manifest: $target_path" >&2
  printf '%s\n' "$target_path"
}

public_endpoints_render_values_file() {
  render_optional_module_values_file \
    "public-endpoints" \
    "infra/local/helm/public-endpoints/values.yaml"
}

public_endpoints_gateway_api_crd_names() {
  printf '%s\n' \
    "gatewayclasses.gateway.networking.k8s.io" \
    "gateways.gateway.networking.k8s.io"
}

public_endpoints_gateway_api_crds_available() {
  if ! tooling_is_execution_enabled; then
    return 0
  fi

  prepare_cluster_access
  require_command kubectl

  local crd_name
  while IFS= read -r crd_name; do
    if ! kubectl get crd "$crd_name" >/dev/null 2>&1; then
      return 1
    fi
  done < <(public_endpoints_gateway_api_crd_names)

  return 0
}

public_endpoints_wait_for_gateway_api_crds() {
  local timeout_seconds="${1:-300}"
  if ! tooling_is_execution_enabled; then
    log_metric "public_endpoints_gateway_api_crd_wait_total" "1" "status=dry_run"
    log_info "dry-run Gateway API CRD wait skipped (set DRY_RUN=false to execute)"
    return 0
  fi

  prepare_cluster_access
  require_command kubectl

  local crd_name started_at now conditions
  while IFS= read -r crd_name; do
    started_at="$(date +%s)"
    # ArgoCD applies the Envoy Gateway controller asynchronously, so the shared
    # Gateway baseline must wait until the Gateway API CRDs actually exist.
    log_info "waiting for Gateway API CRD to report Established=True: $crd_name"
    while true; do
      if kubectl get crd "$crd_name" >/dev/null 2>&1; then
        conditions="$(kubectl get crd "$crd_name" -o jsonpath='{range .status.conditions[*]}{.type}={.status}{"\n"}{end}' 2>/dev/null || true)"
        if printf '%s\n' "$conditions" | grep -qx 'Established=True'; then
          log_metric "public_endpoints_gateway_api_crd_wait_total" "1" "crd=$crd_name status=ready"
          break
        fi
      fi

      now="$(date +%s)"
      if (( now - started_at >= timeout_seconds )); then
        log_metric "public_endpoints_gateway_api_crd_wait_total" "1" "crd=$crd_name status=timeout"
        log_fatal "timed out waiting for Gateway API CRD to report Established=True: $crd_name"
      fi

      sleep 2
    done
  done < <(public_endpoints_gateway_api_crd_names)
}

public_endpoints_wait_for_resource_absence() {
  local kind="$1"
  local name="$2"
  local timeout_seconds="${3:-60}"
  local namespace="${4:-}"
  local started_at now

  started_at="$(date +%s)"
  while true; do
    if [[ -n "$namespace" ]]; then
      if ! kubectl get "$kind" "$name" -n "$namespace" >/dev/null 2>&1; then
        log_metric "public_endpoints_destroy_wait_total" "1" "kind=$kind name=$name status=deleted"
        return 0
      fi
    elif ! kubectl get "$kind" "$name" >/dev/null 2>&1; then
      log_metric "public_endpoints_destroy_wait_total" "1" "kind=$kind name=$name status=deleted"
      return 0
    fi

    now="$(date +%s)"
    if (( now - started_at >= timeout_seconds )); then
      log_metric "public_endpoints_destroy_wait_total" "1" "kind=$kind name=$name status=timeout"
      log_warn "timed out waiting for public-endpoints resource deletion kind=$kind name=$name namespace=${namespace:-cluster}"
      return 1
    fi

    sleep 2
  done
}

public_endpoints_gatewayclass_finalizers() {
  kubectl get gatewayclass "$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" -o jsonpath='{.metadata.finalizers[*]}' 2>/dev/null || true
}

public_endpoints_force_clear_gatewayclass_finalizers() {
  local finalizers
  finalizers="$(public_endpoints_gatewayclass_finalizers)"

  if [[ "$finalizers" != *"gateway-exists-finalizer.gateway.networking.k8s.io"* ]]; then
    log_metric "public_endpoints_gatewayclass_finalizer_clear_total" "1" "status=skipped_missing_known_finalizer"
    return 1
  fi

  # Local destroy must stay idempotent even if the Envoy Gateway controller has
  # already disappeared. In that case the GatewayClass finalizer can never clear
  # itself, so we remove the known class finalizer only after a bounded wait.
  run_cmd kubectl patch gatewayclass "$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" --type=merge -p '{"metadata":{"finalizers":[]}}'
  log_metric "public_endpoints_gatewayclass_finalizer_clear_total" "1" "status=executed"
  log_warn "cleared stuck GatewayClass finalizers for public-endpoints: $PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME"
  return 0
}

public_endpoints_delete_helm_gateway_baseline() {
  if ! tooling_is_execution_enabled; then
    log_metric "public_endpoints_destroy_wait_total" "1" "kind=gateway status=dry_run"
    log_info "dry-run public-endpoints Gateway baseline delete (set DRY_RUN=false to execute)"
    return 0
  fi

  prepare_cluster_access
  require_command kubectl

  run_cmd kubectl delete gateway "$PUBLIC_ENDPOINTS_GATEWAY_NAME" -n "$PUBLIC_ENDPOINTS_NAMESPACE" --ignore-not-found --wait=false
  public_endpoints_wait_for_resource_absence "gateway" "$PUBLIC_ENDPOINTS_GATEWAY_NAME" 30 "$PUBLIC_ENDPOINTS_NAMESPACE" || true

  run_cmd kubectl delete gatewayclass "$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" --ignore-not-found --wait=false
  if public_endpoints_wait_for_resource_absence "gatewayclass" "$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" 30; then
    return 0
  fi

  if public_endpoints_force_clear_gatewayclass_finalizers; then
    public_endpoints_wait_for_resource_absence "gatewayclass" "$PUBLIC_ENDPOINTS_GATEWAY_CLASS_NAME" 15 || true
  fi
}
