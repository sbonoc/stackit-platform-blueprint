locals {
  module_contract = "blueprint-optional-module-observability"
}

provider "vault" {
  address = var.secrets_manager_vault_address
  token   = var.secrets_manager_token
}

resource "vault_kv_secret_v2" "observability_credentials" {
  mount               = "secret"
  name                = "observability/otel-credentials"
  data_json = jsonencode({
    username         = var.observability_credential_username
    password         = var.observability_credential_password
    METRICS_PUSH_URL = var.observability_metrics_push_url
    LOGS_PUSH_URL    = var.observability_logs_push_url
    TRACES_PUSH_URL  = var.observability_traces_push_url
  })
}
