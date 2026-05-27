variable "secrets_manager_vault_address" {
  description = "STACKIT Secrets Manager Vault-compatible API endpoint URL."
  type        = string
}

variable "secrets_manager_token" {
  description = "STACKIT Secrets Manager authentication token for the Vault provider."
  type        = string
  sensitive   = true
}

variable "observability_credential_username" {
  description = "Observability OTC credential username (from foundation outputs)."
  type        = string
  sensitive   = true
}

variable "observability_credential_password" {
  description = "Observability OTC credential password (from foundation outputs)."
  type        = string
  sensitive   = true
}

variable "observability_metrics_push_url" {
  description = "Observability Prometheus remote-write push URL (from foundation outputs)."
  type        = string
}

variable "observability_logs_push_url" {
  description = "Observability Loki push URL (from foundation outputs)."
  type        = string
}

variable "observability_traces_push_url" {
  description = "Observability OTLP gRPC traces push URL (from foundation outputs)."
  type        = string
}
