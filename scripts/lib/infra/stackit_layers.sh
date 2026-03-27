#!/usr/bin/env bash
set -euo pipefail

# Keep layer path resolution self-contained so smoke/status helpers can source
# this library through foundation-output helpers without relying on caller order.
source "$ROOT_DIR/scripts/lib/infra/stack_paths.sh"

STACKIT_FOUNDATION_SKE_ACCESS_PROBE="${STACKIT_FOUNDATION_SKE_ACCESS_PROBE:-not_applicable}"

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

stackit_trim_whitespace() {
  local value="${1:-}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

stackit_emit_tf_string_list_arg_from_csv() {
  local var_name="$1"
  local raw_csv="${2:-}"
  local raw_values=()
  local rendered="["
  local value=""
  local escaped=""

  IFS=',' read -r -a raw_values <<<"$raw_csv"
  for value in "${raw_values[@]}"; do
    value="$(stackit_trim_whitespace "$value")"
    [[ -n "$value" ]] || continue
    escaped="${value//\\/\\\\}"
    escaped="${escaped//\"/\\\"}"
    if [[ "$rendered" != "[" ]]; then
      rendered+=", "
    fi
    rendered+="\"$escaped\""
  done
  rendered+="]"

  if [[ "$rendered" == "[]" ]]; then
    return 0
  fi

  printf '%s\n' "-var=${var_name}=${rendered}"
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

  if is_module_enabled rabbitmq; then
    require_env_vars RABBITMQ_INSTANCE_NAME
    printf '%s\n' "-var=rabbitmq_instance_name=$RABBITMQ_INSTANCE_NAME"
    if [[ -n "${RABBITMQ_VERSION:-}" ]]; then
      printf '%s\n' "-var=rabbitmq_version=$RABBITMQ_VERSION"
    fi
    if [[ -n "${RABBITMQ_PLAN_NAME:-}" ]]; then
      printf '%s\n' "-var=rabbitmq_plan_name=$RABBITMQ_PLAN_NAME"
    fi
  fi

  if is_module_enabled postgres; then
    require_env_vars POSTGRES_INSTANCE_NAME POSTGRES_DB_NAME POSTGRES_USER
    printf '%s\n' "-var=postgres_instance_name=$POSTGRES_INSTANCE_NAME"
    printf '%s\n' "-var=postgres_db_name=$POSTGRES_DB_NAME"
    printf '%s\n' "-var=postgres_username=$POSTGRES_USER"
    if [[ -n "${POSTGRES_VERSION:-}" ]]; then
      printf '%s\n' "-var=postgres_version=$POSTGRES_VERSION"
    fi
    if [[ -n "${POSTGRES_EXTRA_ALLOWED_CIDRS:-}" ]]; then
      stackit_emit_tf_string_list_arg_from_csv "postgres_acl" "$POSTGRES_EXTRA_ALLOWED_CIDRS"
    fi
  fi

  if is_module_enabled object-storage; then
    require_env_vars OBJECT_STORAGE_BUCKET_NAME
    printf '%s\n' "-var=object_storage_bucket_name=$OBJECT_STORAGE_BUCKET_NAME"
  fi

  if is_module_enabled dns; then
    require_env_vars DNS_ZONE_NAME DNS_ZONE_FQDN
    # The runtime contract keeps DNS_ZONE_NAME as the consumer-facing alias,
    # while foundation provisioning keys off the canonical FQDN list.
    stackit_emit_tf_string_list_arg_from_csv "dns_zone_fqdns" "$DNS_ZONE_FQDN"
  fi

  if is_module_enabled secrets-manager; then
    require_env_vars SECRETS_MANAGER_INSTANCE_NAME
    printf '%s\n' "-var=secrets_manager_instance_name=$SECRETS_MANAGER_INSTANCE_NAME"
  fi

  if is_module_enabled kms; then
    require_env_vars KMS_KEY_RING_NAME KMS_KEY_NAME
    printf '%s\n' "-var=kms_key_ring_name=$KMS_KEY_RING_NAME"
    printf '%s\n' "-var=kms_key_name=$KMS_KEY_NAME"
    if [[ -n "${KMS_KEY_RING_DESCRIPTION:-}" ]]; then
      printf '%s\n' "-var=kms_key_ring_description=$KMS_KEY_RING_DESCRIPTION"
    fi
    if [[ -n "${KMS_KEY_DESCRIPTION:-}" ]]; then
      printf '%s\n' "-var=kms_key_description=$KMS_KEY_DESCRIPTION"
    fi
    if [[ -n "${KMS_KEY_ALGORITHM:-}" ]]; then
      printf '%s\n' "-var=kms_key_algorithm=$KMS_KEY_ALGORITHM"
    fi
    if [[ -n "${KMS_KEY_PURPOSE:-}" ]]; then
      printf '%s\n' "-var=kms_key_purpose=$KMS_KEY_PURPOSE"
    fi
    if [[ -n "${KMS_KEY_PROTECTION:-}" ]]; then
      printf '%s\n' "-var=kms_key_protection=$KMS_KEY_PROTECTION"
    fi
    if [[ -n "${KMS_KEY_ACCESS_SCOPE:-}" ]]; then
      printf '%s\n' "-var=kms_key_access_scope=$KMS_KEY_ACCESS_SCOPE"
    fi
    if [[ -n "${KMS_KEY_IMPORT_ONLY:-}" ]]; then
      printf '%s\n' "-var=kms_key_import_only=$KMS_KEY_IMPORT_ONLY"
    fi
  fi
}

stackit_flatten_file_to_single_line() {
  local file_path="$1"
  if [[ ! -f "$file_path" ]]; then
    echo ""
    return 0
  fi
  tr '\n' ' ' <"$file_path" | sed -E 's/[[:space:]]+/ /g; s/^ //; s/ $//'
}

stackit_resolve_service_account_access_token_with_stackit() {
  local service_account_key="$1"
  local normalized_service_account_key="$service_account_key"
  local temp_key_file=""
  local access_token=""
  local stackit_auth_rc=0

  # Accept service account values from env exports where surrounding whitespace is accidental.
  normalized_service_account_key="${normalized_service_account_key#"${normalized_service_account_key%%[![:space:]]*}"}"
  normalized_service_account_key="${normalized_service_account_key%"${normalized_service_account_key##*[![:space:]]}"}"

  if [[ -f "$normalized_service_account_key" ]]; then
    stackit auth activate-service-account \
      --service-account-key-path "$normalized_service_account_key" \
      --only-print-access-token
    return 0
  fi

  if [[ "$normalized_service_account_key" == \{* ]]; then
    temp_key_file="$(mktemp)"
    chmod 600 "$temp_key_file"
    printf '%s' "$normalized_service_account_key" >"$temp_key_file"
    set +e
    access_token="$(
      stackit auth activate-service-account \
      --service-account-key-path "$temp_key_file" \
      --only-print-access-token
    )"
    stackit_auth_rc=$?
    set -e
    rm -f "$temp_key_file"
    if [[ "$stackit_auth_rc" -ne 0 ]]; then
      return "$stackit_auth_rc"
    fi
    printf '%s' "$access_token"
    return 0
  fi

  stackit auth activate-service-account \
    --service-account-token "$normalized_service_account_key" \
    --only-print-access-token
}

stackit_resolve_service_account_access_token() {
  local service_account_key="$1"
  local stackit_auth_stderr_file=""
  local stackit_auth_error=""
  local access_token=""

  require_command stackit

  stackit_auth_stderr_file="$(mktemp)"
  if ! access_token="$(
    stackit_resolve_service_account_access_token_with_stackit "$service_account_key" 2>"$stackit_auth_stderr_file"
  )"; then
    stackit_auth_error="$(stackit_flatten_file_to_single_line "$stackit_auth_stderr_file")"
    rm -f "$stackit_auth_stderr_file"
    if [[ -n "$stackit_auth_error" ]]; then
      log_warn "stackit auth stderr: $stackit_auth_error"
    fi
    log_fatal "failed to resolve STACKIT access token from STACKIT_SERVICE_ACCOUNT_KEY using stackit auth activate-service-account"
  fi
  rm -f "$stackit_auth_stderr_file"

  access_token="${access_token//$'\n'/}"
  access_token="${access_token//$'\r'/}"
  if [[ -z "$access_token" ]]; then
    log_fatal "resolved STACKIT access token is empty"
  fi

  printf '%s' "$access_token"
}

stackit_ske_probe_endpoint() {
  local probe_name="$1"
  local url="$2"
  local access_token="$3"
  local stderr_file=""
  local response_file=""
  local stderr_compact=""
  local response_compact=""
  local combined_compact=""

  stderr_file="$(mktemp)"
  response_file="$(mktemp)"

  if stackit curl "$url" \
    --fail \
    --output "$response_file" \
    -H "Authorization: Bearer $access_token" >/dev/null 2>"$stderr_file"; then
    rm -f "$stderr_file" "$response_file"
    log_metric "infra_stackit_foundation_ske_probe" "1" "probe=$probe_name status=success"
    return 0
  fi

  stderr_compact="$(stackit_flatten_file_to_single_line "$stderr_file")"
  response_compact="$(stackit_flatten_file_to_single_line "$response_file")"
  combined_compact="$stderr_compact $response_compact"

  rm -f "$stderr_file" "$response_file"
  log_metric "infra_stackit_foundation_ske_probe" "0" "probe=$probe_name status=failure"

  if [[ "$combined_compact" == *"403"* ]] || [[ "$combined_compact" == *"Forbidden"* ]] || [[ "$combined_compact" == *"forbidden"* ]] || [[ "$combined_compact" == *"Unauthorized"* ]] || [[ "$combined_compact" == *"unauthorized"* ]] || [[ "$combined_compact" == *"Permission"* ]] || [[ "$combined_compact" == *"permission"* ]] || [[ "$combined_compact" == *"AccessDenied"* ]]; then
    log_fatal "STACKIT foundation preflight failed: service account lacks SKE permissions for probe=$probe_name project=$STACKIT_PROJECT_ID region=$STACKIT_REGION. Ensure STACKIT_SERVICE_ACCOUNT_KEY has SKE service enable/list/read permissions (for example Project Admin) before running foundation apply."
  fi

  if [[ -z "$combined_compact" ]]; then
    combined_compact="no error details emitted by stackit curl"
  fi
  log_fatal "STACKIT foundation preflight SKE probe failed: probe=$probe_name project=$STACKIT_PROJECT_ID region=$STACKIT_REGION details=$combined_compact"
}

stackit_ske_cluster_list_probe() {
  local stderr_file=""
  local output_compact=""

  stderr_file="$(mktemp)"

  if stackit ske cluster list \
    --project-id "$STACKIT_PROJECT_ID" \
    --region "$STACKIT_REGION" \
    --output-format json >/dev/null 2>"$stderr_file"; then
    rm -f "$stderr_file"
    log_metric "infra_stackit_foundation_ske_probe" "1" "probe=cluster-list-read status=success"
    return 0
  fi

  output_compact="$(stackit_flatten_file_to_single_line "$stderr_file")"
  rm -f "$stderr_file"

  if [[ "$output_compact" == *"isn't enabled for this project"* ]] || [[ "$output_compact" == *"not enabled for this project"* ]] || [[ "$output_compact" == *"Not found"* ]] || [[ "$output_compact" == *"status\": 404"* ]]; then
    log_metric "infra_stackit_foundation_ske_probe" "1" "probe=cluster-list-read status=skipped_service_disabled_or_empty"
    log_warn "SKE cluster list probe skipped because SKE is not enabled yet or no clusters exist (project=$STACKIT_PROJECT_ID region=$STACKIT_REGION)"
    return 0
  fi

  log_metric "infra_stackit_foundation_ske_probe" "0" "probe=cluster-list-read status=failure"
  if [[ "$output_compact" == *"403"* ]] || [[ "$output_compact" == *"Forbidden"* ]] || [[ "$output_compact" == *"forbidden"* ]] || [[ "$output_compact" == *"Unauthorized"* ]] || [[ "$output_compact" == *"unauthorized"* ]] || [[ "$output_compact" == *"Permission"* ]] || [[ "$output_compact" == *"permission"* ]] || [[ "$output_compact" == *"AccessDenied"* ]]; then
    log_fatal "STACKIT foundation preflight failed: service account lacks SKE cluster list/read permissions for project=$STACKIT_PROJECT_ID region=$STACKIT_REGION. Ensure STACKIT_SERVICE_ACCOUNT_KEY has SKE cluster list/read permissions."
  fi

  if [[ -z "$output_compact" ]]; then
    output_compact="no error details emitted by stackit ske cluster list"
  fi
  log_fatal "STACKIT foundation preflight SKE cluster list probe failed: project=$STACKIT_PROJECT_ID region=$STACKIT_REGION details=$output_compact"
}

stackit_foundation_ske_preflight() {
  if ! tooling_is_execution_enabled; then
    export STACKIT_FOUNDATION_SKE_ACCESS_PROBE="skipped_dry_run"
    return 0
  fi

  local access_token=""
  local service_endpoint_url=""

  access_token="$(stackit_resolve_service_account_access_token "$STACKIT_SERVICE_ACCOUNT_KEY")"
  service_endpoint_url="https://service-enablement.api.stackit.cloud/v2/projects/$STACKIT_PROJECT_ID/regions/$STACKIT_REGION/services/cloud.stackit.ske"

  # Probe SKE service access via Service Enablement before terraform apply.
  # Cluster listing is best-effort because a greenfield project can legitimately have no SKE enabled yet.
  stackit_ske_probe_endpoint "service-enable-read" "$service_endpoint_url" "$access_token"
  stackit_ske_cluster_list_probe

  export STACKIT_FOUNDATION_SKE_ACCESS_PROBE="passed"
}

stackit_layer_preflight() {
  local layer="$1"
  local target_name=""
  target_name="infra-stackit-$(stackit_layer_label "$layer")-preflight"
  export STACKIT_FOUNDATION_SKE_ACCESS_PROBE="not_applicable"

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
    if [[ "$layer" == "foundation" ]]; then
      stackit_foundation_ske_preflight
    fi
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
    if [[ "$layer" == "foundation" ]]; then
      export STACKIT_FOUNDATION_SKE_ACCESS_PROBE="skipped_dry_run"
    fi
  fi

  return 0
}
