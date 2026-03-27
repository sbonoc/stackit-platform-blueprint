#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"

kms_init_env() {
  set_default_env KMS_KEY_RING_NAME "marketplace-ring"
  set_default_env KMS_KEY_NAME "marketplace-key"
  set_default_env KMS_KEY_RING_DESCRIPTION "Blueprint-managed KMS keyring."
  set_default_env KMS_KEY_DESCRIPTION "Blueprint-managed KMS key."
  set_default_env KMS_KEY_ALGORITHM "aes_256_gcm"
  set_default_env KMS_KEY_PURPOSE "symmetric_encrypt_decrypt"
  set_default_env KMS_KEY_PROTECTION "software"
  set_default_env KMS_KEY_ACCESS_SCOPE "PUBLIC"
  set_default_env KMS_KEY_IMPORT_ONLY "false"

  require_env_vars KMS_KEY_RING_NAME KMS_KEY_NAME
}

kms_key_ring_id() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "kms_key_ring_id" "kms://$KMS_KEY_RING_NAME"
    return 0
  fi
  printf 'kms://%s' "$KMS_KEY_RING_NAME"
}

kms_key_id() {
  if is_stackit_profile; then
    stackit_foundation_output_value_or_default "kms_key_id" "kms://$KMS_KEY_RING_NAME/$KMS_KEY_NAME"
    return 0
  fi
  printf 'kms://%s/%s' "$KMS_KEY_RING_NAME" "$KMS_KEY_NAME"
}
