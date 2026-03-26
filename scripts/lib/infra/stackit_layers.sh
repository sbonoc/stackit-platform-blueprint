#!/usr/bin/env bash
set -euo pipefail

stackit_layer_label() {
  local layer="$1"
  case "$layer" in
  bootstrap)
    echo "bootstrap"
    ;;
  foundation)
    echo "foundation"
    ;;
  *)
    log_fatal "unsupported stackit layer: $layer"
    ;;
  esac
}

stackit_layer_dir() {
  local layer="$1"
  stackit_layer_label "$layer" >/dev/null

  local configured_dir=""
  case "$layer" in
  bootstrap)
    set_default_env STACKIT_BOOTSTRAP_TERRAFORM_DIR "$(stackit_terraform_layer_dir bootstrap)"
    configured_dir="$STACKIT_BOOTSTRAP_TERRAFORM_DIR"
    ;;
  foundation)
    set_default_env STACKIT_FOUNDATION_TERRAFORM_DIR "$(stackit_terraform_layer_dir foundation)"
    configured_dir="$STACKIT_FOUNDATION_TERRAFORM_DIR"
    ;;
  esac

  if [[ "$configured_dir" != /* ]]; then
    configured_dir="$ROOT_DIR/$configured_dir"
  fi
  echo "$configured_dir"
}

stackit_layer_backend_file() {
  local layer="$1"
  stackit_layer_label "$layer" >/dev/null

  local backend_file=""
  case "$layer" in
  bootstrap)
    set_default_env STACKIT_BOOTSTRAP_BACKEND_FILE "$(stackit_terraform_layer_backend_file bootstrap)"
    backend_file="$STACKIT_BOOTSTRAP_BACKEND_FILE"
    ;;
  foundation)
    set_default_env STACKIT_FOUNDATION_BACKEND_FILE "$(stackit_terraform_layer_backend_file foundation)"
    backend_file="$STACKIT_FOUNDATION_BACKEND_FILE"
    ;;
  esac

  if [[ "$backend_file" != /* ]]; then
    backend_file="$ROOT_DIR/$backend_file"
  fi
  echo "$backend_file"
}

stackit_layer_var_file() {
  local layer="$1"
  stackit_layer_label "$layer" >/dev/null

  local var_file=""
  case "$layer" in
  bootstrap)
    set_default_env STACKIT_BOOTSTRAP_VAR_FILE "$(stackit_terraform_layer_var_file bootstrap)"
    var_file="$STACKIT_BOOTSTRAP_VAR_FILE"
    ;;
  foundation)
    set_default_env STACKIT_FOUNDATION_VAR_FILE "$(stackit_terraform_layer_var_file foundation)"
    var_file="$STACKIT_FOUNDATION_VAR_FILE"
    ;;
  esac

  if [[ "$var_file" != /* ]]; then
    var_file="$ROOT_DIR/$var_file"
  fi
  echo "$var_file"
}

stackit_layer_validate_backend_contract() {
  local backend_file="$1"

  if ! grep -q "skip_requesting_account_id" "$backend_file"; then
    log_fatal "backend config '$backend_file' must set skip_requesting_account_id for STACKIT S3 compatibility"
  fi
  if ! grep -q "use_path_style" "$backend_file"; then
    log_fatal "backend config '$backend_file' must set use_path_style for STACKIT S3 compatibility"
  fi
  if ! grep -q "object.storage" "$backend_file"; then
    log_fatal "backend config '$backend_file' must point to STACKIT Object Storage endpoint"
  fi
}

stackit_module_enabled_tf_bool() {
  local module="$1"
  if is_module_enabled "$module"; then
    echo "true"
    return 0
  fi
  echo "false"
}

stackit_layer_var_args() {
  local layer="$1"
  stackit_layer_label "$layer" >/dev/null

  # Resolve explicit runtime values first, then blueprint init values.
  # Dry-run wrappers may rely on placeholder defaults to keep command traces deterministic.
  local project_id="${STACKIT_PROJECT_ID:-${BLUEPRINT_STACKIT_PROJECT_ID:-project-placeholder}}"
  local region="${STACKIT_REGION:-${BLUEPRINT_STACKIT_REGION:-eu01}}"
  local tenant_slug="${STACKIT_TENANT_SLUG:-${BLUEPRINT_STACKIT_TENANT_SLUG:-}}"
  local platform_slug="${STACKIT_PLATFORM_SLUG:-${BLUEPRINT_STACKIT_PLATFORM_SLUG:-}}"

  printf '%s\n' "-var=stackit_project_id=$project_id"
  printf '%s\n' "-var=stackit_region=$region"

  if [[ -n "$tenant_slug" ]]; then
    printf '%s\n' "-var=tenant_slug=$tenant_slug"
  fi
  if [[ -n "$platform_slug" ]]; then
    printf '%s\n' "-var=platform_slug=$platform_slug"
  fi

  if [[ "$layer" != "foundation" ]]; then
    return 0
  fi

  printf '%s\n' "-var=observability_enabled=$(stackit_module_enabled_tf_bool observability)"
  printf '%s\n' "-var=workflows_enabled=$(stackit_module_enabled_tf_bool workflows)"
  printf '%s\n' "-var=langfuse_enabled=$(stackit_module_enabled_tf_bool langfuse)"
  printf '%s\n' "-var=postgres_enabled=$(stackit_module_enabled_tf_bool postgres)"
  printf '%s\n' "-var=neo4j_enabled=$(stackit_module_enabled_tf_bool neo4j)"
  printf '%s\n' "-var=object_storage_enabled=$(stackit_module_enabled_tf_bool object-storage)"
  printf '%s\n' "-var=rabbitmq_enabled=$(stackit_module_enabled_tf_bool rabbitmq)"
  printf '%s\n' "-var=dns_enabled=$(stackit_module_enabled_tf_bool dns)"
  printf '%s\n' "-var=public_endpoints_enabled=$(stackit_module_enabled_tf_bool public-endpoints)"
  printf '%s\n' "-var=secrets_manager_enabled=$(stackit_module_enabled_tf_bool secrets-manager)"
  printf '%s\n' "-var=kms_enabled=$(stackit_module_enabled_tf_bool kms)"
  printf '%s\n' "-var=identity_aware_proxy_enabled=$(stackit_module_enabled_tf_bool identity-aware-proxy)"
}

stackit_layer_preflight() {
  local layer="$1"
  local target_name="infra-stackit-$(stackit_layer_label "$layer")-preflight"

  if ! is_stackit_profile; then
    log_fatal "$target_name requires stackit-* profile; got BLUEPRINT_PROFILE=${BLUEPRINT_PROFILE:-unset}"
  fi

  local env_name
  env_name="$(profile_environment)"
  case "$env_name" in
  dev | stage | prod)
    ;;
  *)
    log_fatal "unsupported stackit environment '$env_name' from BLUEPRINT_PROFILE=$BLUEPRINT_PROFILE"
    ;;
  esac

  local layer_dir
  layer_dir="$(stackit_layer_dir "$layer")"
  local backend_file
  backend_file="$(stackit_layer_backend_file "$layer")"
  local var_file
  var_file="$(stackit_layer_var_file "$layer")"

  if [[ ! -d "$layer_dir" ]]; then
    log_fatal "missing STACKIT terraform directory for layer=$layer: $layer_dir"
  fi
  if ! terraform_dir_has_config "$layer_dir"; then
    log_fatal "terraform configuration not found for layer=$layer in $layer_dir"
  fi
  if [[ ! -f "$backend_file" ]]; then
    log_fatal "missing STACKIT backend file for layer=$layer: $backend_file"
  fi
  if [[ ! -f "$var_file" ]]; then
    log_fatal "missing STACKIT var-file for layer=$layer: $var_file"
  fi

  stackit_layer_validate_backend_contract "$backend_file"

  if tooling_is_execution_enabled; then
    require_env_vars \
      STACKIT_PROJECT_ID \
      STACKIT_REGION \
      STACKIT_SERVICE_ACCOUNT_KEY \
      STACKIT_TFSTATE_ACCESS_KEY_ID \
      STACKIT_TFSTATE_SECRET_ACCESS_KEY
    export STACKIT_TFSTATE_CREDENTIAL_SOURCE="environment"
  else
    # In dry-run mode keep deterministic placeholder values so wrapper state artifacts
    # can still be produced without requiring live credentials.
    set_default_env STACKIT_PROJECT_ID "${BLUEPRINT_STACKIT_PROJECT_ID:-project-placeholder}"
    set_default_env STACKIT_REGION "${BLUEPRINT_STACKIT_REGION:-eu01}"
    set_default_env STACKIT_SERVICE_ACCOUNT_KEY "service-account-key-placeholder"
    set_default_env STACKIT_TFSTATE_BUCKET "${BLUEPRINT_STACKIT_TFSTATE_BUCKET:-tfstate-bucket-placeholder}"
    set_default_env STACKIT_TFSTATE_ACCESS_KEY_ID "tfstate-access-key-placeholder"
    set_default_env STACKIT_TFSTATE_SECRET_ACCESS_KEY "tfstate-secret-key-placeholder"
    export STACKIT_TFSTATE_CREDENTIAL_SOURCE="dry-run-placeholder"
  fi

  return 0
}
