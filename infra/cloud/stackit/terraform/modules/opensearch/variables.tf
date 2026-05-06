variable "stackit_project_id" {
  description = "STACKIT project identifier."
  type        = string
}

variable "opensearch_instance_name" {
  description = "Canonical OpenSearch instance name."
  type        = string
}

variable "opensearch_version" {
  description = "Managed OpenSearch service version."
  type        = string
  default     = "2.17"
}

variable "opensearch_plan_name" {
  description = "Managed OpenSearch plan name."
  type        = string
  default     = "stackit-opensearch-single"
}
