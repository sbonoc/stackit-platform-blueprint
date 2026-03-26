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

variable "ske_enabled" {
  description = "Enable SKE foundation provisioning contract."
  type        = bool
  default     = true
}

variable "ske_default_node_pool_name" {
  description = "Default node-pool name for the managed SKE cluster."
  type        = string
  default     = "default"
}

variable "ske_default_node_pool_machine_type" {
  description = "Default node-pool machine type for SKE."
  type        = string
  default     = "c2i.2"
}

variable "ske_default_node_pool_min" {
  description = "Minimum node count for default SKE node pool."
  type        = number
  default     = 1
}

variable "ske_default_node_pool_max" {
  description = "Maximum node count for default SKE node pool."
  type        = number
  default     = 2
}

variable "ske_default_node_pool_availability_zones" {
  description = "Availability zones assigned to default SKE node pool."
  type        = list(string)
  default     = ["eu01-1"]
}

variable "dns_enabled" {
  description = "Enable DNS foundation provisioning contract."
  type        = bool
  default     = false
}

variable "dns_zone_fqdns" {
  description = "DNS zones to provision when DNS module is enabled (must end with a dot)."
  type        = list(string)
  default     = []
}

variable "postgres_enabled" {
  description = "Enable PostgreSQL Flex provisioning contract."
  type        = bool
  default     = false
}

variable "postgres_instance_name_suffix" {
  description = "Suffix used when naming PostgreSQL Flex instance."
  type        = string
  default     = "postgres"
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
  description = "Roles assigned to PostgreSQL Flex runtime user."
  type        = set(string)
  default     = ["login"]
}

variable "postgres_acl" {
  description = "Optional ACL CIDR allowlist for PostgreSQL Flex access."
  type        = list(string)
  default     = []
}

variable "postgres_backup_schedule" {
  description = "PostgreSQL Flex backup cron schedule."
  type        = string
  default     = "0 2 * * *"
}

variable "postgres_version" {
  description = "PostgreSQL Flex major version."
  type        = string
  default     = "17"
}

variable "postgres_replicas" {
  description = "PostgreSQL Flex replica count."
  type        = number
  default     = 1
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

variable "object_storage_enabled" {
  description = "Enable Object Storage provisioning contract."
  type        = bool
  default     = false
}

variable "object_storage_bucket_name_suffix" {
  description = "Suffix used when naming Object Storage bucket."
  type        = string
  default     = "assets"
}

variable "object_storage_credentials_group_name_suffix" {
  description = "Suffix used when naming Object Storage credentials group."
  type        = string
  default     = "runtime-creds"
}

variable "object_storage_credential_expiration_timestamp" {
  description = "Optional credential expiration timestamp in RFC3339 format."
  type        = string
  default     = null
}

variable "secrets_manager_enabled" {
  description = "Enable Secrets Manager provisioning contract."
  type        = bool
  default     = false
}

variable "secrets_manager_instance_name_suffix" {
  description = "Suffix used when naming Secrets Manager instance."
  type        = string
  default     = "secrets"
}

variable "secrets_manager_acl" {
  description = "Optional ACL CIDR allowlist for Secrets Manager instance."
  type        = set(string)
  default     = []
}

variable "secrets_manager_user_description" {
  description = "Description used for managed Secrets Manager runtime user."
  type        = string
  default     = "Runtime user managed by Terraform foundation."
}

variable "secrets_manager_user_write_enabled" {
  description = "Whether managed Secrets Manager runtime user can write secrets."
  type        = bool
  default     = true
}

variable "observability_enabled" {
  description = "Enable managed Observability provisioning contract."
  type        = bool
  default     = false
}

variable "observability_instance_name_suffix" {
  description = "Suffix used when naming Observability instance."
  type        = string
  default     = "observability"
}

variable "observability_plan_name" {
  description = "STACKIT Observability plan name."
  type        = string
  default     = "Observability-Monitoring-Medium-EU01"
}

variable "observability_acl" {
  description = "Optional ACL CIDR allowlist for Observability instance."
  type        = set(string)
  default     = []
}

variable "observability_grafana_admin_enabled" {
  description = "Whether Grafana local admin should be enabled on Observability instance."
  type        = bool
  default     = false
}

variable "observability_logs_retention_days" {
  description = "Logs retention in days for Observability."
  type        = number
  default     = 14
}

variable "observability_metrics_retention_days" {
  description = "Metrics retention in days for Observability."
  type        = number
  default     = 90
}

variable "observability_metrics_retention_days_5m_downsampling" {
  description = "5m-downsampled metrics retention in days for Observability."
  type        = number
  default     = 180
}

variable "observability_metrics_retention_days_1h_downsampling" {
  description = "1h-downsampled metrics retention in days for Observability."
  type        = number
  default     = 365
}

variable "observability_traces_retention_days" {
  description = "Traces retention in days for Observability."
  type        = number
  default     = 14
}

variable "workflows_enabled" {
  description = "Enable STACKIT Workflows contract in foundation outputs (fallback mode in MVP)."
  type        = bool
  default     = false
}

variable "langfuse_enabled" {
  description = "Enable Langfuse contract in foundation outputs (fallback mode in MVP)."
  type        = bool
  default     = false
}

variable "neo4j_enabled" {
  description = "Enable Neo4j contract in foundation outputs (fallback mode in MVP)."
  type        = bool
  default     = false
}

variable "rabbitmq_enabled" {
  description = "Enable RabbitMQ contract in foundation outputs (fallback mode in MVP)."
  type        = bool
  default     = false
}

variable "public_endpoints_enabled" {
  description = "Enable public endpoints contract in foundation outputs (fallback mode in MVP)."
  type        = bool
  default     = false
}

variable "kms_enabled" {
  description = "Enable KMS contract in foundation outputs (fallback mode in MVP)."
  type        = bool
  default     = false
}

variable "identity_aware_proxy_enabled" {
  description = "Enable IAP contract in foundation outputs (fallback mode in MVP)."
  type        = bool
  default     = false
}
