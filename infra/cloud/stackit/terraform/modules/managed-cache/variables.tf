variable "stackit_project_id" {
  description = "STACKIT project identifier."
  type        = string
}

variable "stackit_region" {
  description = "STACKIT region for all resources."
  type        = string
  default     = "eu01"
}

variable "managed_cache_instance_name" {
  description = "Canonical managed cache (Redis) instance name."
  type        = string
}

variable "managed_cache_version" {
  description = "Redis major version."
  type        = string
  default     = "7"
}

variable "managed_cache_plan_name" {
  description = "STACKIT Redis service plan name."
  type        = string
  default     = "stackit-redis-1.4.10-replica"
}

variable "managed_cache_sgw_acl" {
  description = "Comma-separated CIDR ranges allowed to access the Redis instance via SKE egress gateway."
  type        = string
  default     = ""
}
