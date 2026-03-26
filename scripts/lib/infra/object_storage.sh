#!/usr/bin/env bash
set -euo pipefail

object_storage_init_env() {
  set_default_env OBJECT_STORAGE_BUCKET_NAME "marketplace-assets"
  set_default_env OBJECT_STORAGE_REGION "${STACKIT_REGION:-eu01}"
  set_default_env OBJECT_STORAGE_ACCESS_KEY "minioadmin"
  set_default_env OBJECT_STORAGE_SECRET_KEY "minioadmin123"
  set_default_env OBJECT_STORAGE_NAMESPACE "data"
  set_default_env OBJECT_STORAGE_HELM_RELEASE "blueprint-object-storage"
  set_default_env OBJECT_STORAGE_HELM_CHART "bitnami/minio"
  set_default_env OBJECT_STORAGE_HELM_CHART_VERSION "17.0.17"
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
