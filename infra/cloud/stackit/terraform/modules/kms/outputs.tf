output "kms_keyring_id" {
  description = "The ID of the provisioned KMS keyring."
  value       = stackit_kms_keyring.this.keyring_id
}

output "kms_keyring_display_name" {
  description = "The display name of the provisioned KMS keyring."
  value       = stackit_kms_keyring.this.display_name
}

output "kms_key_id" {
  description = "The ID of the provisioned KMS key."
  value       = stackit_kms_key.this.key_id
}

output "kms_key_display_name" {
  description = "The display name of the provisioned KMS key."
  value       = stackit_kms_key.this.display_name
}
