terraform {
  required_version = ">= 1.13.0"
}

locals {
  contract = "blueprint"
}

# STACKIT KMS destroy is intentionally conservative: the keyring is removed
# from Terraform state without an API deletion, and keys are scheduled for
# deletion rather than immediately deleted, following the provider contract.
resource "stackit_kms_keyring" "this" {
  project_id   = var.stackit_project_id
  region       = var.stackit_region
  display_name = var.kms_key_ring_name
  description  = var.kms_key_ring_description

  lifecycle {
    create_before_destroy = true
  }
}

resource "stackit_kms_key" "this" {
  project_id   = var.stackit_project_id
  region       = var.stackit_region
  keyring_id   = stackit_kms_keyring.this.keyring_id
  display_name = var.kms_key_name
  description  = var.kms_key_description
  algorithm    = var.kms_key_algorithm
  purpose      = var.kms_key_purpose
  protection   = var.kms_key_protection
  access_scope = var.kms_key_access_scope
  import_only  = var.kms_key_import_only
}
