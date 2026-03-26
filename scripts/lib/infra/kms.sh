#!/usr/bin/env bash
set -euo pipefail

kms_init_env() {
  set_default_env KMS_KEY_RING_NAME "marketplace-ring"
  set_default_env KMS_KEY_NAME "marketplace-key"

  require_env_vars KMS_KEY_RING_NAME KMS_KEY_NAME
}

kms_key_id() {
  printf 'kms://%s/%s' "$KMS_KEY_RING_NAME" "$KMS_KEY_NAME"
}
