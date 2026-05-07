variable "stackit_project_id" {
  type        = string
  description = "STACKIT project ID."
}

variable "stackit_region" {
  type        = string
  description = "STACKIT region."
  default     = "eu01"
}

variable "kms_key_ring_name" {
  type        = string
  description = "Display name for the KMS keyring."
}

variable "kms_key_name" {
  type        = string
  description = "Display name for the KMS key."
}

variable "kms_key_ring_description" {
  type        = string
  description = "Description for the KMS keyring."
  default     = "Blueprint-managed KMS keyring."
}

variable "kms_key_description" {
  type        = string
  description = "Description for the KMS key."
  default     = "Blueprint-managed KMS key."
}

variable "kms_key_algorithm" {
  type        = string
  description = "KMS key algorithm."
  default     = "aes_256_gcm"
}

variable "kms_key_purpose" {
  type        = string
  description = "KMS key purpose."
  default     = "symmetric_encrypt_decrypt"
}

variable "kms_key_protection" {
  type        = string
  description = "KMS key protection mode."
  default     = "software"
}

variable "kms_key_access_scope" {
  type        = string
  description = "KMS key access scope."
  default     = "PUBLIC"
}

variable "kms_key_import_only" {
  type        = bool
  description = "Whether the KMS key is import-only."
  default     = false
}
