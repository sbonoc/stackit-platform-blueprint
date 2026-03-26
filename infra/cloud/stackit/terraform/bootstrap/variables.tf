variable "environment" {
  description = "Deployment environment identifier (dev|stage|prod)."
  type        = string

  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment must be one of: dev, stage, prod."
  }
}

variable "tenant_slug" {
  description = "Short deterministic tenant/org slug used in resource naming."
  type        = string
}

variable "platform_slug" {
  description = "Short deterministic platform slug used in resource naming."
  type        = string
}

variable "stackit_project_id" {
  description = "STACKIT project identifier where resources will be provisioned."
  type        = string
}

variable "stackit_region" {
  description = "Canonical STACKIT region for this environment."
  type        = string
}

variable "state_key_prefix" {
  description = "Prefix for deterministic remote Terraform state object keys."
  type        = string
  default     = "terraform/state"
}
