#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"

object_storage_init_env() {
  set_default_env OBJECT_STORAGE_BUCKET_NAME "marketplace-assets"
  set_default_env OBJECT_STORAGE_REGION "${STACKIT_REGION:-eu01}"
  set_default_env OBJECT_STORAGE_ACCESS_KEY "minioadmin"
  set_default_env OBJECT_STORAGE_SECRET_KEY "minioadmin123"
  set_default_env OBJECT_STORAGE_NAMESPACE "data"
  set_default_env OBJECT_STORAGE_HELM_RELEASE "blueprint-object-storage"
  set_default_env OBJECT_STORAGE_HELM_CHART "bitnami/minio"
  set_default_env OBJECT_STORAGE_HELM_CHART_VERSION "$OBJECT_STORAGE_HELM_CHART_VERSION_PIN"
  set_default_env OBJECT_STORAGE_ENDPOINT "$(object_storage_endpoint)"

  require_env_vars OBJECT_STORAGE_BUCKET_NAME
}

object_storage_endpoint() {
  if is_stackit_profile; then
    printf 'https://object-storage.%s.onstackit.cloud' "${STACKIT_REGION:-eu01}"
    return 0
  fi
  printf 'http://%s.%s.svc.cluster.local:9000' "$OBJECT_STORAGE_HELM_RELEASE" "$OBJECT_STORAGE_NAMESPACE"
}

object_storage_bucket_name() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "object_storage_bucket_name" "$OBJECT_STORAGE_BUCKET_NAME"
    return 0
  fi
  printf '%s' "$OBJECT_STORAGE_BUCKET_NAME"
}

object_storage_access_key() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "object_storage_access_key" "provider-generated"
    return 0
  fi
  printf '%s' "$OBJECT_STORAGE_ACCESS_KEY"
}

object_storage_secret_key() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "object_storage_secret_access_key" "provider-generated"
    return 0
  fi
  printf '%s' "$OBJECT_STORAGE_SECRET_KEY"
}
