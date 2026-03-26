#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$ROOT_DIR/scripts/lib/bootstrap.sh"
source "$ROOT_DIR/scripts/lib/infra/profile.sh"
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"
source "$ROOT_DIR/scripts/lib/infra/state.sh"
source "$ROOT_DIR/scripts/lib/infra/tooling.sh"
source "$ROOT_DIR/scripts/lib/infra/public_endpoints.sh"

start_script_metric_trap "infra_public_endpoints_apply"

if ! is_module_enabled public-endpoints; then
  log_info "PUBLIC_ENDPOINTS_ENABLED=false; skipping public-endpoints apply"
  exit 0
fi

public_endpoints_init_env
if ! state_file_exists public_endpoints_plan; then
  log_fatal "missing public-endpoints plan artifact; run infra-public-endpoints-plan first"
fi

provision_driver="none"
provision_path="none"
if is_stackit_profile; then
  provision_driver="terraform"
  provision_path="$(stackit_terraform_module_dir "public-endpoints")"
  run_terraform_action apply "$provision_path"
elif is_local_profile; then
  provision_driver="helm"
  provision_path="$(local_module_helm_values_file "public-endpoints")"
  run_helm_upgrade_install \
    "$PUBLIC_ENDPOINTS_HELM_RELEASE" \
    "$PUBLIC_ENDPOINTS_NAMESPACE" \
    "$PUBLIC_ENDPOINTS_HELM_CHART" \
    "$PUBLIC_ENDPOINTS_HELM_CHART_VERSION" \
    "$provision_path"
else
  log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
fi

state_file="$(write_state_file "public_endpoints_runtime" \
  "profile=$BLUEPRINT_PROFILE" \
  "stack=$(active_stack)" \
  "tooling_mode=$(tooling_execution_mode)" \
  "provision_driver=$provision_driver" \
  "provision_path=$provision_path" \
  "base_domain=$PUBLIC_ENDPOINTS_BASE_DOMAIN" \
  "ingress_class=$PUBLIC_ENDPOINTS_INGRESS_CLASS" \
  "timestamp_utc=$(date -u +"%Y-%m-%dT%H:%M:%SZ")")"

log_info "public-endpoints runtime state written to $state_file"
