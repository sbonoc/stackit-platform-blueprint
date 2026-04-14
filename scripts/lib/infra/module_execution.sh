#!/usr/bin/env bash
set -euo pipefail

# Centralize profile-to-driver resolution for optional modules so wrappers record
# one execution contract across provider-backed, fallback, and external modes.
OPTIONAL_MODULE_EXECUTION_CLASS=""
OPTIONAL_MODULE_EXECUTION_DRIVER=""
OPTIONAL_MODULE_EXECUTION_PATH=""
OPTIONAL_MODULE_EXECUTION_NOTE=""

optional_module_execution_reset() {
  OPTIONAL_MODULE_EXECUTION_CLASS=""
  OPTIONAL_MODULE_EXECUTION_DRIVER=""
  OPTIONAL_MODULE_EXECUTION_PATH=""
  OPTIONAL_MODULE_EXECUTION_NOTE=""
}

optional_module_execution_set() {
  OPTIONAL_MODULE_EXECUTION_CLASS="$1"
  OPTIONAL_MODULE_EXECUTION_DRIVER="$2"
  OPTIONAL_MODULE_EXECUTION_PATH="$3"
  OPTIONAL_MODULE_EXECUTION_NOTE="${4:-}"
}

optional_module_execution_emit_metric() {
  log_metric \
    "optional_module_execution_mode_total" \
    "1" \
    "module=$1 action=$2 class=$OPTIONAL_MODULE_EXECUTION_CLASS driver=$OPTIONAL_MODULE_EXECUTION_DRIVER stack=$(active_stack)"
}

optional_module_unexpected_driver() {
  local module="$1"
  local action="$2"
  log_fatal \
    "unsupported execution driver for module=$module action=$action driver=$OPTIONAL_MODULE_EXECUTION_DRIVER profile=$BLUEPRINT_PROFILE"
}

optional_module_log_execution_note() {
  if [[ -n "$OPTIONAL_MODULE_EXECUTION_NOTE" ]]; then
    log_warn "$OPTIONAL_MODULE_EXECUTION_NOTE"
  fi
}

optional_module_warn_missing_foundation_diff() {
  local module="$1"
  if state_file_exists stackit_foundation_plan || state_file_exists stackit_foundation_apply; then
    return 0
  fi
  log_warn "STACKIT foundation plan/apply state not found; run infra-stackit-foundation-plan for full terraform diff (module=$module)"
}

optional_module_apply_foundation_contract() {
  local module="$1"
  if state_file_exists stackit_foundation_apply; then
    return 0
  fi

  log_info "stackit foundation apply state missing; reconciling foundation for $module contract"
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_preflight.sh"
  run_cmd "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
}

optional_module_destroy_foundation_contract() {
  local module="$1"
  local flag_name
  flag_name="$(module_flag_name "$module")" || log_fatal "unsupported optional module for foundation destroy: $module"
  run_cmd env "${flag_name}=false" "$ROOT_DIR/scripts/bin/infra/stackit_foundation_preflight.sh"
  run_cmd env "${flag_name}=false" "$ROOT_DIR/scripts/bin/infra/stackit_foundation_apply.sh"
}

optional_module_require_manifest_present() {
  local module="$1"
  local manifest_path="$2"
  if [[ -f "$manifest_path" ]]; then
    return 0
  fi
  log_fatal "missing ${module} optional manifest: $manifest_path (run make infra-bootstrap)"
}

