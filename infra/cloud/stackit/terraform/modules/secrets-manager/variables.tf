variable "stackit_project_id" {
  description = "STACKIT project identifier."
  type        = string
}

variable "stackit_region" {
  description = "STACKIT region for all resources. Declared for caller API consistency; not forwarded to provider resources — stackit_secretsmanager_instance and stackit_secretsmanager_user do not accept a region attribute."
  type        = string
  default     = "eu01"
}

variable "secrets_manager_instance_name" {
  description = "Canonical Secrets Manager instance name."
  type        = string
}

variable "secrets_manager_acl" {
  description = "List of CIDR ranges allowed to access the Secrets Manager instance. Empty list disables IP restriction."
  type        = list(string)
  default     = []
}

variable "secrets_manager_user_description" {
  description = "Description for the Secrets Manager user credential."
  type        = string
  default     = "blueprint-managed"
}

variable "secrets_manager_user_write_enabled" {
  description = "Whether the Secrets Manager user has write access."
  type        = bool
  default     = true
}
