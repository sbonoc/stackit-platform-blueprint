#!/usr/bin/env bash
set -euo pipefail

source "$ROOT_DIR/scripts/lib/infra/stackit_foundation_outputs.sh"
source "$ROOT_DIR/scripts/lib/infra/versions.sh"
source "$ROOT_DIR/scripts/lib/infra/fallback_runtime.sh"

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
  set_default_env KMS_NAMESPACE "kms"
  set_default_env KMS_VAULT_HELM_RELEASE "blueprint-vault"
  set_default_env KMS_VAULT_HELM_CHART "hashicorp/vault"
  set_default_env KMS_VAULT_HELM_CHART_VERSION "$KMS_VAULT_HELM_CHART_VERSION_PIN"
  set_default_env KMS_VAULT_ROOT_TOKEN "blueprint-vault-root-token"

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

kms_endpoint() {
  if is_stackit_profile; then
    local region
    region="${STACKIT_REGION:-${BLUEPRINT_STACKIT_REGION:-eu01}}"
    printf 'https://kms.api.%s.stackit.cloud' "$region"
    return 0
  fi
  printf 'http://blueprint-vault.%s.svc.cluster.local:8200/v1/transit' "${KMS_NAMESPACE:-kms}"
}

kms_vault_secret_name() {
  printf '%s-credentials' "$KMS_VAULT_HELM_RELEASE"
}

kms_render_values_file() {
  render_optional_module_values_file \
    "kms" \
    "infra/local/helm/kms/values.yaml" \
    "KMS_VAULT_ROOT_TOKEN=${KMS_VAULT_ROOT_TOKEN:-blueprint-vault-root-token}"
}

kms_reconcile_runtime_secret() {
  apply_optional_module_secret_from_literals \
    "$KMS_NAMESPACE" \
    "$(kms_vault_secret_name)" \
    "vault-token=${KMS_VAULT_ROOT_TOKEN:-blueprint-vault-root-token}" \
    "vault-endpoint=$(kms_endpoint)"
}

kms_delete_runtime_secret() {
  delete_optional_module_secret "$KMS_NAMESPACE" "$(kms_vault_secret_name)"
}

kms_enable_vault_transit() {
  local vault_pod
  vault_pod="$(kubectl get pod \
    -n "$KMS_NAMESPACE" \
    -l "app.kubernetes.io/name=vault,app.kubernetes.io/instance=$KMS_VAULT_HELM_RELEASE" \
    -o jsonpath='{.items[0].metadata.name}')"
  kubectl exec -n "$KMS_NAMESPACE" "$vault_pod" -- vault secrets enable transit 2>/dev/null || true
  kubectl exec -n "$KMS_NAMESPACE" "$vault_pod" -- \
    vault write "transit/keys/$KMS_KEY_NAME" type="aes256-gcm96"
}