resolve_optional_module_execution() {
  local module="$1"
  local action="$2"

  optional_module_execution_reset

  case "${module}:${action}" in
  observability:plan | observability:apply)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_contract" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "crossplane_plus_helm" "$(local_crossplane_kustomize_dir)"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  observability:destroy)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_reconcile_apply" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "argocd_manifest_plus_helm" "$(argocd_optional_manifest "observability")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  postgres:plan | postgres:apply)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_contract" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "helm" "$(rendered_module_helm_values_file "postgres")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  postgres:destroy)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_reconcile_apply" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "helm" "$(rendered_module_helm_values_file "postgres")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  object-storage:plan | object-storage:apply)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_contract" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "helm" "$(rendered_module_helm_values_file "object-storage")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  object-storage:destroy)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_reconcile_apply" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "helm" "$(rendered_module_helm_values_file "object-storage")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  dns:plan | dns:apply | dns:destroy)
    if is_stackit_profile; then
      if [[ "$action" == "destroy" ]]; then
        optional_module_execution_set "provider_backed" "foundation_reconcile_apply" "$(stackit_terraform_layer_dir foundation)"
      else
        optional_module_execution_set "provider_backed" "foundation_contract" "$(stackit_terraform_layer_dir foundation)"
      fi
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "noop" "none" "dns module has no managed local counterpart; $action is a contract no-op"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  secrets-manager:plan | secrets-manager:apply | secrets-manager:destroy)
    if is_stackit_profile; then
      if [[ "$action" == "destroy" ]]; then
        optional_module_execution_set "provider_backed" "foundation_reconcile_apply" "$(stackit_terraform_layer_dir foundation)"
      else
        optional_module_execution_set "provider_backed" "foundation_contract" "$(stackit_terraform_layer_dir foundation)"
      fi
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "noop" "none" "secrets-manager module has no managed local counterpart; $action is a contract no-op"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  rabbitmq:plan | rabbitmq:apply)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_contract" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "fallback_runtime" "helm" "$(rendered_module_helm_values_file "rabbitmq")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  rabbitmq:destroy)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_reconcile_apply" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "fallback_runtime" "helm" "$(rendered_module_helm_values_file "rabbitmq")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  opensearch:plan | opensearch:apply)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_contract" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "noop" "none" \
        "opensearch module has no managed local counterpart; $action is a contract no-op"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  opensearch:destroy)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_reconcile_apply" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "provider_backed" "noop" "none" \
        "opensearch module has no managed local counterpart; destroy is a contract no-op"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  public-endpoints:plan | public-endpoints:apply | public-endpoints:deploy)
    if is_stackit_profile; then
      optional_module_execution_set "fallback_runtime" "argocd_application_chart" "$(argocd_optional_manifest "public-endpoints")"
    elif is_local_profile; then
      optional_module_execution_set "fallback_runtime" "helm" "$(rendered_module_helm_values_file "public-endpoints")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  public-endpoints:destroy)
    if is_stackit_profile; then
      optional_module_execution_set "fallback_runtime" "argocd_application_chart" "$(argocd_optional_manifest "public-endpoints")"
    elif is_local_profile; then
      optional_module_execution_set "fallback_runtime" "helm" "$(rendered_module_helm_values_file "public-endpoints")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  identity-aware-proxy:plan | identity-aware-proxy:apply | identity-aware-proxy:deploy)
    if is_stackit_profile; then
      optional_module_execution_set "fallback_runtime" "argocd_application_chart" "$(argocd_optional_manifest "identity-aware-proxy")"
    elif is_local_profile; then
      optional_module_execution_set "fallback_runtime" "helm" "$(rendered_module_helm_values_file "identity-aware-proxy")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  identity-aware-proxy:destroy)
    if is_stackit_profile; then
      optional_module_execution_set "fallback_runtime" "argocd_application_chart" "$(argocd_optional_manifest "identity-aware-proxy")"
    elif is_local_profile; then
      optional_module_execution_set "fallback_runtime" "helm" "$(rendered_module_helm_values_file "identity-aware-proxy")"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  kms:plan | kms:apply)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_contract" "$(stackit_terraform_layer_dir foundation)"
    elif is_local_profile; then
      optional_module_execution_set "external_contract" "noop" "none" \
        "kms module has no managed local counterpart; $action is a contract no-op"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  kms:destroy)
    if is_stackit_profile; then
      optional_module_execution_set "provider_backed" "foundation_reconcile_apply" "$(stackit_terraform_layer_dir foundation)" \
        "STACKIT KMS destroy removes the keyring from Terraform state and schedules key deletion through the provider API."
    elif is_local_profile; then
      optional_module_execution_set "external_contract" "noop" "none" \
        "kms module has no managed local counterpart; destroy is a contract no-op"
    else
      log_fatal "unsupported BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    fi
    ;;
  langfuse:plan | langfuse:apply | langfuse:deploy | langfuse:destroy)
    optional_module_execution_set "fallback_runtime" "argocd_optional_manifest" "$(argocd_optional_manifest "langfuse")"
    ;;
  neo4j:plan | neo4j:apply | neo4j:deploy | neo4j:destroy)
    optional_module_execution_set "fallback_runtime" "argocd_optional_manifest" "$(argocd_optional_manifest "neo4j")"
    ;;
  *)
    log_fatal "unsupported optional module execution mapping: module=$module action=$action"
    ;;
  esac

  optional_module_execution_emit_metric "$module" "$action"
}
