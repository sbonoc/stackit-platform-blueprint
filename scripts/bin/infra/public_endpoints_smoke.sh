#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../lib/shell/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/public_endpoints.sh"

start_script_metric_trap "infra_public_endpoints_smoke"

if ! is_module_enabled public-endpoints; then
  log_info "PUBLIC_ENDPOINTS_ENABLED=false; skipping public-endpoints smoke"
  exit 0
fi

public_endpoints_init_env
if ! state_file_exists public_endpoints_runtime; then
  log_fatal "missing public-endpoints runtime artifact"
fi

runtime_state="$(state_file_path public_endpoints_runtime)"
if ! grep -q '^base_domain=' "$runtime_state"; then
  log_fatal "public-endpoints runtime base_domain contract is missing"
fi
if ! grep -q '^gateway_name=' "$runtime_state"; then
  log_fatal "public-endpoints runtime gateway_name contract is missing"
fi
if ! grep -q '^gateway_class_name=' "$runtime_state"; then
  log_fatal "public-endpoints runtime gateway_class_name contract is missing"
fi
# Read the Gateway contract from the runtime artifact written at apply time so
# smoke stays bound to the materialized edge baseline instead of the current shell.
runtime_base_domain="$(grep '^base_domain=' "$runtime_state" | head -n1 | cut -d= -f2-)"
runtime_gateway_name="$(grep '^gateway_name=' "$runtime_state" | head -n1 | cut -d= -f2-)"
runtime_gateway_class_name="$(grep '^gateway_class_name=' "$runtime_state" | head -n1 | cut -d= -f2-)"
runtime_gateway_namespace="$(grep '^gateway_namespace=' "$runtime_state" | head -n1 | cut -d= -f2-)"
gateway_manifest_path="$(grep '^gateway_manifest_path=' "$runtime_state" | head -n1 | cut -d= -f2-)"
appproject_path="$ROOT_DIR/infra/gitops/argocd/overlays/$(profile_environment)/appproject.yaml"
edge_appproject_path="$ROOT_DIR/infra/gitops/argocd/overlays/$(profile_environment)/appproject-edge.yaml"
if [[ -z "$runtime_base_domain" || -z "$runtime_gateway_name" || -z "$runtime_gateway_class_name" || -z "$runtime_gateway_namespace" ]]; then
  log_fatal "public-endpoints runtime Gateway contract is incomplete"
fi
if [[ -z "$gateway_manifest_path" || ! -f "$gateway_manifest_path" ]]; then
  log_fatal "public-endpoints runtime gateway manifest artifact is missing"
fi
if [[ ! -f "$appproject_path" || ! -f "$edge_appproject_path" ]]; then
  log_fatal "public-endpoints Argo CD project contract files are missing"
fi
if ! grep -Eq '^[[:space:]]*kind: GatewayClass$' "$gateway_manifest_path"; then
  log_fatal "public-endpoints gateway manifest is missing GatewayClass"
fi
if ! grep -Eq '^[[:space:]]*kind: Gateway$' "$gateway_manifest_path"; then
  log_fatal "public-endpoints gateway manifest is missing Gateway"
fi
if ! grep -q 'from: All' "$gateway_manifest_path"; then
  log_fatal "public-endpoints gateway listener does not allow cross-namespace route attachment"
fi
if ! grep -q 'name: network' "$ROOT_DIR/infra/gitops/platform/base/namespaces.yaml"; then
  log_fatal "platform base namespace contract is missing the shared network namespace"
fi
# The shared edge and consumer route policy resources intentionally live in
# separate Argo CD projects so JWT route policies cannot drift onto the
# shared Gateway baseline in the network namespace.
if grep -q 'namespace: network' "$appproject_path"; then
  log_fatal "application AppProject must not target the shared network namespace"
fi
if ! grep -Eq '^[[:space:]]+kind: HTTPRoute$' "$appproject_path"; then
  log_fatal "application AppProject is missing HTTPRoute permissions"
fi
if ! grep -Eq '^[[:space:]]+kind: BackendTLSPolicy$' "$appproject_path"; then
  log_fatal "application AppProject is missing BackendTLSPolicy permissions"
fi
if ! grep -Eq '^[[:space:]]+kind: SecurityPolicy$' "$appproject_path"; then
  log_fatal "application AppProject is missing SecurityPolicy permissions"
fi
if ! grep -Eq '^[[:space:]]+kind: Backend$' "$appproject_path"; then
  log_fatal "application AppProject is missing Envoy Backend permissions"
fi
if ! grep -q 'namespace: network' "$edge_appproject_path"; then
  log_fatal "edge AppProject is missing the shared network namespace destination"
fi
if ! grep -q 'namespace: envoy-gateway-system' "$edge_appproject_path"; then
  log_fatal "edge AppProject is missing the Envoy Gateway controller namespace destination"
fi
if ! grep -Eq '^[[:space:]]+kind: GatewayClass$' "$edge_appproject_path"; then
  log_fatal "edge AppProject is missing GatewayClass permissions"
fi
if ! grep -Eq '^[[:space:]]+kind: Gateway$' "$edge_appproject_path"; then
  log_fatal "edge AppProject is missing Gateway permissions"
fi

log_metric \
  "public_endpoints_gateway_contract_check_total" \
  "1" \
  "gateway_name=$runtime_gateway_name gateway_class_name=$runtime_gateway_class_name gateway_namespace=$runtime_gateway_namespace"
log_info "validated shared Gateway API contract gateway=$runtime_gateway_name class=$runtime_gateway_class_name namespace=$runtime_gateway_namespace"
log_metric \
  "public_endpoints_route_policy_project_check_total" \
  "1" \
  "environment=$(profile_environment) route_project=$(basename "$appproject_path") edge_project=$(basename "$edge_appproject_path")"
log_info "validated split Argo CD project contract environment=$(profile_environment) route_project=$(basename "$appproject_path") edge_project=$(basename "$edge_appproject_path")"

state_file="$(write_state_file "public_endpoints_smoke" \
  "status=passed" \
  "base_domain=$runtime_base_domain" \
  "gateway_name=$runtime_gateway_name" \
  "gateway_class_name=$runtime_gateway_class_name" \
  "gateway_namespace=$runtime_gateway_namespace" \
  "gateway_manifest_path=$gateway_manifest_path" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints smoke state written to $state_file"
