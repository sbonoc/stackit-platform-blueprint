variable "stackit_project_id" {
  description = "STACKIT project identifier."
  type        = string
}

variable "stackit_region" {
  description = "STACKIT region for all resources."
  type        = string
  default     = "eu01"
}

variable "ske_enabled" {
  description = "When true, SKE egress ranges are used to derive the ACL allowlist."
  type        = bool
  default     = false
}

variable "postgres_instance_name" {
  description = "Canonical PostgreSQL Flex instance name."
  type        = string
}

variable "postgres_db_name" {
  description = "Database name to provision in PostgreSQL Flex."
  type        = string
  default     = "app"
}

variable "postgres_username" {
  description = "Runtime PostgreSQL Flex username."
  type        = string
  default     = "app"
}

variable "postgres_user_roles" {
  description = "Roles assigned to the PostgreSQL Flex runtime user."
  type        = set(string)
  default     = ["login"]
}

variable "postgres_version" {
  description = "PostgreSQL Flex major version."
  type        = string
  default     = "16"
}

variable "postgres_replicas" {
  description = "PostgreSQL Flex replica count."
  type        = number
  default     = 1
}

variable "postgres_acl" {
  description = "ACL CIDR allowlist for PostgreSQL Flex access."
  type        = list(string)
  default     = []

  validation {
    condition     = length(var.postgres_acl) > 0 || var.ske_enabled
    error_message = "postgres_acl must be non-empty or ske_enabled must be true so ACLs can be derived from SKE egress ranges."
  }
}

variable "postgres_backup_schedule" {
  description = "PostgreSQL Flex backup cron schedule."
  type        = string
  default     = "0 2 * * *"
}

variable "postgres_flavor_cpu" {
  description = "vCPU count for PostgreSQL Flex flavor."
  type        = number
  default     = 2
}

variable "postgres_flavor_ram" {
  description = "RAM in GiB for PostgreSQL Flex flavor."
  type        = number
  default     = 4
}

variable "postgres_storage_class" {
  description = "Storage class for PostgreSQL Flex."
  type        = string
  default     = "premium-perf2-stackit"
}

variable "postgres_storage_size_gb" {
  description = "Storage size in GiB for PostgreSQL Flex."
  type        = number
  default     = 20
}
